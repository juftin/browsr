<div align="center">
  <a href="https://github.com/juftin/browsr">
    <img src="https://raw.githubusercontent.com/juftin/browsr/main/docs/_static/browsr.png" width=400 alt="browsr" />
  </a>
</div>

<p align="center">
a pleasant <strong>file explorer</strong> in your terminal supporting <strong>all filesystems</strong>
</p>

<p align="center">
  <a href="https://github.com/juftin/browsr"><img src="https://img.shields.io/pypi/v/browsr?color=blue&label=%F0%9F%97%82%EF%B8%8F%20browsr" alt="PyPI"></a>
  <a href="https://pypi.python.org/pypi/browsr/"><img src="https://img.shields.io/pypi/pyversions/browsr" alt="PyPI - Python Version"></a>
  <a href="https://github.com/juftin/browsr/blob/main/LICENSE"><img src="https://img.shields.io/github/license/juftin/browsr?color=blue&label=License" alt="GitHub License"></a>
  <a href="https://juftin.github.io/browsr/"><img src="https://img.shields.io/static/v1?message=docs&color=526CFE&logo=Material+for+MkDocs&logoColor=FFFFFF&label=" alt="docs"></a>
  <a href="https://github.com/juftin/browsr/actions/workflows/tests.yaml?query=branch%3Amain"><img src="https://github.com/juftin/browsr/actions/workflows/tests.yaml/badge.svg?branch=main" alt="Testing Status"></a>
  <a href="https://github.com/pypa/hatch"><img src="https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg" alt="Hatch project"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://github.com/pre-commit/pre-commit"><img src="https://img.shields.io/badge/pre--commit-enabled-lightgreen?logo=pre-commit" alt="pre-commit"></a>
  <a href="https://github.com/semantic-release/semantic-release"><img src="https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg" alt="semantic-release"></a>
  <a href="https://gitmoji.dev"><img src="https://img.shields.io/badge/gitmoji-%20😜%20😍-FFDD67.svg" alt="Gitmoji"></a>
</p>

**`browsr`** 🗂️ is a pleasant **file explorer** in your terminal. It's a command line **TUI**
(text-based user interface) application that empowers you to browse the contents of local
and remote filesystems with your keyboard or mouse.

You can quickly navigate through directories and peek at files whether they're hosted **locally**,
in **GitHub**, over **SSH**, in **AWS S3**, **Google Cloud Storage**, or **Azure Blob Storage**. View code files
with syntax highlighting, format JSON files, render images, convert data files to navigable
datatables, and more.

<style>
  .grid-item {
    transition: all 0.5s ease;
  }

  .grid-item:hover {
    transform: scale(1.2);
  }

  .expanded {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
  }

  .expanded img {
    max-width: 80%;
    max-height: 80%;
    object-fit: contain;
  }
</style>

<body>
  <div class="grid" style="display: grid; grid-template-columns: repeat(2, 1fr); grid-gap: 10px;">
    <div class="grid-item">
      <img src="_static/screenshot_utils.png" alt="Image 1">
    </div>
    <div class="grid-item">
      <img src="_static/screenshot_datatable.png" alt="Image 2">
    </div>
    <div class="grid-item">
      <img src="_static/screenshot_mona_lisa.png" alt="Image 3">
    </div>
    <div class="grid-item">
      <img src="_static/screenshot_markdown.png" alt="Image 4">
    </div>
  </div>

  <div class="expanded" style="display: none;">
    <img src="">
  </div>

  <script>
    var expanded = document.querySelector('.expanded');
    expanded.onclick = function() {
      this.style.display = 'none';
    };
  </script>
</body>

<details>
<summary>Screen Recording</summary>
<video controls>
  <source src="https://user-images.githubusercontent.com/49741340/238535232-459847af-a15c-4d9b-91ac-fab9958bc74f.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>
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
If you'd like to browse parquet / feather files, you'll need to install the `data` extra. Or, even simpler,
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

** _Currently AWS S3, Google Cloud Storage, and Azure Blob Storage are supported._

### SSH / SFTP

```shell
browsr ssh://username@example.com:22
```
