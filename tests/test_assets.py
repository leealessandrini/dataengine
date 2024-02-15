import os
import pytest
from unittest.mock import patch
from dataengine import assets

DIRNAME = os.path.dirname(os.path.realpath(__file__))

# Mock BaseDataset Inputs
@pytest.fixture
def valid_input_data():
    return {
        "asset_name": "MyAsset",
        "dirname": DIRNAME,
        "file_path": "data/file.csv",
        "file_format": "csv",
        "separator": ",",
        "location": "local",
        "header": True,
        "schema": {"name": "string", "age": "int"}}


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


def test_deserialize_valid_input(valid_input_data):
    schema = assets.BaseDatasetSchema()
    result = schema.load(valid_input_data)
    assert isinstance(result, assets.BaseDataset)
    assert result.asset_name == "MyAsset"
    assert result.file_path_list == [os.path.join(DIRNAME, "data/file.csv")]


def test_deserialize_invalid_file_format(valid_input_data):
    invalid_data = valid_input_data.copy()
    invalid_data['file_format'] = 'unsupported_format'
    schema = assets.BaseDatasetSchema()
    with pytest.raises(assets.ValidationError) as excinfo:
        schema.load(invalid_data)
    assert "Invalid file_format" in str(excinfo.value)

def test_base_dataset_instantiation_via_schema(valid_input_data):
    # Instantiate your schema
    schema = assets.BaseDatasetSchema()

    # Deserialize the input data, which should invoke post_load to create a BaseDataset instance
    result = schema.load(valid_input_data)

    # Assertions to verify the BaseDataset instance is correctly instantiated
    assert isinstance(result, assets.BaseDataset), "Resulting object is not an instance of BaseDataset"
    assert result.asset_name == valid_input_data["asset_name"], "Asset name was not set correctly"
    assert result.file_path_list == [
        os.path.join(DIRNAME, valid_input_data["file_path"])
    ], "File paths were not set correctly"
    assert result.file_format == valid_input_data["file_format"], "File format was not set correctly"
    assert result.separator == valid_input_data["separator"], "Separator was not set correctly"
    assert result.location == valid_input_data["location"], "Location was not set correctly"
    assert result.header == valid_input_data["header"], "Header flag was not set correctly"
    assert result.schema == valid_input_data["schema"], "Schema was not set correctly"