import os
import logging
from typing import Union
from dotenv import load_dotenv
from slack import WebClient
from slack.errors import SlackApiError

load_dotenv()


class SlackBotHandler(logging.Handler):
    """
    Logging Handler that operates via the SlackAPI to send messages to one or multiple specified Slack channels.
    """
    def __init__(self, channels: Union[str, list, tuple]):
        logging.Handler.__init__(self)
        self.level = logging.WARNING

        slack_token = os.environ.get("SLACK_BOT_TOKEN")
        self._slack_client = WebClient(token=slack_token)

        self._channels: list = self._parse_channels(channels)

    @staticmethod
    def _parse_channels(channels: Union[str, list, tuple]) -> list:
        """
        Parses channels (string or collection of strings) to a list of strings.

        Args:
            channels: String of a single channel or collection of multiple channels to communicate to.
        """
        if isinstance(channels, str):
            channels_parsed: list = [channels]
        else:
            channels_parsed: list = [channel for channel in channels]

        return channels_parsed

    def flush(self) -> None:
        """
        Defines the flush method of the logging.Handler parent class.
        Does not do anything for the SlackBotHandler
        """
        pass

    def emit(self, record: logging.LogRecord) -> None:
        """
        Defines the emit method of the logging.Handler parent class.
        Emits incoming LogRecords as messages sent via the Slack bot (sequentially sent to all specified channels).

        Args:
            record: incoming LogRecord
        """
        message: str = self.format(record)

        for channel in self._channels:
            self._send_slack_message(message, channel)

    def _send_slack_message(self, message: str, channel: str) -> None:
        """
        Uses the WebClient of the Slack API to send a message to the specified channel.
        Catches potentially occurring SlackAPIErrors.

        Args:
            message: String of the message to be communicated.
            channel: String identifier of the channel to be communicated to.
        """
        try:
            _ = self._slack_client.chat_postMessage(
                channel=channel,
                text=message
            )
        except SlackApiError as e:
            print(e)
