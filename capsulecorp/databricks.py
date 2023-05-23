"""
This module contains all DataBricks interactive functionality.
"""
import os
import base64
import json
import requests


def update_global_init_script(script_text, workspace, token, script_id, name):
    """
        This method will update a DataBricks global init script.

        Args:
            script_text (str): init script plain text
            workspace (str): URL of DataBricks workspace
            token (str): DataBricks API token
            script_id (str): global init script ID
            name (str): name of init script

        Returns:
            success boolean
    """
    response = requests.request(
        "PATCH",
        os.path.join(workspace, "api/2.0/global-init-scripts", script_id),
        data=json.dumps({
            "name": name, "script": base64.b64encode(
                bytes(script_text, "utf-8")).decode("ascii")}),
        headers={"Authorization": f"Bearer {token}"})

    return response.status_code == 200
