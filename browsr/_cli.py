"""
browsr command line interface
"""

from typing import Optional

import click
import rich_click

from browsr._base import (
    TextualAppContext,
)
from browsr._version import __application__, __version__
from browsr.browsr import Browsr

rich_click.rich_click.MAX_WIDTH = 100
rich_click.rich_click.STYLE_OPTION = "bold green"
rich_click.rich_click.STYLE_SWITCH = "bold blue"
rich_click.rich_click.STYLE_METAVAR = "bold red"
rich_click.rich_click.STYLE_HELPTEXT_FIRST_LINE = "bold blue"
rich_click.rich_click.STYLE_HELPTEXT = ""
rich_click.rich_click.STYLE_HEADER_TEXT = "bold green"
rich_click.rich_click.STYLE_OPTION_DEFAULT = "bold yellow"
rich_click.rich_click.STYLE_OPTION_HELP = ""
rich_click.rich_click.STYLE_ERRORS_SUGGESTION = "bold red"
rich_click.rich_click.STYLE_OPTIONS_TABLE_BOX = "SIMPLE_HEAVY"
rich_click.rich_click.STYLE_COMMANDS_TABLE_BOX = "SIMPLE_HEAVY"


@click.command(name="browsr", cls=rich_click.rich_command.RichCommand)
@click.argument("path", default=None, required=False, metavar="PATH")
@click.option(
    "-m",
    "--max-file-size",
    default=20,
    type=int,
    help="Maximum file size in MB for the application to open",
)
@click.version_option(version=__version__, prog_name=__application__)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable extra debugging output",
    type=click.BOOL,
)
def browsr(
    path: Optional[str],
    debug: bool,
    max_file_size: int,
) -> None:
    """
    **`browsr`** is a file browser TUI (textual user interface) application. The application
    allows you to visually browse through a directory (local or cloud) and display the
    contents of its files

    \f

    ![browsr](https://raw.githubusercontent.com/juftin/browsr/main/docs/_static/screenshot_utils.png)

    ## Installation

    It's recommended to install **`browsr`** via [pipx](https://pypa.github.io/pipx/)
    with **`all`** optional dependencies, this enables **`browsr`** to access
    remote cloud storage buckets and open parquet files.

    ```shell
    pipx install "browsr[all]"
    ```

    ## Usage Examples

    - Load your current working directory: **`browsr`**
    - Load a specific directory: **`browsr /path/to/directory`**
    - Load an S3 bucket: **`browsr s3://bucket-name`**
    - Load a GCS bucket: **`browsr gs://bucket-name`**

    ## Key Bindings
    - **`q`** - Quit the application
    - **`f`** - Toggle the file tree sidebar
    - **`t`** - Toggle the rich theme for code formatting
    - **`n`** - Toggle line numbers for code formatting
    - **`d`** - Toggle dark mode for the application
    - **`x`** - Download the file from cloud storage
    """
    config = TextualAppContext(file_path=path, debug=debug, max_file_size=max_file_size)
    app = Browsr(config_object=config)
    app.run()


if __name__ == "__main__":
    browsr()
