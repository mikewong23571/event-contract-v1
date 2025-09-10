from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from jinja2 import Environment, FileSystemLoader, DictLoader, TemplateNotFound, StrictUndefined


def _filter_strftime(value: Any, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    if isinstance(value, datetime):
        return value.strftime(fmt)
    # try to parse ISO strings
    try:
        dt = datetime.fromisoformat(str(value))
        return dt.strftime(fmt)
    except Exception:  # noqa: BLE001
        return str(value)


class TemplateEngine:
    """Jinja2-based template engine for notifications (T075).

    Features:
      - Load templates from directories or register in-memory templates
      - Strict undefined variables (raises) to catch mistakes early
      - Helpful default filters (strftime)
    """

    def __init__(
        self,
        template_dirs: Optional[List[str]] = None,
        *,
        default_language: str = "en",
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.default_language = default_language

        loaders = []  # type: List
        if template_dirs:
            loaders.append(FileSystemLoader(template_dirs))
        # Always include an in-memory loader for dynamically added templates
        self._memory_loader = DictLoader({})
        loaders.append(self._memory_loader)

        loader = loaders[0] if len(loaders) == 1 else tuple(loaders)
        self.env = Environment(
            loader=loader,  # type: ignore[arg-type]
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined,
        )
        # Filters
        self.env.filters["strftime"] = _filter_strftime

    def register_template(self, name: str, content: str) -> None:
        """Register an in-memory template by name."""
        self._memory_loader.mapping[name] = content

    def get_template(self, name: str):  # type: ignore[override]
        return self.env.get_template(name)

    def list_templates(self) -> List[str]:
        # FileSystemLoader does not expose names without scanning the FS.
        # We only list in-memory registered templates to keep it predictable.
        return sorted(self._memory_loader.mapping.keys())

    def render(
        self,
        template_name_or_content: str,
        context: Dict[str, Any],
        *,
        is_raw: bool = False,
    ) -> str:
        """Render a template by name or from raw content.

        When `is_raw=True`, the input is treated as a raw Jinja2 template.
        When `is_raw=False`, the engine attempts to load a named template. If
        not found, it falls back to treating the input as raw content.
        """

        try:
            if is_raw:
                tpl = self.env.from_string(template_name_or_content)
            else:
                try:
                    tpl = self.get_template(template_name_or_content)
                except TemplateNotFound:
                    # Fallback: treat as a raw template string
                    tpl = self.env.from_string(template_name_or_content)
            return tpl.render(**context)
        except Exception as e:  # noqa: BLE001
            # Keep error message explicit for easier debugging by callers
            return f"Template rendering error: {e}"

    def validate_template(self, content: str, sample_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a template by attempting to render with the provided context."""
        try:
            tpl = self.env.from_string(content)
            rendered = tpl.render(**sample_context)
            return {"valid": True, "issues": [], "preview": rendered[:500]}
        except Exception as e:  # noqa: BLE001
            return {"valid": False, "issues": [str(e)], "preview": None}


__all__ = ["TemplateEngine"]

