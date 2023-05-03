# browsr

<div align="center">
<a href="https://github.com/juftin/browsr">
  <img src=https://i.imgur.com/QiAXcEm.png
    width="400" alt="browsr">
</a>
</div>

[![browsr Version](https://img.shields.io/pypi/v/browsr?color=blue&label=browsr)](https://github.com/juftin/browsr)
[![PyPI](https://img.shields.io/pypi/pyversions/browsr)](https://pypi.python.org/pypi/browsr/)
[![Testing Status](https://github.com/juftin/browsr/actions/workflows/tests.yaml/badge.svg?branch=main)](https://github.com/juftin/browsr/actions/workflows/tests.yaml?query=branch%3Amain)
[![GitHub License](https://img.shields.io/github/license/juftin/browsr?color=blue&label=License)](https://github.com/juftin/browsr/blob/main/LICENSE)

**`browsr`** is a TUI (text-based user interface) file browser for your terminal.
It's a simple way to browse your files and take a peek at their contents. Plus it
works on local and remote file systems.

---

<body>
<div style="display: grid; grid-template-columns: repeat(2, 1fr); grid-gap: 10px;">
  <img src="https://i.imgur.com/6apkI2Q.png" alt="Image 1">
  <img src="https://i.imgur.com/y7ZLRTX.png" alt="Image 2">
  <img src="https://i.imgur.com/oRBJ0vj.png" alt="Image 3">
  <img src="https://i.imgur.com/HWSjWCY.png" alt="Image 4">
</div>
</body>

## Installation

The below command recommends [pipx](https://pypa.github.io/pipx/) instead of pip. `pipx` installs the package in
an isolated environment and makes it easy to uninstall. If you'd like to use `pip` instead, just replace `pipx`
with `pip` in the below command.

```console
pipx install browsr
```

## Extra Installation

If you're looking to use `browsr` on remote file systems, like AWS S3, you'll need to install the `remote` extra.
If you'd like to browse parquet files, you'll need to install the `parquet` extra. Or, even simpler,
you can install the `all` extra to get all the extras.

```console
pipx install "browsr[all]"
```

## Usage

```console
browsr ~/Downloads/
```

Simply give `browsr` a path to a file/directory and it will open a browser window
with a file browser. You can also give it a URL to a remote file system, like AWS S3.

```console
browsr s3://my-bucket/my-file.parquet
```

## License

`browsr` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
