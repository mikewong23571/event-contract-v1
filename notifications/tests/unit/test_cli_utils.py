from notifications.src.cli._utils import get_version, print_output


def test_get_version_returns_string():
    v = get_version("event-contract-notifications", "0.0.0")
    assert isinstance(v, str)
    assert len(v) > 0


def test_print_output_text_non_str(capsys):
    print_output({"a": 1}, "text")
    captured = capsys.readouterr().out
    assert "\"a\": 1" in captured

