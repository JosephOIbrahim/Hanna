"""D006 Calendar channel — publishes a BriefPayload to a dedicated iCloud
calendar named ``Hanna`` via ``osascript`` on macOS.

Contract (per D006 / D010 / D011 / D012):

- ``publish(brief)`` authors a **0-minute anchor event** at
  ``brief.phase_anchor_iso`` (D010 rhythm-anchor, NOT the compose moment) on
  the dedicated ``Hanna`` calendar (D006), with the brief markdown body in the
  event notes. The brief's ``brief_id`` is stored in the event URL field as
  the dedup key (D012); a second ``publish()`` call with the same brief_id
  returns the existing ``CalendarEventId`` without re-creating the event.
- ``publish(brief)`` is a **graceful no-op** (returns ``None``) for
  ``FAMILY_LOCKOUT`` briefs or briefs with an empty ``phase_anchor_iso``
  (D010 / D011 — never publish during the family-first window).
- On non-macOS hosts ``osascript`` is absent; ``publish()`` raises
  ``HannaCalendarNotAvailable`` (D011 — the channel is macOS-only at v1).
- The ``Hanna · Archive`` calendar is **not auto-created**; if missing,
  ``archive()`` raises ``HannaCalendarNotFound``.

Mitigations folded in from FORUM.md DELIBERATE cycle 1 critique on Line A:

- **R1** (AppleScript template fragility): the brief body is written to a
  ``tempfile.NamedTemporaryFile`` and read by AppleScript via
  ``do shell script "cat " & quoted form of bodyPath`` — no inline body-string
  escaping.
- **R2** (Calendar.app permission prompt under launchd): an osascript error
  code ``-1743`` (errAEEventNotPermitted) is detected in stderr and surfaced
  as ``HannaCalendarPermissionRequired`` with the System Settings grant path
  in the message.
- **R3** (multiple calendars named ``Hanna``): the AppleScript looks up by
  ``calendar_name`` argument (default ``"Hanna"``); the per-brief D012 lookup
  by ``brief_id`` short-circuits before any "create" branch runs.
- **R5** (archive calendar missing): ``archive()`` queries for the named
  archive calendar first and raises ``HannaCalendarNotFound`` cleanly when
  the calendar is absent.

Stdlib only. No third-party dependencies.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

from src._log import get_logger
from src.schemas import BriefPayload, CalendarEventId, ProducerPhase

logger = get_logger("hanna.calendar")

# Default macOS osascript timeout. Calendar.app round-trips are sub-second
# in normal operation; 10s leaves wide headroom for first-launch indexing
# without freezing the brief composer indefinitely.
_OSASCRIPT_TIMEOUT_S = 10.0

# AppleScript / Cocoa error code surfaced when Calendar access has not been
# granted to the invoking process. Detected via substring match in stderr.
_APPLESCRIPT_PERMISSION_DENIED_CODE = "-1743"


class HannaCalendarError(RuntimeError):
    """Base class for Hanna Calendar channel failures (D006)."""


class HannaCalendarNotAvailable(HannaCalendarError):
    """The Calendar channel is unreachable on this host (D011).

    Raised when ``osascript`` is not present (non-macOS) or
    ``subprocess.run`` raises ``FileNotFoundError``. Calling code is expected
    to handle this as a well-defined no-op: persist the brief, record the
    unpublished reason, exit cleanly.
    """


class HannaCalendarNotFound(HannaCalendarError):
    """The named calendar does not exist in Calendar.app (D006).

    Hanna does not auto-create calendars — Joe creates the ``Hanna`` and
    ``Hanna · Archive`` iCloud calendars manually so the channel respects
    his calendar set. This exception surfaces the missing-calendar state
    cleanly rather than silently failing or authoring a stray calendar.
    """


class HannaCalendarPermissionRequired(HannaCalendarError):
    """Calendar.app has not granted Automation access to this process (R2).

    Detected via AppleScript error code -1743 in osascript stderr. The
    message includes the System Settings path Joe walks to grant access.
    """


class HannaCalendarPublishFailed(HannaCalendarError):
    """Generic publish failure with a stderr excerpt for diagnostics."""


def _format_applescript_date(anchor_iso: str) -> str:
    """Return the AppleScript ``date`` literal for an ISO-8601 anchor string.

    AppleScript's ``date`` constructor accepts a locale-formatted string such
    as ``"Monday, May 26, 2026 at 9:00:00 AM"``. We compose it from the
    parsed datetime using ``strftime`` so the format is deterministic.
    """
    dt = datetime.fromisoformat(anchor_iso)
    # %A = full weekday name; %B = full month name; platform-portable.
    # Hour without leading zero is rendered via the AppleScript hour arithmetic
    # we accept — %-I is non-portable, so we strip the leading zero by hand.
    weekday = dt.strftime("%A")
    month = dt.strftime("%B")
    day = dt.day
    year = dt.year
    hour_12 = dt.hour % 12 or 12
    minute = dt.minute
    second = dt.second
    am_pm = "AM" if dt.hour < 12 else "PM"
    return (
        f"{weekday}, {month} {day}, {year} at "
        f"{hour_12}:{minute:02d}:{second:02d} {am_pm}"
    )


def _applescript_string(value: str) -> str:
    """Escape a Python string for safe embedding inside an AppleScript literal.

    AppleScript string literals delimit with double quotes; backslashes and
    double quotes inside the literal must be escaped. The body markdown does
    NOT travel through this helper (R1 mitigation: bodies go via tempfile);
    short metadata strings (titles, calendar names, brief_ids) do.
    """
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _build_lookup_script(calendar_name: str, brief_id: str) -> str:
    """AppleScript: return the UID of the first event in *calendar_name* whose
    URL field equals *brief_id*. Returns the empty string if no match.
    """
    cal = _applescript_string(calendar_name)
    bid = _applescript_string(brief_id)
    return (
        'tell application "Calendar"\n'
        f'    set theCal to first calendar whose name is "{cal}"\n'
        f'    set theEvents to (every event of theCal whose url is "{bid}")\n'
        '    if (count of theEvents) is 0 then\n'
        '        return ""\n'
        '    else\n'
        '        return uid of (item 1 of theEvents)\n'
        '    end if\n'
        'end tell'
    )


def _build_publish_script(
    calendar_name: str,
    title: str,
    body_path: str,
    anchor_applescript_date: str,
    brief_id: str,
) -> str:
    """AppleScript: create a 0-minute event on *calendar_name* and return the
    new event's UID. Body text is read from *body_path* via the shell so the
    AppleScript template never inlines the brief body (R1 mitigation).
    """
    cal = _applescript_string(calendar_name)
    title_esc = _applescript_string(title)
    body_path_esc = _applescript_string(body_path)
    bid = _applescript_string(brief_id)
    return (
        f'set bodyPath to "{body_path_esc}"\n'
        'set bodyText to do shell script "cat " & quoted form of bodyPath\n'
        f'set startDate to date "{anchor_applescript_date}"\n'
        'tell application "Calendar"\n'
        f'    set theCal to first calendar whose name is "{cal}"\n'
        '    set newEvent to make new event at end of events of theCal with properties '
        f'{{summary:"{title_esc}", start date:startDate, end date:startDate, '
        f'description:bodyText, url:"{bid}"}}\n'
        '    return uid of newEvent\n'
        'end tell'
    )


def _build_archive_script(
    source_calendar: str, archive_calendar: str, event_uid: str
) -> str:
    """AppleScript: move the event with the given UID from *source_calendar*
    to *archive_calendar*. Raises (via AppleScript) if archive_calendar is
    absent; the Python caller detects the missing-calendar state up front.
    """
    src = _applescript_string(source_calendar)
    arc = _applescript_string(archive_calendar)
    uid = _applescript_string(event_uid)
    return (
        'tell application "Calendar"\n'
        f'    set theSource to first calendar whose name is "{src}"\n'
        f'    set theArchive to first calendar whose name is "{arc}"\n'
        f'    set theEvent to first event of theSource whose uid is "{uid}"\n'
        '    move theEvent to theArchive\n'
        'end tell'
    )


def _build_archive_calendar_exists_script(archive_calendar: str) -> str:
    """AppleScript: return ``"yes"`` if a calendar named *archive_calendar*
    exists, else ``"no"``. Lets us surface ``HannaCalendarNotFound`` cleanly
    without parsing AppleScript exception text (R5 mitigation).
    """
    arc = _applescript_string(archive_calendar)
    return (
        'tell application "Calendar"\n'
        f'    set matching to (every calendar whose name is "{arc}")\n'
        '    if (count of matching) is 0 then\n'
        '        return "no"\n'
        '    else\n'
        '        return "yes"\n'
        '    end if\n'
        'end tell'
    )


def _run_osascript(script: str) -> subprocess.CompletedProcess:
    """Invoke ``osascript -e SCRIPT`` and return the completed process.

    Raises ``HannaCalendarNotAvailable`` if the binary cannot be launched
    (FileNotFoundError → D011 non-macOS path).
    """
    try:
        return subprocess.run(
            ["osascript", "-e", script],
            check=False,
            capture_output=True,
            text=True,
            timeout=_OSASCRIPT_TIMEOUT_S,
        )
    except FileNotFoundError as exc:
        raise HannaCalendarNotAvailable(
            "osascript not present — Calendar channel is macOS-only at v1 per D011"
        ) from exc


def _interpret_failure(
    completed: subprocess.CompletedProcess, context: str
) -> HannaCalendarError:
    """Map a non-zero osascript completion into the right exception class."""
    stderr = (completed.stderr or "").strip()
    if _APPLESCRIPT_PERMISSION_DENIED_CODE in stderr:
        return HannaCalendarPermissionRequired(
            "Calendar.app has not granted Automation access to this process "
            "(AppleScript error -1743). Grant access via System Settings → "
            "Privacy & Security → Automation → enable Calendar for Terminal "
            "(or the Python binary used to invoke Hanna), then retry. "
            f"Context: {context}; stderr: {stderr[:240]}"
        )
    excerpt = stderr[:240] if stderr else "(no stderr)"
    return HannaCalendarPublishFailed(
        f"osascript exited with returncode={completed.returncode} during "
        f"{context}: {excerpt}"
    )


def _lookup_existing(
    calendar_name: str, brief_id: str
) -> CalendarEventId | None:
    """Return the existing CalendarEventId for *brief_id* on *calendar_name*,
    or None if no event matches (D012 idempotency precondition).
    """
    script = _build_lookup_script(calendar_name, brief_id)
    completed = _run_osascript(script)
    if completed.returncode != 0:
        raise _interpret_failure(completed, "lookup")
    uid = (completed.stdout or "").strip()
    if not uid:
        return None
    logger.debug("calendar idempotency hit brief_id=%s uid=%s", brief_id, uid)
    return CalendarEventId(uid)


def publish(
    brief: BriefPayload, calendar_name: str = "Hanna"
) -> CalendarEventId | None:
    """Publish *brief* as a 0-minute anchor event on *calendar_name*.

    Returns the new (or pre-existing, per D012) ``CalendarEventId``. Returns
    ``None`` as a graceful no-op when ``brief.phase`` is ``FAMILY_LOCKOUT``
    or ``brief.phase_anchor_iso`` is empty (Rule 34 / D010 / D011 — never
    publish outside the producer-rhythm window).

    Raises:
        HannaCalendarNotAvailable: ``osascript`` is not present (non-macOS).
        HannaCalendarPermissionRequired: Calendar Automation grant missing
            (AppleScript error -1743).
        HannaCalendarPublishFailed: any other osascript failure; the message
            includes a stderr excerpt for diagnostics.
    """
    # D010 / D011 / Rule 34: no publish during FAMILY_LOCKOUT or any phase
    # whose anchor is undefined. The graceful no-op is the contract; calling
    # code records ``unpublished_reason="family_lockout"`` separately.
    if brief.phase == ProducerPhase.FAMILY_LOCKOUT or brief.phase_anchor_iso == "":
        logger.info(
            "calendar publish skipped reason=lockout-or-empty-anchor phase=%s",
            brief.phase.name.lower(),
        )
        return None

    # D011: detect macOS osascript availability up front so non-mac callers
    # get the documented exception without spawning a subprocess.
    if shutil.which("osascript") is None:
        raise HannaCalendarNotAvailable(
            "osascript not present — Calendar channel is macOS-only at v1 per D011"
        )

    logger.info(
        "calendar publish start phase=%s brief_id=%s calendar=%s",
        brief.phase.name.lower(),
        brief.brief_id or "(none)",
        calendar_name,
    )

    # D012 idempotency: look up by brief_id first; return the existing UID
    # without authoring a duplicate event.
    if brief.brief_id:
        existing = _lookup_existing(calendar_name, brief.brief_id)
        if existing is not None:
            logger.info(
                "calendar publish idempotent-hit brief_id=%s uid=%s",
                brief.brief_id,
                existing,
            )
            return existing

    title = f"Hanna · {brief.phase.name.lower().replace('_', ' ')}"
    anchor_applescript_date = _format_applescript_date(brief.phase_anchor_iso)

    # R1 mitigation: write the body to a temp file; AppleScript reads it via
    # ``do shell script "cat " & quoted form of bodyPath``. The body is never
    # inlined into the AppleScript template, so quotes/newlines/backticks in
    # the brief body never escape into the script.
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".md",
        prefix="hanna-brief-",
        delete=False,
    ) as body_file:
        body_file.write(brief.body_markdown)
        body_path = body_file.name

    script = _build_publish_script(
        calendar_name=calendar_name,
        title=title,
        body_path=body_path,
        anchor_applescript_date=anchor_applescript_date,
        brief_id=brief.brief_id,
    )
    completed = _run_osascript(script)
    if completed.returncode != 0:
        logger.warning(
            "calendar publish failed brief_id=%s rc=%s stderr=%s",
            brief.brief_id,
            completed.returncode,
            (completed.stderr or "").strip()[:240],
        )
        raise _interpret_failure(completed, "publish")

    uid = (completed.stdout or "").strip()
    if not uid:
        raise HannaCalendarPublishFailed(
            "osascript publish returned an empty UID; cannot reconcile "
            "the published event without a handle"
        )
    logger.info(
        "calendar publish ok brief_id=%s uid=%s", brief.brief_id, uid
    )
    return CalendarEventId(uid)


def archive(
    event_id: CalendarEventId,
    archive_calendar_name: str = "Hanna · Archive",
    source_calendar_name: str = "Hanna",
) -> None:
    """Move the event identified by *event_id* from *source_calendar_name*
    to *archive_calendar_name*.

    Raises:
        HannaCalendarNotAvailable: ``osascript`` is not present (non-macOS).
        HannaCalendarNotFound: the *archive_calendar_name* calendar does
            not exist; Hanna does not auto-create it (D006 / R5 mitigation).
        HannaCalendarPermissionRequired: Calendar Automation grant missing.
        HannaCalendarPublishFailed: any other osascript failure.
    """
    if shutil.which("osascript") is None:
        raise HannaCalendarNotAvailable(
            "osascript not present — Calendar channel is macOS-only at v1 per D011"
        )

    # R5: verify the archive calendar exists before issuing the move.
    exists_script = _build_archive_calendar_exists_script(archive_calendar_name)
    exists_completed = _run_osascript(exists_script)
    if exists_completed.returncode != 0:
        raise _interpret_failure(exists_completed, "archive-calendar-lookup")
    if (exists_completed.stdout or "").strip() != "yes":
        raise HannaCalendarNotFound(
            f"Archive calendar {archive_calendar_name!r} does not exist. "
            "Hanna does not auto-create calendars (D006); create it manually "
            "in Calendar.app and retry."
        )

    move_script = _build_archive_script(
        source_calendar=source_calendar_name,
        archive_calendar=archive_calendar_name,
        event_uid=event_id,
    )
    move_completed = _run_osascript(move_script)
    if move_completed.returncode != 0:
        raise _interpret_failure(move_completed, "archive-move")
    logger.info(
        "calendar archive ok uid=%s source=%s archive=%s",
        event_id,
        source_calendar_name,
        archive_calendar_name,
    )


# ----------------------------------------------------------------------------
# `python3 -m src.channels.calendar publish-now` entrypoint (ROADMAP §4 L4b).
# Composes one brief end-to-end via scripts/first_hanna_brief.py's helpers,
# publishes it, prints the resulting CalendarEventId or the no-op JSON,
# exits 0 on the lockout / non-mac no-op paths as well.
# ----------------------------------------------------------------------------


def _publish_now_main() -> int:
    """Compose one brief via scripts/first_hanna_brief.py helpers and publish.

    Re-uses the composer so the L4b launcher swap target lands without
    duplicating composition logic. Prints either the new event UID or a
    structured no-op JSON describing why publication was skipped.
    """
    import importlib.util
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent.parent
    composer_path = repo_root / "scripts" / "first_hanna_brief.py"
    spec = importlib.util.spec_from_file_location(
        "first_hanna_brief", composer_path
    )
    if spec is None or spec.loader is None:
        print("error: cannot load scripts/first_hanna_brief.py", file=sys.stderr)
        return 2
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    phase = module._phase_now()
    if phase == ProducerPhase.FAMILY_LOCKOUT:
        print(json.dumps({"published": False, "reason": "family_lockout"}))
        return 0

    harlo_reachable, harlo_payload = module._read_harlo()
    brief = module._compose_brief(phase, harlo_reachable, harlo_payload)
    module._persist(brief, harlo_reachable)

    try:
        event_id = publish(brief)
    except HannaCalendarNotAvailable:
        print(json.dumps({"published": False, "reason": "non_macos"}))
        return 0
    except HannaCalendarError as exc:
        print(
            json.dumps(
                {
                    "published": False,
                    "reason": "publish_failed",
                    "detail": type(exc).__name__,
                }
            )
        )
        return 0
    if event_id is None:
        print(json.dumps({"published": False, "reason": "no_anchor"}))
        return 0
    print(json.dumps({"published": True, "event_id": str(event_id)}))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print(
            "usage: python3 -m src.channels.calendar publish-now",
            file=sys.stderr,
        )
        return 2
    command = args[0]
    if command == "publish-now":
        return _publish_now_main()
    print(f"error: unknown command {command!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
