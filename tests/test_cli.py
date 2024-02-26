"""
Testing of the Demo Class
"""

from click.testing import CliRunner

from browsr.cli import browsr


def test_cli_main(runner: CliRunner) -> None:
    """
    Test the main function of the CLI
    """
    result = runner.invoke(browsr, ["--help"])
    assert result.exit_code == 0


def test_cli_bad_path(runner: CliRunner) -> None:
    """
    Test the main function of the CLI
    """
    result = runner.invoke(browsr, ["not_a_real_path.csv"])
    assert result.exit_code == 0
