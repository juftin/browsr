"""
Pytest Fixtures Shared Across all Unit Tests
"""

import pytest
from click.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    """
    Return a CliRunner object
    """
    return CliRunner()
