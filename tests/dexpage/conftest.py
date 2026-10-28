import pytest

from tools.dexpage.paths import Paths


@pytest.fixture(scope="session")
def paths():
    return Paths.default()
