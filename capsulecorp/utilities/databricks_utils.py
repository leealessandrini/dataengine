"""
This module contains all DataBricks interactive functionality.
"""
import os
import base64
import json
import requests
from databricks_cli.sdk.api_client import ApiClient
from databricks_cli.sdk.service import WorkspaceService


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
        os.path.join(host, 'api/2.0/jobs/runs/get'), json={"run_id": run_id},
        headers={"Authorization": f"Bearer {token}"})


def get_job_info(host, token, job_id):
    """
        Get DataBricks job information given a job id.

        Args:
            host (str): URL of DataBricks workspace
            token (str): DataBricks API token
            run_id (int): respective run id

        Returns:
            request response
    """
    return requests.get(
        os.path.join(host, 'api/2.0/jobs/get'), json={"job_id": job_id},
        headers={"Authorization": f"Bearer {token}"})


def get_task_params(host, token, job_id):
    """
        This method will get the existing task parameters given a job id.

        Args:
            host (str): URL of DataBricks workspace
            token (str): DataBricks API token
            job_id (int): respective job id

        Returns:
            task parameter list and success boolean
    """
    # Initialize values
    success = False
    task_params = []
    # Get all job information
    response = get_job_info(host, token, job_id)
    # If a successful response has been retrieved pull the task parameters
    if response.status_code == 200:
        success = True
        # Parse response
        content = response.json()
        # If there are multiple tasks build the list
        if "tasks" in content["settings"]:
            task_params = [
                {
                    key: value for key, value in i.items()
                    if key in ["task_key", "notebook_task"]
                }
                for i in content["settings"]["tasks"]]
        # Otherwise, use notebook_task field and fill task key with empty str
        else:
            task_params = [{
                "task_key": "",
                "notebook_task": content["settings"]["notebook_task"]}]

    return task_params, success


def export_notebook(host, token, notebook_path):
    """
        This method will export a DataBricks notebook to a python source file
        locally stored.

        Arguments:
            notebook_path (str): local DataBricks path to notebook

        Returns:
            source code string
    """
    # Initialize DataBricks API Client and Workspace API
    databricks_client = ApiClient(host=host, token=token, verify=True)
    workspace_service = WorkspaceService(databricks_client)
    # Export Workspace
    output = workspace_service.export_workspace(notebook_path, 'SOURCE')
    # Return decoded source code as a string
    return base64.b64decode(output["content"]).decode()


def import_notebook(host, token, source_code, notebook_path):
    """
        Import source code into DataBricks given a location.

        TODO: Add success boolean as return vaue

        Arguments:
            source_code (str): string of python source code
            notebook_path (str): location of notebook

        Returns:
            None
    """
    # Initialize DataBricks API Client and Workspace API
    databricks_client = ApiClient(host=host, token=token, verify=True)
    workspace_service = WorkspaceService(databricks_client)
    # Import the source code as the new DataBricks notebook
    workspace_service.import_workspace(
        notebook_path, "SOURCE", "PYTHON", source_code, True)

    return
