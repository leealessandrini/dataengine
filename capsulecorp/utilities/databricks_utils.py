"""
This module contains all DataBricks interactive functionality.
"""
import os
import base64
import json
import requests
from databricks_cli.sdk.api_client import ApiClient
from databricks_cli.sdk.service import WorkspaceService
from databricks_cli.dbfs.cli import DbfsApi


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
        os.path.join(host, 'api/2.0/jobs/run-now'),
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


def delete_job_run(host, token, run_id):
    """
        This method will delete a specified run of a job configuration.

        Args:
            host (str): URL of DataBricks workspace
            token (str): DataBricks API token
            run_id (int): respective run id

        Returns:
            request response
    """
    return requests.post(
        os.path.join(host, "api/2.0/jobs/runs/delete"),
        headers={"Authorization": f"Bearer {token}"},
        json={"run_id": run_id})


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
            host (str): URL of DataBricks workspace
            token (str): DataBricks API token
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
            host (str): URL of DataBricks workspace
            token (str): DataBricks API token
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


def does_dir_exist(host, token, user, notebook_path):
    """
        This method will determine whether the directory in a notebook path
        exists.

        Args:
            host (str): URL of DataBricks workspace
            token (str): DataBricks API token
            user (str): databricks user path
            notebook_path (str): location of notebook

        Returns:
            boolean
    """
    # Parse the directory name from the full notebook path
    dir_name = os.path.dirname(notebook_path.split(user)[1])
    # Initialize DataBricks API Client and Workspace API
    databricks_client = ApiClient(host=host, token=token, verify=True)
    workspace_service = WorkspaceService(databricks_client)
    # Grab the workspace objects for the provided user
    workspace_objects = workspace_service.list(user)
    # Return a boolean for whether the directory exists iin the workspace
    return any([
        user + dir_name == i["path"]
        for i in workspace_objects["objects"]
        if i["object_type"] == "DIRECTORY"])


def make_dir(host, token, user, notebook_path):
    """
        This method will make a databricks directory given user and notebook
        path information.

        Args:
            host (str): URL of DataBricks workspace
            token (str): DataBricks API token
            user (str): databricks user path
            notebook_path (str): location of notebook

        Returns:

    """
    # Parse the directory name from the full notebook path
    dir_name = os.path.dirname(notebook_path.split(user)[1])
    # Initialize DataBricks API Client and Workspace API
    databricks_client = ApiClient(host=host, token=token, verify=True)
    workspace_service = WorkspaceService(databricks_client)
    # Make the directory
    return workspace_service.mkdirs(user + dir_name)


def put_file(host, token, src_path, dbfs_path):
    """
        Uploads a file from the local filesystem to Databricks File System.

        Args:
            host (str): URL of DataBricks workspace
            token (str): DataBricks API token
            src_path (str): The path of the file on the local filesystem.
            dbfs_path (str): DBFS path where the file will be uploaded.

        Returns:
            TODO: Add success boolean
    """
    # Connect to databricks
    databricks_client = ApiClient(host=host, token=token, verify=True)
    dbfs_api = DbfsApi(databricks_client)
    # Read file and upload to dbfs
    handle = dbfs_api.client.create(dbfs_path, True)['handle']
    with open(src_path, 'rb') as local_file:
        while True:
            contents = local_file.read(2 ** 20)
            if len(contents) == 0:
                break
            # add_block should not take a bytes object.
            dbfs_api.client.add_block(
                handle, base64.b64encode(contents).decode())
        dbfs_api.client.close(handle)

    return
