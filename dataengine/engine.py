"""
This is the main module for Data Engine.
"""
from . import assets


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
