"""Reconciliation-invariant tests (P6): every persisted ``briefs`` row carries
either a ``calendar_event_uid`` (successful publish) OR an
``unpublished_reason`` (lockout / non-mac / publish failure).

Exercises ``scripts/first_hanna_brief.py``'s reconciliation column flow:

- Successful publish path → ``calendar_event_uid`` set, ``unpublished_reason`` NULL.
- FAMILY_LOCKOUT brief (persisted via helper, since main() exits before
  ``_persist`` on lockout) → ``unpublished_reason = "family_lockout"``.
- ``HannaCalendarNotAvailable`` on non-mac → ``unpublished_reason = "non_macos"``.
- Property invariant: across every persisted row, exactly one of the two
  reconciliation columns is set.
"""

from __future__ import annotations

import importlib.util
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.channels.calendar import HannaCalendarNotAvailable
from src.schemas import BriefPayload, ProducerPhase

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "first_hanna_brief.py"

_spec = importlib.util.spec_from_file_location("first_hanna_brief", _SCRIPT_PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)


def _morning_brief(brief_id: str = "morning_test_id") -> BriefPayload:
    return BriefPayload(
        phase=ProducerPhase.MORNING,
        composed_at_iso="2026-05-26T09:00:00-04:00",
        body_markdown="# Hanna brief — morning\n\nbody",
        referenced_products=["harlo"],
        phase_anchor_iso="2026-05-26T09:00:00-04:00",
        brief_id=brief_id,
    )


def _lockout_brief() -> BriefPayload:
    # FAMILY_LOCKOUT briefs carry empty anchor + brief_id per BriefPayload.compute_*.
    return BriefPayload(
        phase=ProducerPhase.FAMILY_LOCKOUT,
        composed_at_iso="2026-05-30T15:00:00+00:00",
        body_markdown="# Hanna paused",
        referenced_products=[],
        phase_anchor_iso="",
        brief_id="",
    )


class TestReconciliationColumns:
    def test_persist_creates_columns_via_schema(self, tmp_path):
        # Smoke check: after _persist, the briefs table has both new columns.
        db_path = tmp_path / "hanna.sqlite"
        _module._persist(_morning_brief(), harlo_reachable=True, db_path=db_path)
        with sqlite3.connect(db_path) as conn:
            cols = {
                row[1] for row in conn.execute("PRAGMA table_info(briefs)").fetchall()
            }
        assert "calendar_event_uid" in cols
        assert "unpublished_reason" in cols

    def test_migration_idempotent_on_legacy_schema(self, tmp_path):
        # If an older DB exists with the pre-L4b schema, the migration must
        # add the columns without losing existing rows. Build a legacy DB
        # by hand and then call _persist; assert the columns appear and the
        # legacy row survives.
        db_path = tmp_path / "legacy.sqlite"
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "CREATE TABLE briefs ("
                "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "  ts TEXT NOT NULL,"
                "  phase TEXT NOT NULL,"
                "  body TEXT NOT NULL,"
                "  harlo_reachable INTEGER NOT NULL,"
                "  brief_id TEXT UNIQUE,"
                "  phase_anchor_iso TEXT NOT NULL DEFAULT ''"
                ")"
            )
            conn.execute(
                "INSERT INTO briefs (ts, phase, body, harlo_reachable, brief_id, "
                "phase_anchor_iso) VALUES (?, ?, ?, ?, ?, ?)",
                ("2026-05-22T09:00:00-04:00", "morning", "legacy", 1,
                 "legacy_id", "2026-05-22T09:00:00-04:00"),
            )
            conn.commit()
        # Re-running _persist should migrate the legacy schema.
        _module._persist(_morning_brief(), harlo_reachable=True, db_path=db_path)
        with sqlite3.connect(db_path) as conn:
            cols = {
                row[1] for row in conn.execute("PRAGMA table_info(briefs)").fetchall()
            }
            (legacy_count,) = conn.execute(
                "SELECT COUNT(*) FROM briefs WHERE brief_id = 'legacy_id'"
            ).fetchone()
        assert "calendar_event_uid" in cols
        assert "unpublished_reason" in cols
        assert legacy_count == 1  # legacy row preserved

    def test_successful_publish_records_uid_and_clears_reason(
        self, monkeypatch, tmp_path
    ):
        # End-to-end: main() persists the brief, publish() returns a UID,
        # and the reconciliation columns reflect the successful publish.
        db_path = tmp_path / "hanna.sqlite"
        monkeypatch.setattr(_module, "DB_PATH", db_path)
        monkeypatch.setattr(_module, "_phase_now", lambda: ProducerPhase.MORNING)

        # Stub the bridge so main()'s _read_harlo returns state-blind cleanly.
        class _StubBridge:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return None

            def drive_coaching_exchange(self):
                from src.harlo_bridge import HarloUnreachable

                raise HarloUnreachable("stubbed")

        monkeypatch.setattr(_module, "HarloBridge", _StubBridge)

        fake_publish = MagicMock(return_value="CAL_UID_OK")
        monkeypatch.setattr(_module, "calendar_publish", fake_publish)

        exit_code = _module.main()
        assert exit_code == 0
        fake_publish.assert_called_once()

        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(
                "SELECT calendar_event_uid, unpublished_reason FROM briefs"
            ).fetchall()
        assert len(rows) == 1
        cal_uid, reason = rows[0]
        assert cal_uid == "CAL_UID_OK"
        assert reason is None

    def test_family_lockout_brief_records_lockout_reason(self, tmp_path):
        # FAMILY_LOCKOUT main() exits before _persist (preserves existing
        # test contract). For helper code paths that DO persist a lockout
        # brief, the reconciliation invariant still holds: the row must
        # carry unpublished_reason = "family_lockout".
        db_path = tmp_path / "hanna.sqlite"
        # Persist a lockout brief directly via the lower-level helpers,
        # since main() short-circuits.
        brief = _lockout_brief()
        # Direct INSERT to bypass main()'s early-return contract while
        # still exercising _persist + the migration step.
        # _persist refuses INSERT OR IGNORE on empty brief_id (NULL UNIQUE),
        # but we need a deterministic row id to update — use the canonical
        # path: _persist for schema/migrations, then a direct INSERT for
        # the lockout sentinel row.
        _module._persist(_morning_brief("anchor_row"), harlo_reachable=True, db_path=db_path)
        with sqlite3.connect(db_path) as conn:
            _module._apply_pragmas(conn)
            _module._apply_reconciliation_migrations(conn)
            conn.execute(
                "INSERT INTO briefs (ts, phase, body, harlo_reachable, brief_id, "
                "phase_anchor_iso) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    brief.composed_at_iso,
                    brief.phase.name.lower(),
                    brief.body_markdown,
                    1,
                    None,
                    brief.phase_anchor_iso,
                ),
            )
            conn.commit()
        # The lockout row has brief_id IS NULL; the fallback path of
        # _update_reconciliation targets the most-recent NULL-brief_id row.
        _module._update_reconciliation(
            brief_id="",
            unpublished_reason="family_lockout",
            db_path=db_path,
        )
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(
                "SELECT phase, calendar_event_uid, unpublished_reason "
                "FROM briefs WHERE brief_id IS NULL"
            ).fetchall()
        assert len(rows) == 1
        phase, cal_uid, reason = rows[0]
        assert phase == "family_lockout"
        assert cal_uid is None
        assert reason == "family_lockout"

    def test_non_macos_publish_records_non_macos_reason(
        self, monkeypatch, tmp_path
    ):
        db_path = tmp_path / "hanna.sqlite"
        monkeypatch.setattr(_module, "DB_PATH", db_path)
        monkeypatch.setattr(_module, "_phase_now", lambda: ProducerPhase.MORNING)

        class _StubBridge:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return None

            def drive_coaching_exchange(self):
                from src.harlo_bridge import HarloUnreachable

                raise HarloUnreachable("stubbed")

        monkeypatch.setattr(_module, "HarloBridge", _StubBridge)

        def _raise_unavailable(_brief):
            raise HannaCalendarNotAvailable("osascript missing")

        monkeypatch.setattr(_module, "calendar_publish", _raise_unavailable)

        exit_code = _module.main()
        assert exit_code == 0

        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(
                "SELECT calendar_event_uid, unpublished_reason FROM briefs"
            ).fetchall()
        assert len(rows) == 1
        cal_uid, reason = rows[0]
        assert cal_uid is None
        assert reason == "non_macos"

    def test_publish_failure_records_publish_failed_reason(
        self, monkeypatch, tmp_path
    ):
        from src.channels.calendar import HannaCalendarPublishFailed

        db_path = tmp_path / "hanna.sqlite"
        monkeypatch.setattr(_module, "DB_PATH", db_path)
        monkeypatch.setattr(_module, "_phase_now", lambda: ProducerPhase.MORNING)

        class _StubBridge:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return None

            def drive_coaching_exchange(self):
                from src.harlo_bridge import HarloUnreachable

                raise HarloUnreachable("stubbed")

        monkeypatch.setattr(_module, "HarloBridge", _StubBridge)

        def _raise_publish_failed(_brief):
            raise HannaCalendarPublishFailed("osascript rc=2 stderr=boom")

        monkeypatch.setattr(_module, "calendar_publish", _raise_publish_failed)

        exit_code = _module.main()
        assert exit_code == 0

        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(
                "SELECT calendar_event_uid, unpublished_reason FROM briefs"
            ).fetchall()
        assert len(rows) == 1
        cal_uid, reason = rows[0]
        assert cal_uid is None
        assert reason is not None
        assert reason.startswith("publish_failed:")
        assert "HannaCalendarPublishFailed" in reason


class TestReconciliationInvariant:
    """P6 property: every persisted row has calendar_event_uid XOR
    unpublished_reason. Lockout rows that exit main() before _persist
    don't violate the invariant — they simply don't exist. Any row
    that DOES exist must carry exactly one of the two columns.
    """

    def test_invariant_holds_across_mixed_outcomes(self, monkeypatch, tmp_path):
        # Build a corpus of rows via the three observable post-persist paths
        # and assert the property over every resulting row.
        db_path = tmp_path / "hanna.sqlite"
        monkeypatch.setattr(_module, "DB_PATH", db_path)

        class _StubBridge:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return None

            def drive_coaching_exchange(self):
                from src.harlo_bridge import HarloUnreachable

                raise HarloUnreachable("stubbed")

        monkeypatch.setattr(_module, "HarloBridge", _StubBridge)

        # Row 1: successful publish (MORNING + uid).
        monkeypatch.setattr(_module, "_phase_now", lambda: ProducerPhase.MORNING)
        monkeypatch.setattr(_module, "calendar_publish", MagicMock(return_value="UID_A"))
        assert _module.main() == 0

        # Row 2: non-mac publish (MIDDAY + reason="non_macos").
        monkeypatch.setattr(_module, "_phase_now", lambda: ProducerPhase.MIDDAY)

        def _raise_unavailable(_b):
            raise HannaCalendarNotAvailable("no osascript")

        monkeypatch.setattr(_module, "calendar_publish", _raise_unavailable)
        assert _module.main() == 0

        # Row 3: publish_failed (EVENING + reason="publish_failed: ...").
        from src.channels.calendar import HannaCalendarPublishFailed

        monkeypatch.setattr(_module, "_phase_now", lambda: ProducerPhase.EVENING)

        def _raise_failed(_b):
            raise HannaCalendarPublishFailed("rc=2")

        monkeypatch.setattr(_module, "calendar_publish", _raise_failed)
        assert _module.main() == 0

        # Assert the invariant: every row has calendar_event_uid IS NULL
        # XOR unpublished_reason IS NULL. (Lockout rows are excluded because
        # main() exits before _persist; the test covers post-persist rows.)
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(
                "SELECT calendar_event_uid, unpublished_reason FROM briefs"
            ).fetchall()
        assert len(rows) == 3
        for cal_uid, reason in rows:
            # Exactly one is non-NULL — XOR over presence.
            assert (cal_uid is None) != (reason is None), (
                f"Reconciliation invariant violated: cal_uid={cal_uid!r}, "
                f"reason={reason!r}"
            )

    def test_invariant_query_returns_zero_offending_rows(
        self, monkeypatch, tmp_path
    ):
        # SQL-side restatement of the invariant: COUNT(*) WHERE BOTH-NULL OR
        # BOTH-NON-NULL must be zero across the persisted corpus.
        db_path = tmp_path / "hanna.sqlite"
        monkeypatch.setattr(_module, "DB_PATH", db_path)

        class _StubBridge:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return None

            def drive_coaching_exchange(self):
                from src.harlo_bridge import HarloUnreachable

                raise HarloUnreachable("stubbed")

        monkeypatch.setattr(_module, "HarloBridge", _StubBridge)
        monkeypatch.setattr(_module, "_phase_now", lambda: ProducerPhase.MORNING)
        monkeypatch.setattr(_module, "calendar_publish", MagicMock(return_value="UID_X"))
        assert _module.main() == 0

        with sqlite3.connect(db_path) as conn:
            (offenders,) = conn.execute(
                "SELECT COUNT(*) FROM briefs WHERE "
                "(calendar_event_uid IS NULL AND unpublished_reason IS NULL) "
                "OR (calendar_event_uid IS NOT NULL AND unpublished_reason IS NOT NULL)"
            ).fetchone()
        assert offenders == 0
