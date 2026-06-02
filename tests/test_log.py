"""Tests for src/_log.py + python -m src status + _read_harlo() stderr surfacing.

Closes the c011 "zero logging" leg: structured logging now exists, the status
probe exists, and the lane-boundary error paths surface bridge.last_stderr().
"""

from __future__ import annotations

import importlib.util
import json
import logging
import re
import subprocess
import sys
from pathlib import Path

import pytest

from src._log import get_logger
from src.harlo_bridge import HarloUnreachable

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "first_hanna_brief.py"

_spec = importlib.util.spec_from_file_location("first_hanna_brief_logtest", _SCRIPT_PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)


class TestGetLogger:
    """src/_log.py exposes a single configured logger entry point."""

    def test_get_logger_returns_logger_with_expected_format(self):
        # First call configures the root logger; subsequent calls are no-ops on config.
        logger = get_logger("hanna.test.getlogger")
        assert isinstance(logger, logging.Logger)
        # Inspect a root handler's formatter directly — pytest's caplog hijacks
        # stderr capture, so we verify the formatter spec rather than the stream.
        root = logging.getLogger()
        assert root.handlers, "root logger has no handlers after get_logger()"
        formatter = root.handlers[0].formatter
        assert formatter is not None
        # Format: "%(asctime)s.%(msecs)03dZ %(levelname)s %(name)s: %(message)s"
        # → "YYYY-MM-DDTHH:MM:SS.mmmZ LEVEL name: msg"
        record = logging.LogRecord(
            name="hanna.test.getlogger",
            level=logging.WARNING,
            pathname=__file__,
            lineno=1,
            msg="probe-message-xyz",
            args=(),
            exc_info=None,
        )
        rendered = formatter.format(record)
        pattern = re.compile(
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z "
            r"WARNING hanna\.test\.getlogger: probe-message-xyz$"
        )
        assert pattern.match(rendered), f"format mismatch; rendered={rendered!r}"


class TestStatusSubprocess:
    """`python3 -m src status` returns valid JSON on stdout with the contract keys."""

    def test_status_subprocess_returns_valid_json_with_expected_keys(self):
        # Run the status probe in a subprocess so we exercise the real
        # __main__ entrypoint (not a function call). harlo binary is absent
        # in this environment → harlo_reachable=false is the expected path.
        result = subprocess.run(
            [sys.executable, "-m", "src", "status"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0, (
            f"non-zero exit\nstdout={result.stdout!r}\nstderr={result.stderr!r}"
        )
        # JSON on stdout; logs on stderr.
        payload = json.loads(result.stdout.strip())
        for key in (
            "hanna",
            "harlo_reachable",
            "harlo_burnout",
            "ts",
            "phase",
            "next_phase_boundary_eta_minutes",
        ):
            assert key in payload, f"missing key {key!r} in {payload!r}"
        assert payload["hanna"] == "ok"
        assert isinstance(payload["harlo_reachable"], bool)
        # harlo binary absent in CI → unreachable is the operational path.
        assert payload["harlo_reachable"] is False
        assert payload["harlo_burnout"] is None


class TestReadHarloLogsStderrTail:
    """When _read_harlo()'s HarloBridge raises, the WARNING log surfaces the
    bridge's last_stderr() — closing the c011 "diagnostic data no production
    caller reads" gap."""

    def test_read_harlo_logs_warning_with_stderr_tail_on_unreachable(self, caplog):
        # Stub a bridge whose drive_coaching_exchange raises HarloUnreachable
        # and whose last_stderr() returns a sentinel line we can assert on.
        sentinel = "harlo-stderr-sentinel-line-12345"

        class _StubBridge:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return None

            def drive_coaching_exchange(self):
                raise HarloUnreachable("stubbed: spawn failed")

            def last_stderr(self):
                return [sentinel]

        # Patch the module-local symbol so _read_harlo picks up the stub.
        original = _module.HarloBridge
        _module.HarloBridge = _StubBridge
        try:
            with caplog.at_level(logging.WARNING, logger="hanna.brief"):
                reachable, payload = _module._read_harlo()
            assert reachable is False
            assert payload is None
            # The WARNING-level records on hanna.brief must include:
            #   1) the unreachable reason
            #   2) the stderr tail line surfaced from bridge.last_stderr()
            warnings = [
                rec for rec in caplog.records
                if rec.name == "hanna.brief" and rec.levelno >= logging.WARNING
            ]
            messages = [rec.getMessage() for rec in warnings]
            assert any("reason=unreachable" in m for m in messages), messages
            assert any(sentinel in m for m in messages), messages
        finally:
            _module.HarloBridge = original
