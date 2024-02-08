"""
Test the actual browsr app
"""

import pytest

from browsr.base import TextualAppContext
from browsr.browsr import Browsr


def test_bad_path() -> None:
    """
    Test a bad path
    """
    with pytest.raises(FileNotFoundError):
        _ = Browsr(
            config_object=TextualAppContext(file_path="bad_file_path.csv", debug=True)
        )
