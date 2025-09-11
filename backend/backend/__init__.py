"""Shim package to support test imports like `backend.src.*` when running tests
from the component directory.

This avoids changing tests by exposing a `backend.src` package that points to
the real `backend/src` module tree.
"""

