"""Mocked-subprocess tests for the D006 Calendar channel (`src/channels/calendar.py`).

All tests patch ``subprocess.run`` so they pass on any CI host (the
real osascript / Calendar.app integration is gated on Joe's Mac per
D011). Coverage targets:

- success path: a returncode-0 osascript with a UID in stdout becomes
  a ``CalendarEventId``.
- FAMILY_LOCKOUT graceful no-op: ``publish`` returns ``None`` without
  spawning a subprocess (Rule 34 + D010 + D011).
- non-mac path: ``shutil.which("osascript")`` -> None raises
  ``HannaCalendarNotAvailable`` (D011).
- permission denied: AppleScript error -1743 in stderr surfaces as
  ``HannaCalendarPermissionRequired`` (R2 mitigation).
- D012 idempotency: a second publish with the same brief_id returns
  the existing UID without re-creating the event.
- archive R5: missing ``Hanna · Archive`` calendar raises
  ``HannaCalendarNotFound`` without attempting the move.
"""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from src.channels import calendar as calendar_channel
from src.channels.calendar import (
    HannaCalendarNotAvailable,
    HannaCalendarNotFound,
    HannaCalendarPermissionRequired,
    HannaCalendarPublishFailed,
    archive,
    publish,
)
from src.schemas import BriefPayload, CalendarEventId, ProducerPhase


def _brief(
    phase: ProducerPhase = ProducerPhase.MORNING,
    brief_id: str = "abc123def4567890",
    anchor_iso: str = "2026-05-26T09:00:00-04:00",
    body: str = "# Hanna brief — morning\n\nbody",
) -> BriefPayload:
    return BriefPayload(
        phase=phase,
        composed_at_iso="2026-05-26T07:42:11+00:00",
        body_markdown=body,
        referenced_products=["harlo"],
        phase_anchor_iso=anchor_iso,
        brief_id=brief_id,
    )


def _completed(returncode: int, stdout: str = "", stderr: str = ""):
    """Build a subprocess.CompletedProcess stand-in for mocking."""
    return subprocess.CompletedProcess(
        args=["osascript", "-e", "..."],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


class TestPublish:
    def test_publish_returns_event_id_on_success(self):
        # The lookup step returns "" (no existing event); the create step
        # returns the new UID on stdout.
        run_mock = MagicMock(
            side_effect=[
                _completed(returncode=0, stdout=""),  # lookup
                _completed(returncode=0, stdout="EventUID123"),  # create
            ]
        )
        with patch("src.channels.calendar.subprocess.run", run_mock), patch(
            "src.channels.calendar.shutil.which", return_value="/usr/bin/osascript"
        ):
            result = publish(_brief())
        assert result == "EventUID123"
        assert isinstance(result, str)  # NewType collapses to str at runtime
        assert run_mock.call_count == 2

    def test_publish_returns_none_on_family_lockout(self):
        # Rule 34 + D010 + D011: lockout brief is a graceful no-op; no
        # subprocess is ever spawned.
        run_mock = MagicMock()
        with patch("src.channels.calendar.subprocess.run", run_mock):
            result = publish(
                _brief(phase=ProducerPhase.FAMILY_LOCKOUT, anchor_iso="", brief_id="")
            )
        assert result is None
        run_mock.assert_not_called()

    def test_publish_returns_none_when_anchor_empty(self):
        # Belt-and-braces: even a non-lockout phase with an empty anchor
        # short-circuits to None (defends the D010 invariant if a future
        # composer ever produces an anchor-less non-lockout brief).
        run_mock = MagicMock()
        with patch("src.channels.calendar.subprocess.run", run_mock):
            result = publish(
                _brief(phase=ProducerPhase.MORNING, anchor_iso="", brief_id="")
            )
        assert result is None
        run_mock.assert_not_called()

    def test_publish_raises_unavailable_on_no_osascript(self):
        # D011 non-mac path: shutil.which returns None; the exception is
        # raised before any subprocess call.
        run_mock = MagicMock()
        with patch("src.channels.calendar.shutil.which", return_value=None), patch(
            "src.channels.calendar.subprocess.run", run_mock
        ):
            with pytest.raises(HannaCalendarNotAvailable):
                publish(_brief())
        run_mock.assert_not_called()

    def test_publish_raises_unavailable_on_file_not_found(self):
        # Defence-in-depth: shutil.which says yes but subprocess.run blows
        # up with FileNotFoundError (e.g. /usr/bin/osascript got removed
        # mid-flight). The exception still surfaces as unavailable.
        run_mock = MagicMock(side_effect=FileNotFoundError("osascript missing"))
        with patch(
            "src.channels.calendar.shutil.which", return_value="/usr/bin/osascript"
        ), patch("src.channels.calendar.subprocess.run", run_mock):
            with pytest.raises(HannaCalendarNotAvailable):
                publish(_brief())

    def test_publish_raises_permission_required_on_neg_1743(self):
        # R2 mitigation: AppleScript error -1743 in stderr (Calendar
        # Automation not granted) surfaces as the dedicated exception class
        # so the bin/README.md grant path is referenced in the message.
        run_mock = MagicMock(
            return_value=_completed(
                returncode=1,
                stdout="",
                stderr="execution error: Not authorized... (-1743)",
            )
        )
        with patch("src.channels.calendar.subprocess.run", run_mock), patch(
            "src.channels.calendar.shutil.which", return_value="/usr/bin/osascript"
        ):
            with pytest.raises(HannaCalendarPermissionRequired) as excinfo:
                publish(_brief())
        # The exception message names the System Settings grant path so
        # the operator has remediation context inline.
        assert "Automation" in str(excinfo.value)

    def test_publish_raises_publish_failed_on_generic_error(self):
        # Anything other than the permission code surfaces as the generic
        # publish-failed class with the stderr excerpt in the message.
        run_mock = MagicMock(
            side_effect=[
                _completed(returncode=0, stdout=""),  # lookup ok
                _completed(
                    returncode=2,
                    stdout="",
                    stderr="some other AppleScript error: boom",
                ),  # create blows up
            ]
        )
        with patch("src.channels.calendar.subprocess.run", run_mock), patch(
            "src.channels.calendar.shutil.which", return_value="/usr/bin/osascript"
        ):
            with pytest.raises(HannaCalendarPublishFailed) as excinfo:
                publish(_brief())
        assert "boom" in str(excinfo.value)

    def test_publish_idempotent_on_duplicate_brief_id(self):
        # D012: a second publish() call with the same brief_id returns the
        # existing UID without re-creating the event. The lookup step now
        # returns the UID; the create step must NOT be invoked.
        run_mock = MagicMock(
            side_effect=[
                _completed(returncode=0, stdout="EXISTING_UID"),  # lookup hit
            ]
        )
        with patch("src.channels.calendar.subprocess.run", run_mock), patch(
            "src.channels.calendar.shutil.which", return_value="/usr/bin/osascript"
        ):
            result = publish(_brief())
        assert result == "EXISTING_UID"
        # Critical: only the lookup ran; no create call followed.
        assert run_mock.call_count == 1


class TestArchive:
    def test_archive_raises_not_found_when_archive_calendar_missing(self):
        # R5 mitigation: the existence check returns "no" -> raise
        # HannaCalendarNotFound cleanly; the move step is never attempted.
        run_mock = MagicMock(
            side_effect=[
                _completed(returncode=0, stdout="no"),  # existence check
            ]
        )
        with patch("src.channels.calendar.subprocess.run", run_mock), patch(
            "src.channels.calendar.shutil.which", return_value="/usr/bin/osascript"
        ):
            with pytest.raises(HannaCalendarNotFound) as excinfo:
                archive(CalendarEventId("UID-to-archive"))
        # Hanna does not auto-create — the message names the manual remediation.
        assert "Hanna · Archive" in str(excinfo.value)
        assert run_mock.call_count == 1  # move was NOT attempted

    def test_archive_raises_unavailable_on_no_osascript(self):
        run_mock = MagicMock()
        with patch("src.channels.calendar.shutil.which", return_value=None), patch(
            "src.channels.calendar.subprocess.run", run_mock
        ):
            with pytest.raises(HannaCalendarNotAvailable):
                archive(CalendarEventId("UID-1"))
        run_mock.assert_not_called()

    def test_archive_success_when_archive_calendar_present(self):
        # Happy path: existence check returns "yes"; the move step returns
        # success. archive() returns None on success per the contract.
        run_mock = MagicMock(
            side_effect=[
                _completed(returncode=0, stdout="yes"),  # exists
                _completed(returncode=0, stdout=""),  # move ok
            ]
        )
        with patch("src.channels.calendar.subprocess.run", run_mock), patch(
            "src.channels.calendar.shutil.which", return_value="/usr/bin/osascript"
        ):
            result = archive(CalendarEventId("UID-1"))
        assert result is None
        assert run_mock.call_count == 2


class TestApplescriptDateFormatting:
    def test_format_date_renders_locale_friendly_string(self):
        # The AppleScript date constructor needs a locale-formatted string.
        # We compose deterministically via strftime so the format is stable
        # across hosts; this guards the wire-format from drift.
        rendered = calendar_channel._format_applescript_date(
            "2026-05-26T09:00:00-04:00"
        )
        # Spec: "Weekday, Month D, YYYY at H:MM:SS AM/PM"
        assert "Tuesday" in rendered
        assert "May" in rendered
        assert "26" in rendered
        assert "2026" in rendered
        assert "9:00:00 AM" in rendered

    def test_format_date_renders_pm_correctly(self):
        rendered = calendar_channel._format_applescript_date(
            "2026-05-26T17:00:00-04:00"
        )
        assert "5:00:00 PM" in rendered


class TestApplescriptStringEscaping:
    def test_escapes_backslash_and_double_quote(self):
        # Defence in depth: even though brief bodies travel via tempfile,
        # short metadata strings (calendar names, brief_ids) flow through
        # the AppleScript template directly. Escape them safely.
        out = calendar_channel._applescript_string('Hanna "edge" \\ case')
        assert out == 'Hanna \\"edge\\" \\\\ case'
