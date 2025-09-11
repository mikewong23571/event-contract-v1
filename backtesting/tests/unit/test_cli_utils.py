from backtesting.src.cli._utils import get_version, print_output


def test_get_version_returns_string():
    v = get_version("event-contract-backtesting", "0.0.0")
    assert isinstance(v, str)
    assert len(v) > 0


def test_print_output_json(capsys):
    data = {"a": 1}
    print_output(data, "json")
    captured = capsys.readouterr().out
    assert "\n" in captured and "\"a\": 1" in captured

