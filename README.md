# browsr

<div align="center" href="https://github.com/juftin/browsr">
    <a href="https://github.com/juftin/browsr">
      <img src=https://raw.githubusercontent.com/juftin/browsr/main/docs/_static/browsr.png
        width="400" alt="browsr">
    </a>
</div>

[![browsr Version](https://img.shields.io/pypi/v/browsr?color=blue&label=browsr)](https://github.com/juftin/browsr)
[![PyPI](https://img.shields.io/pypi/pyversions/browsr)](https://pypi.python.org/pypi/browsr/)
[![Testing Status](https://github.com/juftin/browsr/actions/workflows/tests.yaml/badge.svg?branch=main)](https://github.com/juftin/browsr/actions/workflows/tests.yaml?query=branch%3Amain)
[![GitHub License](https://img.shields.io/github/license/juftin/browsr?color=blue&label=License)](https://github.com/juftin/browsr/blob/main/LICENSE)

**`browsr`** 🗂️ is a pleasant **file explorer** in your terminal. It's a command line **TUI**
(text-based user interface) application that empowers you to browse the contents of local
and remote filesystems with your keyboard or mouse.

You can quickly navigate through directories and peek at files whether they're hosted **locally**,
in **GitHub**, over **SSH**, in **AWS S3**, **Google Cloud Storage**, or **Azure Blob Storage**. View code files
with syntax highlighting, format JSON files, render images, convert data files to navigable
datatables, and more.

![](https://raw.githubusercontent.com/juftin/browsr/main/docs/_static/screenshot_utils.png)

<details>
<summary>Screenshots</summary>

<body>
<div>
    <img src="https://raw.githubusercontent.com/juftin/browsr/main/docs/_static/screenshot_datatable.png" alt="Image 2">
    <img src="https://raw.githubusercontent.com/juftin/browsr/main/docs/_static/screenshot_mona_lisa.png" alt="Image 3">
    <img src="https://raw.githubusercontent.com/juftin/browsr/main/docs/_static/screenshot_markdown.png" alt="Image 4">
</div>
</body>

</details>

<details>
<summary>Screen Recording</summary>

https://user-images.githubusercontent.com/49741340/238535232-459847af-a15c-4d9b-91ac-fab9958bc74f.mp4

</details>

## Installation

It's recommended to use [pipx](https://pypa.github.io/pipx/) instead of pip. `pipx` installs the package in
an isolated environment and makes it available everywhere. If you'd like to use `pip` instead, just replace `pipx`
with `pip` in the below command.

```shell
pipx install browsr
```

### Extra Installation

If you're looking to use **`browsr`** on remote file systems, like GitHub or AWS S3, you'll need to install the `remote` extra.
If you'd like to browse parquet files, you'll need to install the `parquet` extra. Or, even simpler,
you can install the `all` extra to get all the extras.

```shell
pipx install "browsr[all]"
```

## Usage

Simply give **`browsr`** a path to a local or remote file / directory.
[Check out the Documentation](https://juftin.com/browsr/) for more information
about the file systems supported.

### Local

```shell
browsr ~/Downloads/
```

### GitHub

```
browsr github://juftin:browsr
```

```
export GITHUB_TOKEN="ghp_1234567890"
browsr github://juftin:browsr-private@main
```

### Cloud

```shell
browsr s3://my-bucket
```

\*\* _Currently AWS S3, Google Cloud Storage, and Azure Blob Storage / Data Lake are supported._

### SSH / SFTP

```shell
browsr ssh://username@example.com:22
```

## License

**`browsr`** is distributed under the terms of the [MIT license](LICENSE).
