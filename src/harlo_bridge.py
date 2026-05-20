# Cloned from Harlo (github.com/JosephOIbrahim/Harlo). Specialized for Hanna.
"""Read-only MCP-stdio client to Harlo.

See `docs/SPIKE_HARLO_EDGE_2026-05-20.md` for the reconciled contract and
`docs/DECISIONS.md` D001 for the Rule 35 permissive reading that authorizes
the `coach`-wrapping method below.
"""

from __future__ import annotations

import json
import subprocess
import threading
from types import TracebackType
from typing import Any


class HarloUnreachable(RuntimeError):
    """Subprocess failed to spawn, exited, or did not respond in time."""


class HarloProtocolError(RuntimeError):
    """Malformed JSON-RPC frame or unexpected response shape."""


class HarloCoachingExchangeAlreadyDriven(RuntimeError):
    """drive_coaching_exchange called more than once on this bridge instance."""


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
        self._coach_driven = False

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
            if self._proc and self._proc.poll() is None:
                try:
                    self._proc.terminate()
                    self._proc.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
            self._proc = None

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

    def drive_coaching_exchange(self, session_id: str | None = None) -> dict:
        if self._coach_driven:
            raise HarloCoachingExchangeAlreadyDriven(
                "drive_coaching_exchange already called on this HarloBridge instance"
            )
        self._coach_driven = True
        args: dict[str, Any] = {}
        if session_id is not None:
            args["session_id"] = session_id
        return self._call_tool("coach", **args)

    # --- memory queries (wrap Harlo `recall` / `query_past_experience` / `patterns`) ---

    def recall(self, query: str, depth: str = "normal") -> dict:
        return self._call_tool("recall", query=query, depth=depth)

    def query_past_experience(self, query: str, limit: int = 10) -> dict:
        return self._call_tool("query_past_experience", query=query, limit=limit)

    def patterns(self) -> dict:
        return self._call_tool("patterns")

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

    @staticmethod
    def _read_frame(proc: subprocess.Popen[bytes], timeout: float | None = None) -> dict:
        if proc.stdout is None:
            raise HarloUnreachable("Harlo subprocess has no stdout")
        # MCP stdio uses Content-Length-prefixed JSON frames (LSP-style).
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
