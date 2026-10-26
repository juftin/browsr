#!/usr/bin/env bash
set -euo pipefail

tool_test_dir=$(mktemp -d)
trap 'rm -rf "$tool_test_dir"' EXIT
export UV_TOOL_DIR="$tool_test_dir/tools"
export UV_TOOL_BIN_DIR="$tool_test_dir/bin"
export PATH="$UV_TOOL_BIN_DIR:$PATH"

# Build a previous version with the same dependencies to exercise an actual
# upgrade. Both installations resolve wheel metadata without consulting uv.lock.
mkdir -p "$tool_test_dir/previous" "$tool_test_dir/index/browsr"
cp -R browsr README.md LICENSE "$tool_test_dir/previous/"
sed 's/^version = .*/version = "0.0.0"/' pyproject.toml \
    > "$tool_test_dir/previous/pyproject.toml"
uv build "$tool_test_dir/previous" --wheel --out-dir "$tool_test_dir/previous-dist"
uv build --wheel --out-dir "$tool_test_dir/dist"
wheels=("$tool_test_dir"/dist/*.whl)
wheel_name=$(basename "${wheels[0]}")
version=${wheel_name#browsr-}
version=${version%%-*}

for extra in "" "[remote]" "[all]"; do
    rm -f "$tool_test_dir/index/browsr/$wheel_name"
    cp "$tool_test_dir"/previous-dist/*.whl "$tool_test_dir/index/browsr/"
    printf '<a href="browsr-0.0.0-py3-none-any.whl">browsr</a>\n' \
        > "$tool_test_dir/index/browsr/index.html"
    uv tool install --index "$tool_test_dir/index" "browsr$extra"
    "$UV_TOOL_BIN_DIR/browsr" --help

    cp "${wheels[0]}" "$tool_test_dir/index/browsr/"
    printf '<a href="%s">%s</a>\n' "$wheel_name" "$wheel_name" \
        >> "$tool_test_dir/index/browsr/index.html"
    uv tool upgrade --all
    "$UV_TOOL_BIN_DIR/browsr" --help
    uv pip check --python "$UV_TOOL_DIR/browsr/bin/python"
    "$UV_TOOL_DIR/browsr/bin/python" - "$version" <<'PY'
import sys
from importlib.metadata import version

assert version("browsr") == sys.argv[1]
PY

    if [ -n "$extra" ]; then
        "$UV_TOOL_DIR/browsr/bin/python" - <<'PY'
from fsspec import get_filesystem_class

for protocol in ("s3", "gcs", "az", "sftp", "github"):
    get_filesystem_class(protocol)
PY
    fi

    uv tool uninstall browsr
done
