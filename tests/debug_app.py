"""
App Debugging
"""

import pytest

from browsr.base import TextualAppContext
from browsr.browsr import Browsr


@pytest.mark.asyncio
async def test_debug_app() -> None:
    """
    Test the actual browsr app
    """
    config = TextualAppContext(file_path=".", debug=True)
    app = Browsr(config_object=config)
    async with app.run_test() as pilot:
        _ = pilot.app
