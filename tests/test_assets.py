import os
import pytest
from unittest.mock import patch
from dataengine import assets


# Mock environment variables
@pytest.fixture(scope='function')
def mock_env_vars():
    env_vars = {
        'DB1_HOST': 'localhost1',
        'DB1_PORT': '5431',
        'DB1_USER': 'user1',
        'DB1_PASSWORD': 'password1',
        'DB2_HOST': 'localhost2',
        'DB2_PORT': '5432',
        'DB2_USER': 'user2',
        'DB2_PASSWORD': 'password2',
    }
    for key, value in env_vars.items():
        os.environ[key] = value
    yield
    for key in env_vars.keys():
        del os.environ[key]

def test_load_asset_config_files(mock_env_vars):
    yaml_paths = [
        './tests/sample_configs/sample_config1.yaml',
        './tests/sample_configs/sample_config2.yaml']
    db_map = assets.load_asset_config_files(yaml_paths)
    assert all(i in db_map for i in ["db1", "db2"])

def test_load_assets(mock_env_vars):
    yaml_paths = [
        './tests/sample_configs/sample_config1.yaml',
        './tests/sample_configs/sample_config2.yaml']
    db_map = assets.load_assets(
        assets.load_asset_config_files(yaml_paths))
    # Validate that the databases are loaded correctly
    assert 'db1' in db_map["databases"]
    assert 'db2' in db_map["databases"]
    # Validate that the environment variables are applied
    assert db_map["databases"]['db1'].host == 'localhost1'
    assert db_map["databases"]['db1'].port == 5431
    assert db_map["databases"]['db2'].host == 'localhost2'
    assert db_map["databases"]['db2'].port == 5432
