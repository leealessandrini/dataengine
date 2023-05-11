"""
This module will house all automated slack app logic.
"""
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def post_pandas_dataframe(channel, token, pandas_df, message):
    """
        Posts a pandas DataFrame to a Slack channel.

        Args:
            channel (str): The ID or name of the Slack channel to post to.
            token (str): The Slack API token to use for authentication.
            pandas_df (pd.DataFrame): The DataFrame to post to the channel.
            message (str): A message to include with the DataFrame.

        Returns:
            None.
    """
    post_text = (
        # Place the message above the DataFrame
        message + "\n\n" +
        # Convert the DataFrame to a string surrounded by backticks
        "``` \n" + pandas_df.to_markdown(index=False) + "\n ```")
    # Initialize a Slack WebClient instance
    client = WebClient(token=token)
    # Post the message to Slack
    try:
        response = client.chat_postMessage(channel=channel, text=post_text)
        print("Message posted to Slack")
    except SlackApiError as e:
        print("Error posting message to Slack: {}".format(e))
