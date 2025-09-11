import importlib


def run_cli(argv):
    mod = importlib.import_module("src.cli.backtest_cli")
    return mod.main(argv)


def test_backtest_cli_help():
    assert run_cli(["--help"]) == 0


def test_backtest_cli_version():
    assert run_cli(["--version"]) == 0


def test_backtest_cli_backtest_minimal():
    code = run_cli([
        "--format",
        "json",
        "backtest",
        "--strategy-name",
        "SMA",
        "--symbol",
        "BTCUSDT",
        "--days",
        "1",
    ])
    assert code == 0

