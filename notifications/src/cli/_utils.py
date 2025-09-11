"""CLI utilities for notifications package."""

from __future__ import annotations

import json
from typing import Any

try:  # pragma: no cover
    from importlib.metadata import version as _pkg_version
except Exception:  # pragma: no cover
    _pkg_version = None  # type: ignore


def get_version(package_name: str, default_version: str) -> str:
    try:
        if _pkg_version is not None:
            return _pkg_version(package_name)
    except Exception:
        pass
    return default_version


def print_output(data: Any, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, indent=2, default=str))
    else:
        if isinstance(data, str):
            print(data)
        else:
            print(json.dumps(data, indent=2, default=str))

