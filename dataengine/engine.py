"""
This is the main module for Data Engine.
"""
import datetime
import logging
from . import assets, dataset


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
