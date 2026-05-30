"""Tests for src/harlo_bridge.py covering D005.1, D005.2, and D005.3.

D005.1: per-composition gate via begin_composition / end_composition.
D005.2: _read_frame honors the timeout parameter via selectors.
D005.3: background stderr drainer writes into a 64-deep ring buffer.

Subprocess spawning is mocked throughout — these tests never touch a real
Harlo binary.
"""

from __future__ import annotations

import collections
import io
import json
import os
import threading
import time
from typing import Any
from unittest.mock import patch

import pytest

from src.harlo_bridge import (
    HarloBridge,
    HarloCoachingExchangeAlreadyDriven,
    HarloCoachingExchangeOutsideComposition,
    HarloCompositionAlreadyActive,
    HarloCompositionNotActive,
    HarloProtocolError,
    HarloTimeout,
    HarloUnreachable,
)


# --------------------------------------------------------------------------
# Test doubles
# --------------------------------------------------------------------------


class _MockProc:
    """Minimal subprocess.Popen[bytes] stand-in for non-IO-shape tests."""

    def __init__(
        self,
        stdout: Any = None,
        stderr: Any = None,
        stdin: Any = None,
    ) -> None:
        self.stdout = stdout if stdout is not None else io.BytesIO()
        self.stderr = stderr if stderr is not None else io.BytesIO()
        self.stdin = stdin if stdin is not None else io.BytesIO()
        self._poll_result: int | None = None

    def poll(self) -> int | None:
        return self._poll_result

    def terminate(self) -> None:
        self._poll_result = -15

    def wait(self, timeout: float | None = None) -> int:
        return self._poll_result if self._poll_result is not None else 0

    def kill(self) -> None:
        self._poll_result = -9


def _frame(payload: dict) -> bytes:
    body = json.dumps(payload).encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body


# --------------------------------------------------------------------------
# D005.1 — per-composition gate
# --------------------------------------------------------------------------


class TestCompositionScope:
    def test_begin_composition_sets_active(self) -> None:
        bridge = HarloBridge()
        bridge.begin_composition()
        assert bridge._composition_active is True
        assert bridge._coach_called_in_composition is False

    def test_begin_composition_raises_if_already_active(self) -> None:
        bridge = HarloBridge()
        bridge.begin_composition()
        with pytest.raises(HarloCompositionAlreadyActive):
            bridge.begin_composition()

    def test_end_composition_clears_active(self) -> None:
        bridge = HarloBridge()
        bridge.begin_composition()
        bridge.end_composition()
        assert bridge._composition_active is False
        assert bridge._coach_called_in_composition is False

    def test_end_composition_raises_if_not_active(self) -> None:
        bridge = HarloBridge()
        with pytest.raises(HarloCompositionNotActive):
            bridge.end_composition()

    def test_coach_outside_composition_raises(self) -> None:
        bridge = HarloBridge()
        with pytest.raises(HarloCoachingExchangeOutsideComposition):
            bridge._coach()

    def test_coach_twice_in_one_composition_raises(self) -> None:
        bridge = HarloBridge()
        bridge.begin_composition()
        with patch.object(bridge, "_call_tool", return_value={"ok": True}):
            bridge._coach()
            with pytest.raises(HarloCoachingExchangeAlreadyDriven):
                bridge._coach()

    def test_coach_resets_across_compositions(self) -> None:
        bridge = HarloBridge()
        with patch.object(bridge, "_call_tool", return_value={"ok": True}) as ct:
            bridge.begin_composition()
            bridge._coach()
            bridge.end_composition()
            bridge.begin_composition()
            result = bridge._coach()
            bridge.end_composition()
            assert result == {"ok": True}
            assert ct.call_count == 2

    def test_drive_coaching_exchange_wraps_begin_end(self) -> None:
        bridge = HarloBridge()
        with patch.object(bridge, "_call_tool", return_value={"ok": True}):
            result = bridge.drive_coaching_exchange()
            assert result == {"ok": True}
            assert bridge._composition_active is False
            # Repeat call succeeds because each drive_* call owns its own scope.
            again = bridge.drive_coaching_exchange()
            assert again == {"ok": True}
            assert bridge._composition_active is False

    def test_end_composition_resets_gate_even_after_coach(self) -> None:
        bridge = HarloBridge()
        with patch.object(bridge, "_call_tool", return_value={"ok": True}):
            bridge.begin_composition()
            bridge._coach()
            assert bridge._coach_called_in_composition is True
            bridge.end_composition()
            assert bridge._coach_called_in_composition is False


# --------------------------------------------------------------------------
# D005.2 — read timeout via selectors
# --------------------------------------------------------------------------


class _PipeProc:
    """Wraps a real os.pipe() FD so selectors can observe readiness."""

    def __init__(self) -> None:
        self._read_fd, self._write_fd = os.pipe()
        self.stdout = os.fdopen(self._read_fd, "rb", buffering=0)
        self.stderr = io.BytesIO()
        self.stdin = io.BytesIO()
        self._poll_result: int | None = None

    def feed(self, data: bytes) -> None:
        os.write(self._write_fd, data)

    def close_write(self) -> None:
        try:
            os.close(self._write_fd)
        except OSError:
            pass

    def close(self) -> None:
        self.close_write()
        try:
            self.stdout.close()
        except Exception:
            pass

    def poll(self) -> int | None:
        return self._poll_result


class TestReadFrameTimeout:
    def test_read_frame_timeout_on_no_data(self) -> None:
        proc = _PipeProc()
        try:
            start = time.monotonic()
            with pytest.raises(HarloTimeout):
                HarloBridge()._read_frame(proc, timeout=0.1)  # type: ignore[arg-type]
            elapsed = time.monotonic() - start
            assert elapsed < 1.0
        finally:
            proc.close()

    def test_read_frame_timeout_partial_headers(self) -> None:
        proc = _PipeProc()
        try:
            # Send a partial header but never finish — should time out.
            proc.feed(b"Content-Length: 12\r\n")
            with pytest.raises(HarloTimeout):
                HarloBridge()._read_frame(proc, timeout=0.1)  # type: ignore[arg-type]
        finally:
            proc.close()

    def test_read_frame_timeout_partial_body(self) -> None:
        proc = _PipeProc()
        try:
            # Full header block but short body — should time out on body read.
            proc.feed(b"Content-Length: 32\r\n\r\n{\"jsonrpc\":")
            with pytest.raises(HarloTimeout):
                HarloBridge()._read_frame(proc, timeout=0.1)  # type: ignore[arg-type]
        finally:
            proc.close()

    def test_read_frame_completes_within_timeout(self) -> None:
        proc = _PipeProc()
        try:
            payload = {"jsonrpc": "2.0", "id": 1, "result": {"ok": True}}
            proc.feed(_frame(payload))
            result = HarloBridge()._read_frame(proc, timeout=1.0)  # type: ignore[arg-type]
            assert result == payload
        finally:
            proc.close()

    def test_read_frame_closed_stdout_raises_unreachable(self) -> None:
        proc = _PipeProc()
        proc.close_write()  # EOF immediately.
        try:
            with pytest.raises(HarloUnreachable):
                HarloBridge()._read_frame(proc, timeout=1.0)  # type: ignore[arg-type]
        finally:
            proc.close()

    def test_read_frame_malformed_content_length_raises_protocol(self) -> None:
        proc = _PipeProc()
        try:
            proc.feed(b"Content-Length: not-an-int\r\n\r\n{}")
            with pytest.raises(HarloProtocolError):
                HarloBridge()._read_frame(proc, timeout=1.0)  # type: ignore[arg-type]
        finally:
            proc.close()


# --------------------------------------------------------------------------
# D005.3 — stderr drainer
# --------------------------------------------------------------------------


def _wait_until(predicate, timeout: float = 2.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


class TestStderrDrainer:
    def test_stderr_drainer_captures_lines(self) -> None:
        bridge = HarloBridge()
        stderr = io.BytesIO(b"line one\nline two\nline three\n")
        bridge._proc = _MockProc(stderr=stderr)  # type: ignore[assignment]
        bridge._start_drainer()
        try:
            assert _wait_until(lambda: len(bridge.last_stderr()) >= 3)
            captured = bridge.last_stderr()
            assert captured[:3] == ["line one", "line two", "line three"]
        finally:
            bridge._drainer_stop.set()
            if bridge._drainer_thread is not None:
                bridge._drainer_thread.join(timeout=1.0)

    def test_stderr_drainer_ring_buffer_caps_at_64(self) -> None:
        bridge = HarloBridge()
        payload = b"".join(f"line-{i:03d}\n".encode("ascii") for i in range(100))
        stderr = io.BytesIO(payload)
        bridge._proc = _MockProc(stderr=stderr)  # type: ignore[assignment]
        bridge._start_drainer()
        try:
            assert _wait_until(lambda: len(bridge.last_stderr()) == 64)
            captured = bridge.last_stderr()
            assert len(captured) == 64
            # Deque(maxlen=64) keeps the LAST 64 lines — lines 036..099.
            assert captured[0] == "line-036"
            assert captured[-1] == "line-099"
        finally:
            bridge._drainer_stop.set()
            if bridge._drainer_thread is not None:
                bridge._drainer_thread.join(timeout=1.0)

    def test_stderr_drainer_no_deadlock_on_large_write(self) -> None:
        bridge = HarloBridge()
        # ~80 KB of stderr — well above any typical pipe buffer.
        payload = b"".join(
            f"chunk-line-{i:05d}-payload-padding-padding-padding\n".encode("ascii")
            for i in range(2000)
        )
        stderr = io.BytesIO(payload)
        bridge._proc = _MockProc(stderr=stderr)  # type: ignore[assignment]
        bridge._start_drainer()
        try:
            # _wait_until functionally verifies non-deadlocking behavior;
            # an explicit wall-clock bound was brittle under loaded CI runners.
            assert _wait_until(lambda: len(bridge.last_stderr()) == 64)
            assert len(bridge.last_stderr()) == 64
        finally:
            bridge._drainer_stop.set()
            if bridge._drainer_thread is not None:
                bridge._drainer_thread.join(timeout=1.0)

    def test_stderr_drainer_thread_joins_on_close(self) -> None:
        bridge = HarloBridge()
        stderr = io.BytesIO(b"only-line\n")
        bridge._proc = _MockProc(stderr=stderr)  # type: ignore[assignment]
        bridge._start_drainer()
        assert _wait_until(lambda: len(bridge.last_stderr()) >= 1)
        bridge.close()
        assert bridge._drainer_thread is None
        # No lingering live drainer threads.
        live = [t for t in threading.enumerate() if t.name == "HarloBridge._drain_stderr" and t.is_alive()]
        assert live == []

    def test_last_stderr_returns_copy_not_internal_deque(self) -> None:
        bridge = HarloBridge()
        bridge._stderr_ring.append("a")
        bridge._stderr_ring.append("b")
        snapshot = bridge.last_stderr()
        assert snapshot == ["a", "b"]
        assert isinstance(snapshot, list)
        # Mutating the snapshot must not touch the underlying ring.
        snapshot.append("c")
        assert list(bridge._stderr_ring) == ["a", "b"]

    def test_stderr_ring_is_bounded_deque(self) -> None:
        bridge = HarloBridge()
        assert isinstance(bridge._stderr_ring, collections.deque)
        assert bridge._stderr_ring.maxlen == 64


# --------------------------------------------------------------------------
# Frame coalescing — round-3 _recv_buffer regression coverage (belief c007)
# --------------------------------------------------------------------------


class TestFrameCoalescing:
    """Regress the round-3 fix: when a single os.read() returns bytes from
    two LSP frames concatenated, the trailing bytes beyond content_length
    MUST be buffered in `self._recv_buffer` and reused on the next
    `_read_frame_with_timeout` call. Without the buffer, the second frame's
    head was dropped and subsequent RPCs desynchronized.
    """

    def test_two_frames_in_one_read_both_decoded(self) -> None:
        proc = _PipeProc()
        try:
            bridge = HarloBridge()
            payload_one = {"jsonrpc": "2.0", "id": 1, "result": {"step": "first"}}
            payload_two = {"jsonrpc": "2.0", "id": 2, "result": {"step": "second"}}
            # Write BOTH frames in a single os.write — the read side will
            # very likely receive them in one os.read(), exercising the
            # coalescing path.
            proc.feed(_frame(payload_one) + _frame(payload_two))
            first = bridge._read_frame_with_timeout(proc, timeout=1.0)  # type: ignore[arg-type]
            assert first == payload_one
            # The second call must NOT block on the pipe (the bytes are
            # already in _recv_buffer); a generous timeout protects CI but
            # the call should return immediately on the happy path.
            second = bridge._read_frame_with_timeout(proc, timeout=1.0)  # type: ignore[arg-type]
            assert second == payload_two
            # After consuming both frames cleanly, the buffer is drained.
            assert len(bridge._recv_buffer) == 0
        finally:
            proc.close()

    def test_partial_second_frame_buffered(self) -> None:
        proc = _PipeProc()
        try:
            bridge = HarloBridge()
            payload_one = {"jsonrpc": "2.0", "id": 10, "result": {"ok": True}}
            payload_two = {"jsonrpc": "2.0", "id": 11, "result": {"ok": "again"}}
            frame_two = _frame(payload_two)
            # Frame-1 complete, then only the header block of frame-2 (split
            # at the body boundary so phase-2 has bytes but phase-3 must
            # wait for more).
            header_end = frame_two.index(b"\r\n\r\n") + 4
            head_only = frame_two[:header_end]
            tail = frame_two[header_end:]
            proc.feed(_frame(payload_one) + head_only)
            first = bridge._read_frame_with_timeout(proc, timeout=1.0)  # type: ignore[arg-type]
            assert first == payload_one
            # Buffer must hold the partial frame-2 header bytes for the next
            # call — proves the coalesce path didn't discard them.
            assert len(bridge._recv_buffer) > 0
            assert bytes(bridge._recv_buffer) == head_only
            # Feed the remaining body and complete the second read.
            proc.feed(tail)
            second = bridge._read_frame_with_timeout(proc, timeout=1.0)  # type: ignore[arg-type]
            assert second == payload_two
            assert len(bridge._recv_buffer) == 0
        finally:
            proc.close()

    def test_recv_buffer_cleared_on_close(self) -> None:
        proc = _PipeProc()
        try:
            bridge = HarloBridge()
            payload_one = {"jsonrpc": "2.0", "id": 20, "result": {"ok": True}}
            payload_two = {"jsonrpc": "2.0", "id": 21, "result": {"ok": True}}
            frame_two = _frame(payload_two)
            # Frame-1 complete + partial frame-2 (header only) so that after
            # reading frame-1, _recv_buffer has leftover bytes.
            header_end = frame_two.index(b"\r\n\r\n") + 4
            proc.feed(_frame(payload_one) + frame_two[:header_end])
            first = bridge._read_frame_with_timeout(proc, timeout=1.0)  # type: ignore[arg-type]
            assert first == payload_one
            assert len(bridge._recv_buffer) > 0
            # close() must drain the buffer so a fresh proc handle doesn't
            # inherit stale bytes from a previous subprocess generation.
            bridge.close()
            assert len(bridge._recv_buffer) == 0
        finally:
            proc.close()
