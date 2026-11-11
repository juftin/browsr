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


def test_local_path_containing_github_resolves_locally(tmp_path) -> None:
    """
    A local directory whose name merely contains 'github' must resolve
    to the local filesystem instead of raising "Invalid GitHub URL".
    """
    from browsr.base import TextualAppContext

    target = tmp_path / "my-github-notes"
    target.mkdir()
    resolved = TextualAppContext(file_path=str(target)).path
    assert "github://" not in str(resolved)
    assert str(resolved).endswith("my-github-notes")
