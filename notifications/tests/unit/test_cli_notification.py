import importlib


def run_cli(argv):
    mod = importlib.import_module("src.cli.notification_cli")
    return mod.main(argv)


def test_notification_cli_help():
    assert run_cli(["--help"]) == 0


def test_notification_cli_version():
    assert run_cli(["--version"]) == 0

