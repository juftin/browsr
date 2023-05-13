"""
Testing of the Demo Class
"""

from click.testing import CliRunner

from browsr._cli import browsr


def test_cli_main(runner: CliRunner) -> None:
    """
    Test the main function of the CLI
    """
    result = runner.invoke(browsr, ["--help"])
    assert result.exit_code == 0
