from pathlib import Path

import pandas as pd
import pytest
from textual.app import App, ComposeResult
from textual_universal_directorytree import UPath

from browsr.widgets.windows import DataTableWindow


@pytest.mark.asyncio
@pytest.mark.parametrize("suffix", ["csv", "csv.gz", "parquet", "feather", "fea"])
async def test_data_file_preview(tmp_path: Path, suffix: str) -> None:
    frame = pd.DataFrame(
        {
            "name": ["café", None, "last"],
            "score": [1.5, float("nan"), 3.5],
            "active": [True, False, True],
        }
    )
    path = tmp_path / f"example.{suffix}"
    if suffix.startswith("csv"):
        frame.to_csv(path, index=False)
    elif suffix == "parquet":
        frame.to_parquet(path, index=False)
    else:
        frame.to_feather(path)

    window = DataTableWindow()

    class Preview(App[None]):
        def compose(self) -> ComposeResult:
            yield window

    async with Preview().run_test():
        window.refresh_from_file(UPath(path), max_lines=2)

        assert [column.label.plain for column in window.columns.values()] == [
            "",
            "name",
            "score",
            "active",
        ]
        assert window.row_count == 2
        assert window.get_row_at(0) == ["0", "café", "1.5", "True"]
        assert window.get_row_at(1) == ["1", "", "", "False"]
