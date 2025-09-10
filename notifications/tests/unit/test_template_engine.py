import os
import sys

import pytest


# Ensure package src is importable
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from templates.template_engine import TemplateEngine  # type: ignore  # noqa: E402


def test_template_engine_render_basic():
    engine = TemplateEngine()
    engine.register_template(
        "signal_generated",
        """
        🚀 New Trading Signal\n\n
        Symbol: {{ symbol }}\n
        Direction: {{ direction }}\n
        Probability: {{ (probability * 100) | round(1) }}%\n
        Confidence: {{ confidence }}\n
        Expires: {{ expiry_time }}\n
        """,
    )

    rendered = engine.render(
        "signal_generated",
        {
            "symbol": "BTCUSDT",
            "direction": "UP",
            "probability": 0.72,
            "confidence": "HIGH",
            "expiry_time": "15:30 UTC",
        },
    )

    assert "BTCUSDT" in rendered
    assert "72.0%" in rendered
    assert "HIGH" in rendered


def test_template_engine_validate_and_raw_render():
    engine = TemplateEngine()

    # Missing variable should be caught by StrictUndefined
    invalid = engine.validate_template("Hello {{ name }}", sample_context={})
    assert not invalid["valid"]

    # Provide the context correctly
    valid = engine.validate_template("Hello {{ name }}", sample_context={"name": "Alice"})
    assert valid["valid"]
    assert "Alice" in valid["preview"]

    # Raw rendering fallback
    out = engine.render("Hello {{ who }}", {"who": "World"}, is_raw=True)
    assert out.strip() == "Hello World"

