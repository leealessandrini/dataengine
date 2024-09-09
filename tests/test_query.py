import os
import pytest
from unittest.mock import patch
from dataengine import query

DIRNAME = os.path.dirname(os.path.realpath(__file__))

# Mock BaseDataset Inputs
@pytest.fixture
def valid_base_query_data():
    return {
        "asset_name": "TestQuery",
        "description": "This is a test query.",
        "dirname": DIRNAME,
        "sql_info": {"filename": os.path.join(DIRNAME, "sample_configs/sql/test_query.sql")},
        "output": "result.csv",
        "file_format": "csv",
        "separator": ",",
        "use_pandas": True,
        "header": True,
        "dependencies": [
            {
                "table_name": "test_table",
                "base_dataset": "test_base_dataset"
            }
        ],
    }

def test_deserialize_base_query(valid_base_query_data):
    schema = query.BaseQuerySchema()
    result = schema.load(valid_base_query_data)
    assert isinstance(result, query.BaseQuery)
    assert result.asset_name == "TestQuery"
    assert result.output == "result.csv"
    assert result.description == "This is a test query."
