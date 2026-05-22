# Cloned from Harlo (github.com/JosephOIbrahim/Harlo). Specialized for Hanna.
"""Read-only MCP-stdio client to Harlo.

See `docs/SPIKE_HARLO_EDGE_2026-05-20.md` for the reconciled contract and
`docs/DECISIONS.md` D001 for the Rule 35 permissive reading that authorizes
the `coach`-wrapping method below.
"""

from __future__ import annotations

import collections
import json
import os
import selectors
import subprocess
import threading
import time
from types import TracebackType
from typing import Any


class HarloUnreachable(RuntimeError):
    """Subprocess failed to spawn, exited, or did not respond in time."""


class HarloProtocolError(RuntimeError):
    """Malformed JSON-RPC frame or unexpected response shape."""


class HarloTimeout(RuntimeError):
    """Harlo subprocess did not produce a frame within the timeout."""


class HarloCoachingExchangeAlreadyDriven(RuntimeError):
    """coach already called in the current composition (rate-limited per D001)."""


class HarloCompositionAlreadyActive(RuntimeError):
    """begin_composition called while another composition is already active."""


class HarloCompositionNotActive(RuntimeError):
    """end_composition or coach called outside an active composition."""


class HarloCoachingExchangeOutsideComposition(RuntimeError):
    """coach called outside a begin_composition / end_composition scope."""


class HarloBridge:
    def __init__(
        self,
        harlo_command: list[str] | None = None,
        startup_timeout_seconds: float = 5.0,
    ) -> None:
        self._command = list(harlo_command) if harlo_command else ["harlo", "mcp"]
        self._startup_timeout = startup_timeout_seconds
        self._proc: subprocess.Popen[bytes] | None = None
        # RLock — the first _rpc("initialize") is recursively invoked from
        # _ensure_proc while the outer caller already holds the lock.
        self._lock = threading.RLock()
        self._next_id = 1
        # Per-composition gate (D005.1).
        self._composition_active = False
        self._coach_called_in_composition = False
        # Background stderr drainer (D005.3).
        self._stderr_ring: collections.deque[str] = collections.deque(maxlen=64)
        self._drainer_thread: threading.Thread | None = None
        self._drainer_stop = threading.Event()
        # Trailing bytes from the previous frame read (D005.2 — frame coalescing).
        self._recv_buffer: bytearray = bytearray()

    # --- lifecycle ----------------------------------------------------

    def __enter__(self) -> "HarloBridge":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        with self._lock:
            self._drainer_stop.set()
            if self._proc and self._proc.poll() is None:
                try:
                    self._proc.terminate()
                    self._proc.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
            if self._drainer_thread and self._drainer_thread.is_alive():
                self._drainer_thread.join(timeout=2.0)
            self._drainer_thread = None
            self._proc = None
            self._recv_buffer.clear()

    # --- composition scope (D005.1) -----------------------------------

    def begin_composition(self) -> None:
        with self._lock:
            if self._composition_active:
                raise HarloCompositionAlreadyActive(
                    "begin_composition called while another composition is already active"
                )
            self._composition_active = True
            self._coach_called_in_composition = False

    def end_composition(self) -> None:
        with self._lock:
            if not self._composition_active:
                raise HarloCompositionNotActive(
                    "end_composition called outside an active composition"
                )
            self._composition_active = False
            self._coach_called_in_composition = False

    # --- cheap reads (wrap Harlo `status`) ---------------------------

    def read_state(self) -> dict:
        return self._call_tool("status")["v9"]

    def read_burnout_level(self) -> str:
        return self.read_state()["state"]["burnout"]

    def read_schedule(self) -> dict:
        return self.read_state()["schedule"]

    def read_prediction(self) -> dict | None:
        return self.read_state()["prediction"]

    # --- heavy drive (wraps Harlo `coach`, rate-limited per D001) ----

    def _coach(self, session_id: str | None = None) -> dict:
        with self._lock:
            if not self._composition_active:
                raise HarloCoachingExchangeOutsideComposition(
                    "coach called outside a begin_composition / end_composition scope"
                )
            if self._coach_called_in_composition:
                raise HarloCoachingExchangeAlreadyDriven(
                    "coach already called in this composition (rate-limited per D001)"
                )
            self._coach_called_in_composition = True
        args: dict[str, Any] = {}
        if session_id is not None:
            args["session_id"] = session_id
        return self._call_tool("coach", **args)

    def drive_coaching_exchange(self, session_id: str | None = None) -> dict:
        self.begin_composition()
        try:
            return self._coach(session_id=session_id)
        finally:
            self.end_composition()

    # --- memory queries (wrap Harlo `recall` / `query_past_experience` / `patterns`) ---

    def recall(self, query: str, depth: str = "normal") -> dict:
        return self._call_tool("recall", query=query, depth=depth)

    def query_past_experience(self, query: str, limit: int = 10) -> dict:
        return self._call_tool("query_past_experience", query=query, limit=limit)

    def patterns(self) -> dict:
        return self._call_tool("patterns")

    # --- stderr drainer (D005.3) -------------------------------------

    def last_stderr(self) -> list[str]:
        return list(self._stderr_ring)

    def _start_drainer(self) -> None:
        if self._proc is None or self._proc.stderr is None:
            return
        self._drainer_stop.clear()
        self._drainer_thread = threading.Thread(
            target=self._drain_stderr,
            name="HarloBridge._drain_stderr",
            daemon=True,
        )
        self._drainer_thread.start()

    def _drain_stderr(self) -> None:
        if self._proc is None or self._proc.stderr is None:
            return
        stderr = self._proc.stderr
        while not self._drainer_stop.is_set():
            try:
                line = stderr.readline()
            except (ValueError, OSError):
                break
            if not line:
                break  # EOF — subprocess closed stderr.
            try:
                text = line.decode("utf-8", errors="replace").rstrip("\r\n")
            except Exception:
                text = repr(line)
            self._stderr_ring.append(text)

    # --- MCP stdio plumbing ------------------------------------------

    def _ensure_proc(self) -> subprocess.Popen[bytes]:
        if self._proc and self._proc.poll() is None:
            return self._proc
        try:
            self._proc = subprocess.Popen(
                self._command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
            )
        except (FileNotFoundError, OSError) as e:
            raise HarloUnreachable(f"failed to spawn Harlo subprocess {self._command!r}: {e}") from e
        self._start_drainer()
        self._rpc("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "hanna-harlo-bridge", "version": "0.1.0"},
        }, timeout=self._startup_timeout)
        self._send_notification("notifications/initialized", {})
        return self._proc

    def _call_tool(self, name: str, **arguments: Any) -> dict:
        result = self._rpc("tools/call", {"name": name, "arguments": arguments})
        content = result.get("content")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    try:
                        return json.loads(item["text"])
                    except (KeyError, json.JSONDecodeError) as e:
                        raise HarloProtocolError(f"tool {name!r} returned non-JSON text content: {e}") from e
        if isinstance(result.get("structuredContent"), dict):
            return result["structuredContent"]
        raise HarloProtocolError(f"tool {name!r} returned no parsable content: {result!r}")

    def _rpc(self, method: str, params: dict, timeout: float | None = None) -> dict:
        with self._lock:
            proc = self._ensure_proc()
            req_id = self._next_id
            self._next_id += 1
            self._write_frame(proc, {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params})
            response = self._read_frame(proc, timeout=timeout)
        if response.get("id") != req_id:
            raise HarloProtocolError(f"id mismatch: expected {req_id}, got {response.get('id')!r}")
        if "error" in response:
            raise HarloProtocolError(f"JSON-RPC error from {method!r}: {response['error']!r}")
        if "result" not in response:
            raise HarloProtocolError(f"JSON-RPC response missing result: {response!r}")
        return response["result"]

    def _send_notification(self, method: str, params: dict) -> None:
        with self._lock:
            proc = self._ensure_proc()
            self._write_frame(proc, {"jsonrpc": "2.0", "method": method, "params": params})

    @staticmethod
    def _write_frame(proc: subprocess.Popen[bytes], message: dict) -> None:
        if proc.stdin is None:
            raise HarloUnreachable("Harlo subprocess has no stdin")
        body = json.dumps(message).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        try:
            proc.stdin.write(header + body)
            proc.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            raise HarloUnreachable(f"failed to write frame to Harlo: {e}") from e

    def _read_frame(self, proc: subprocess.Popen[bytes], timeout: float | None = None) -> dict:
        if proc.stdout is None:
            raise HarloUnreachable("Harlo subprocess has no stdout")
        # MCP stdio uses Content-Length-prefixed JSON frames (LSP-style).
        if timeout is None:
            # Legacy blocking path — preserved for callers passing None.
            return HarloBridge._read_frame_blocking(proc)
        return self._read_frame_with_timeout(proc, timeout)

    @staticmethod
    def _read_frame_blocking(proc: subprocess.Popen[bytes]) -> dict:
        assert proc.stdout is not None
        content_length: int | None = None
        while True:
            line = proc.stdout.readline()
            if not line:
                raise HarloUnreachable("Harlo subprocess closed stdout before sending a frame")
            line = line.rstrip(b"\r\n")
            if not line:
                break
            if line.lower().startswith(b"content-length:"):
                try:
                    content_length = int(line.split(b":", 1)[1].strip())
                except ValueError as e:
                    raise HarloProtocolError(f"bad Content-Length header: {line!r}") from e
        if content_length is None:
            raise HarloProtocolError("frame missing Content-Length header")
        body = proc.stdout.read(content_length)
        if len(body) != content_length:
            raise HarloUnreachable(f"short read: expected {content_length} bytes, got {len(body)}")
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise HarloProtocolError(f"malformed JSON frame: {e}") from e

    def _read_frame_with_timeout(self, proc: subprocess.Popen[bytes], timeout: float) -> dict:
        assert proc.stdout is not None
        deadline = time.monotonic() + timeout
        sel = selectors.DefaultSelector()
        try:
            fd = proc.stdout.fileno()
        except (AttributeError, OSError) as e:
            raise HarloUnreachable(f"Harlo stdout has no usable fd: {e}") from e
        sel.register(proc.stdout, selectors.EVENT_READ)
        try:
            # Seed buf with any bytes left over from the previous frame read so
            # frame coalescing (two frames in one TCP write) doesn't drop the
            # tail of the previous read.
            buf = bytearray(self._recv_buffer)
            self._recv_buffer.clear()
            content_length: int | None = None
            header_end = buf.find(b"\r\n\r\n")
            # Phase 1: read until the header block separator appears.
            while header_end < 0:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise HarloTimeout(f"Harlo did not send frame headers within {timeout}s")
                ready = sel.select(timeout=remaining)
                if not ready:
                    raise HarloTimeout(f"Harlo did not send frame headers within {timeout}s")
                try:
                    chunk = os.read(fd, 4096)
                except (BlockingIOError, InterruptedError):
                    continue
                except OSError as e:
                    raise HarloUnreachable(f"failed to read from Harlo stdout: {e}") from e
                if not chunk:
                    raise HarloUnreachable("Harlo subprocess closed stdout before sending a frame")
                buf.extend(chunk)
                header_end = buf.find(b"\r\n\r\n")
            # Phase 2: parse Content-Length out of header block.
            for line in bytes(buf[:header_end]).split(b"\r\n"):
                if line.lower().startswith(b"content-length:"):
                    try:
                        content_length = int(line.split(b":", 1)[1].strip())
                    except ValueError as e:
                        raise HarloProtocolError(f"bad Content-Length header: {line!r}") from e
            if content_length is None:
                raise HarloProtocolError("frame missing Content-Length header")
            # Phase 3: take only this frame's body from buf; save trailing
            # bytes (e.g. start of the next frame) into the recv buffer for
            # the next _read_frame_with_timeout call.
            body_start = header_end + 4
            body = bytearray(buf[body_start:body_start + content_length])
            if len(buf) > body_start + content_length:
                self._recv_buffer.extend(buf[body_start + content_length:])
            while len(body) < content_length:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise HarloTimeout(f"Harlo did not send frame body within {timeout}s")
                ready = sel.select(timeout=remaining)
                if not ready:
                    raise HarloTimeout(f"Harlo did not send frame body within {timeout}s")
                try:
                    chunk = os.read(fd, content_length - len(body))
                except (BlockingIOError, InterruptedError):
                    continue
                except OSError as e:
                    raise HarloUnreachable(f"failed to read from Harlo stdout: {e}") from e
                if not chunk:
                    raise HarloUnreachable("Harlo subprocess closed stdout mid-body")
                body.extend(chunk)
            try:
                return json.loads(bytes(body[:content_length]).decode("utf-8"))
            except json.JSONDecodeError as e:
                raise HarloProtocolError(f"malformed JSON frame: {e}") from e
        finally:
            try:
                sel.unregister(proc.stdout)
            except (KeyError, ValueError):
                pass
            sel.close()
