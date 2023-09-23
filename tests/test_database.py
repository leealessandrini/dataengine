import os
import pytest
from unittest.mock import patch
from capsulecorp import database


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


def test_load_databases(mock_env_vars):
    yaml_paths = [
        './tests/sample_configs/sample_config1.yaml',
        './tests/sample_configs/sample_config2.yaml']
    db_map = database.load_databases(yaml_paths)
    # Validate that the databases are loaded correctly
    assert 'db1' in db_map
    assert 'db2' in db_map
    print(db_map["db1"])
    # Validate that the environment variables are applied
    assert db_map['db1'].host == 'localhost1'
    assert db_map['db1'].port == 5431
    assert db_map['db2'].host == 'localhost2'
    assert db_map['db2'].port == 5432
