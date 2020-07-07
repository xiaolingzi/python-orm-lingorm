import os
from lingorm.drivers.database_config import DatabaseConfig

def test_get_config_by_database():
    config = DatabaseConfig.get_config_by_database("test")
    assert config is not None
    assert "database" in config
    assert config["database"] == "test"

def test_get_config_by_key():
    config = DatabaseConfig.get_config_by_key("test")
    assert config is not None
    assert "database" in config
    assert config["database"] == "test"
