import pytest
from typing import Generator
from hometray.config import Config
from pathlib import Path


@pytest.fixture(scope="function", name="config", autouse=True)
def config(tmp_path: Path) -> Config:
    config_path = tmp_path / "test.ini"
    config_path.write_text("""
    [TEST]
    Token = test-token
    ApiUrl = http://test.com
    Entities = entity1,entity2
    Domains = domain1,domain2
    DomainEntitiesIgnore = ignore1,ignore2
    UpdateInterval = 5
    
    [COLORS]
    UseRGBValue = True
    On = 1,2,3
    Off = 225,225,225
    """)
    c = Config(str(config_path), "TEST", "COLORS")
    return c


def test_read(config: Config) -> None:
    assert config.token == "test-token"
    assert config.api_url == "http://test.com"
    assert config.entities == ["entity1", "entity2"]
    assert config.domains == ["domain1", "domain2"]
    assert config.domain_entities_ignore == ["ignore1", "ignore2"]
    assert config.update_interval == 5
    assert config.color_use_rgb_value
    assert config.color_on == [1, 2, 3]
    assert config.color_off == [225, 225, 225]
    assert config.color_unknown == [100, 100, 100]


def test_write(config: Config) -> None:
    config.api_url = "http://test2.com"
    assert config.api_url == "http://test2.com"

    config.entities = ["entity3", "entity4"]
    assert config.entities == ["entity3", "entity4"]
