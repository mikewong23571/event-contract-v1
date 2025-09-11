import builtins
import importlib
import sys


def run_cli(argv):
    mod = importlib.import_module("src.cli.signal_cli")
    return mod.main(argv)


def test_signal_cli_help(capsys):
    code = run_cli(["--help"])  # argparse prints and exits 0
    assert code == 0


def test_signal_cli_version(capsys):
    code = run_cli(["--version"])  # prints version
    assert code == 0


def test_signal_cli_generate_sample_json(capsys):
    code = run_cli([
        "--format",
        "json",
        "generate",
        "--symbol",
        "BTCUSDT",
        "--sample-data",
        "--data-points",
        "5",
    ])
    captured = capsys.readouterr()
    assert code == 0
    assert "BTCUSDT" in captured.out

