"""CLI utilities for backend package.

Provides small shared helpers to avoid duplication across CLI modules.
"""

from __future__ import annotations

import json
from typing import Any

try:  # pragma: no cover - importlib metadata sometimes unavailable in tests
    from importlib.metadata import version as _pkg_version
except Exception:  # pragma: no cover
    _pkg_version = None  # type: ignore


def get_version(package_name: str, default_version: str) -> str:
    """Return installed package version or a default fallback.

    Parameters
    - package_name: distribution name for this component
    - default_version: fallback when package metadata is unavailable
    """
    try:
        if _pkg_version is not None:
            return _pkg_version(package_name)
    except Exception:
        # Fall through to default version
        pass
    return default_version


def print_output(data: Any, fmt: str) -> None:
    """Print data in JSON or plain text format.

    - fmt: "json" or "text"
    - Non-string values in text mode are pretty-printed JSON
    """
    if fmt == "json":
        print(json.dumps(data, indent=2, default=str))
    else:
        if isinstance(data, str):
            print(data)
        else:
            print(json.dumps(data, indent=2, default=str))

