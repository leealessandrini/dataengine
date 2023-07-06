"""
This module contains all DataBricks interactive functionality.
"""
import os
import base64
import json
import requests


def update_global_init_script(host, token, script_text, script_id, name):
    """
        This method will update a DataBricks global init script.

        Args:
            host (str): URL of DataBricks workspace
            token (str): DataBricks API token
            script_text (str): init script plain text
            script_id (str): global init script ID
            name (str): name of init script

        Returns:
            request response
    """
    return requests.request(
        "PATCH",
        os.path.join(host, "api/2.0/global-init-scripts", script_id),
        data=json.dumps({
            "name": name, "script": base64.b64encode(
                bytes(script_text, "utf-8")).decode("ascii")}),
        headers={"Authorization": f"Bearer {token}"})


def update_job(host, token, job_id, **kwargs):
    """
        This method will run a DataBricks job given the job id.

        Args:
            host (str): URL of DataBricks workspace
            token (str): DataBricks API token
            job_id (int): respective job id

        Returns:
            request response
    """
    return requests.post(
        os.path.join(host, "api/2.0/jobs/update"),
        headers={"Authorization": f"Bearer {token}"},
        json={"job_id": job_id, **kwargs})


def run_job(host, token, job_id, **kwargs):
    """
        This method will run a DataBricks job given the job id.

        Args:
            host (str): URL of DataBricks workspace
            token (str): DataBricks API token
            job_id (int): respective job id

        Returns:
            request response
    """
    return requests.post(
        os.path.join(databricks_host, 'api/2.0/jobs/run-now'),
        headers={"Authorization": f"Bearer {token}"},
        json={"job_id": job_id, **kwargs})


def get_run_status(host, token, run_id):
    """
        Get DataBricks run status information given a run id.

        Args:
            host (str): URL of DataBricks workspace
            token (str): DataBricks API token
            run_id (int): respective run id

        Returns:
            request response
    """
    return requests.get(
        os.path.join(host, 'api/2.0/jobs/runs/get'),
        headers={"Authorization": f"Bearer {token}"}, json={"run_id": run_id})
