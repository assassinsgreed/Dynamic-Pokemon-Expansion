import pytest

from tools.dexpage.paths import Paths


@pytest.fixture(scope="session")
def paths():
    return Paths.default()


@pytest.fixture(scope="session")
def source_data(paths):
    from tools.dexpage.roster import load_source_data
    return load_source_data(paths)


@pytest.fixture(scope="session")
def roster(source_data):
    from tools.dexpage.roster import build_roster
    return build_roster(source_data)


@pytest.fixture(scope="session")
def evo_links(source_data, roster):
    from tools.dexpage.roster import evolution_links
    return evolution_links(source_data, {e.key for e in roster})
