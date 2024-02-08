"""
browsr command line interface
"""

import os
from typing import Optional, Tuple

import click
import rich_click

from browsr.__about__ import __application__, __version__
from browsr.base import (
    TextualAppContext,
)
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
    "-l",
    "--max-lines",
    default=1000,
    show_default=True,
    type=int,
    help="Maximum number of lines to display in the code browser",
    envvar="BROWSR_MAX_LINES",
    show_envvar=True,
)
@click.option(
    "-m",
    "--max-file-size",
    default=20,
    show_default=True,
    type=int,
    help="Maximum file size in MB for the application to open",
    envvar="BROWSR_MAX_FILE_SIZE",
    show_envvar=True,
)
@click.version_option(version=__version__, prog_name=__application__)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable extra debugging output",
    type=click.BOOL,
    envvar="BROWSR_DEBUG",
    show_envvar=True,
)
@click.option(
    "-k",
    "--kwargs",
    multiple=True,
    help="Key=Value pairs to pass to the filesystem",
    envvar="BROWSR_KWARGS",
    show_envvar=True,
)
def browsr(
    path: Optional[str],
    debug: bool,
    max_lines: int,
    max_file_size: int,
    kwargs: Tuple[str, ...],
) -> None:
    """
    browsr 🗂️  a pleasant file explorer in your terminal

    Navigate through directories and peek at files whether they're hosted locally,
    over SSH, in GitHub, AWS S3, Google Cloud Storage, or Azure Blob Storage.
    View code files with syntax highlighting, format JSON files, render images,
    convert data files to navigable datatables, and more.

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

    #### Pass Extra Arguments to Cloud Storage

    Some cloud storage providers require extra arguments to be passed to the
    filesystem. For example, to browse an anonymous S3 bucket, you need to pass
    the `anon=True` argument to the filesystem. This can be done with the `-k/--kwargs`
    argument.

    ```shell
    browsr s3://anonymous-bucket -k anon=True
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
    - **`.`** - Parent Directory - go up one directory
    - **`R`** - Reload the current directory
    - **`C`** - Copy the current file or directory path to the clipboard
    - **`X`** - Download the file from cloud storage
    """
    extra_kwargs = {}
    if kwargs:
        for kwarg in kwargs:
            try:
                key, value = kwarg.split("=")
                extra_kwargs[key] = value
            except ValueError as ve:
                raise click.BadParameter(
                    message=(
                        f"Invalid Key/Value pair: `{kwarg}` "
                        "- must be in the format Key=Value"
                    ),
                    param_hint="kwargs",
                ) from ve
    file_path = path or os.getcwd()
    config = TextualAppContext(
        file_path=file_path,
        debug=debug,
        max_file_size=max_file_size,
        max_lines=max_lines,
        kwargs=extra_kwargs,
    )
    app = Browsr(config_object=config)
    app.run()


if __name__ == "__main__":
    browsr()
