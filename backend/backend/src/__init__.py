"""Namespace path extender for `backend.src`.

Ensures `import backend.src.xxx` resolves to modules under the real `backend/src`.
"""
from __future__ import annotations

import pkgutil
from pathlib import Path

# Extend the package search path to include the real src directory
__path__ = pkgutil.extend_path(__path__, __name__)  # type: ignore[name-defined]

_real_src = Path(__file__).resolve().parents[2] / "src"
if _real_src.is_dir():
    __path__.append(str(_real_src))  # type: ignore[attr-defined]

