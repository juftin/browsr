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
    browsr 🗂️  a pleasant file explorer in your terminal

    Navigate through directories and peek at files whether they're hosted locally,
    over SSH, in GitHub, AWS S3, Google Cloud Storage, or Azure Blob Storage. View code files
    with syntax highlighting, format JSON files, render images, convert data files to navigable
    datatables, and more.

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

    ### Local

    #### Browse your current working directory

    ```shell
    browsr
    ```

    #### Browse a local directory

    ```shell
    browsr/path/to/directory
    ```

    ### Cloud Storage

    #### Browse an S3 bucket

    ```shell
    browsr s3://bucket-name
    ```

    #### Browse a GCS bucket

    ```shell
    browsr gs://bucket-name
    ```

    #### Browse Azure Services

    ```shell
    browsr adl://bucket-name
    browsr az://bucket-name
    ```

    ### GitHub

    #### Browse a GitHub repository

    ```shell
    browsr github://juftin:browsr
    ```

    #### Browse a GitHub Repository Branch

    ```shell
    browsr github://juftin:browsr@main
    ```

    #### Browse a Private GitHub Repository

    ```shell
    export GITHUB_TOKEN="ghp_1234567890"
    browsr github://juftin:browsr-private@main
    ```

    #### Browse a GitHub Repository Subdirectory

    ```shell
    browsr github://juftin:browsr@main/tests
    ```

    #### Browse a GitHub URL

    ```shell
    browsr https://github.com/juftin/browsr
    ```

    #### Browse a Filesystem over SSH

    ```
    browsr ssh://user@host:22
    ```

    #### Browse a SFTP Server

    ```
    browsr sftp://user@host:22/path/to/directory
    ```

    ## Key Bindings
    - **`Q`** - Quit the application
    - **`F`** - Toggle the file tree sidebar
    - **`T`** - Toggle the rich theme for code formatting
    - **`N`** - Toggle line numbers for code formatting
    - **`D`** - Toggle dark mode for the application
    - **`X`** - Download the file from cloud storage
    """
    config = TextualAppContext(file_path=path, debug=debug, max_file_size=max_file_size)
    app = Browsr(config_object=config)
    app.run()


if __name__ == "__main__":
    browsr()
