"""Stdlib-only logging helper for Hanna lane-boundary diagnostics.

One configuration point. Idempotent. Honors HANNA_LOG_LEVEL.

Rule 36 voice applies to log messages produced through these loggers:
surface, don't decide. Log call sites in `src/` and `scripts/` MUST NOT
use directive language ("you should...", "retry now", etc.).
"""

from __future__ import annotations

import logging
import os
import sys

_FORMAT = "%(asctime)s.%(msecs)03dZ %(levelname)s %(name)s: %(message)s"
_DATEFMT = "%Y-%m-%dT%H:%M:%S"
_CONFIGURED = False


def _resolve_level() -> int:
    raw = os.environ.get("HANNA_LOG_LEVEL", "INFO").strip().upper()
    return getattr(logging, raw, logging.INFO) if raw else logging.INFO


def _configure_once() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    # Use Formatter directly so asctime is rendered in UTC (the trailing 'Z'
    # in the format string is a literal; we ensure converter is gmtime so
    # the rendered value matches that literal).
    logging.Formatter.converter = __import__("time").gmtime
    logging.basicConfig(
        level=_resolve_level(),
        format=_FORMAT,
        datefmt=_DATEFMT,
        stream=sys.stderr,
    )
    # basicConfig is a no-op if root already has handlers; force-apply the
    # level + formatter so behavior is deterministic across import orders.
    root = logging.getLogger()
    root.setLevel(_resolve_level())
    formatter = logging.Formatter(fmt=_FORMAT, datefmt=_DATEFMT)
    for handler in root.handlers:
        handler.setFormatter(formatter)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger. First call configures the root logger."""
    _configure_once()
    return logging.getLogger(name)
