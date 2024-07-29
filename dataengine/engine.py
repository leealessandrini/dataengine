"""
This is the main module for Data Engine.
"""
import datetime
import logging
from . import assets, dataset, query


def generate_query_log_message(
    query_name: str, 
    query_object: query.Query, 
    query: str, 
    dependencies: dict
) -> str:
    """
    Generate a neatly formatted log message for a query.

    Args:
        query_name (str): The name of the query.
        query_object (query.Query): The query object instance.
        query (str): The query string.
        dependencies (dict): A dictionary mapping dependencies.

    Returns:
        A formatted log message.
    """
    intro = [f"Beginning execution of {query_name}\n"]
    dependency_list = [
        f"Dependencies:\n" +
        "\n".join(
            f"    {key}:\n        {value}"
            for key, value in dependencies.items())]
    intermittent_tables = query_object.intermittent_tables
    if intermittent_tables:
        it_list = [
            "Intermittent Tables:\n" +
            "\n".join(
                f"    {itable['table_name']}:\n" +
                "\n".join(f"        {line}" for line in itable["sql"].splitlines())
                for itable in intermittent_tables)]
    else:
        it_list = []
    query_list = [
        "Query:\n" +
        "\n".join(f"    {line}" for line in query.splitlines())]

    return "\n".join(intro + dependency_list + it_list + query_list) + "\n"


class Engine:
    """
    This class will function as the primary class for Data Engine.
    """
    def __init__(
            self,
            asset_config_path_list: list
    ):
        # Load assets
        self.assets = assets.load_assets(
            assets.load_asset_config_files(asset_config_path_list))

    def load_dataset(
            self, spark, base_dataset, dt=datetime.datetime.utcnow(),
            hour="*", bucket=None, format_args={}, time_delta={},
            timestamp_conversion=[], dt_delta={}, exclude_hours=[],
            file_path=None, rename={}, check_path=True, **kwargs):
        """
        This method will load a Dataset object from the available base
        datasets in this engine.
        """
        dataset_obj = None
        load_success = False
        if base_dataset in self.assets["base_datasets"]:
            # TODO: Add file path override here
            try:
                dataset_obj = dataset.Dataset.from_base_dataset(
                    self.assets["base_datasets"][base_dataset], spark=spark,
                    dt=dt, hour=str(hour), bucket=bucket,
                    format_args=format_args, time_delta=time_delta,
                    dt_delta=dt_delta, rename=rename,
                    exclude_hours=exclude_hours, check_path=check_path,
                    timestamp_conversion=timestamp_conversion)
                load_success = True
            except Exception as e:
                logging.error(f"Error loading dataset {base_dataset}:\n{e}\n")
        else:
            logging.error(f"Invalid base dataset provided: {base_dataset}\n")

        return dataset_obj, load_success
