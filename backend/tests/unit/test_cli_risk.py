import importlib


def run_cli(argv):
    mod = importlib.import_module("src.cli.risk_cli")
    return mod.main(argv)


def test_risk_cli_help():
    assert run_cli(["--help"]) == 0


def test_risk_cli_version():
    assert run_cli(["--version"]) == 0


def test_risk_cli_position_size():
    code = run_cli([
        "position-size",
        "--symbol",
        "BTCUSDT",
        "--probability",
        "0.6",
        "--account-balance",
        "1000",
    ])
    assert code == 0

