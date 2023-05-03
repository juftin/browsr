"""
Testing of the Demo Class
"""

from click.testing import CliRunner

from browsr.code_browser import browse


def test_cli_main(runner: CliRunner) -> None:
    """
    Test the main function of the CLI
    """
    result = runner.invoke(browse, ["--help"])
    assert result.exit_code == 0
