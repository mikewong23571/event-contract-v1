import importlib


def run_cli(argv):
    mod = importlib.import_module("src.cli.data_cli")
    return mod.main(argv)


def test_data_cli_help():
    assert run_cli(["--help"]) == 0


def test_data_cli_version():
    assert run_cli(["--version"]) == 0


def test_data_cli_ingest_json(capsys):
    code = run_cli(["ingest", "--symbols", "BTCUSDT,ETHUSDT", "--limit", "3"]) 
    assert code == 0
    out = capsys.readouterr().out
    assert "BTCUSDT" in out or "symbols" in out

