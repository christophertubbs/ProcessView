"""
Application specific metadata values used to convey basic operating parameters
"""
import logging
import os
import typing

APPLICATION_NAME: typing.Final[str] = os.environ.get("PVIEW_APPLICATION_NAME", "ProcessView")
"""The name of this application"""

APPLICATION_DESCRIPTION: typing.Final[str] = os.environ.get(
    "PVIEW_APPLICATION_DESCRIPTION",
    """Displays local process information within your browser"""
)
"""The description of what this application does"""

DEFAULT_PORT: typing.Final[int] = int(os.environ.get("PVIEW_DEFAULT_PORT", 10324))
"""The port to serve on if none is specified"""

ALLOW_REMOTE: typing.Final[bool] = os.environ.get("PVIEW_ALLOW_REMOTE", "no").lower() in ('t', 'true', 'y', 'yes', '1')
"""Whether to allow remote access to this application. Set to `True` at your own risk"""

INDEX_PAGE: typing.Final[str] = os.environ.get("PVIEW_INDEX_PAGE", "")
"""The relative path to the index/home page of the application"""

USERNAME: typing.Final[str] = os.environ.get("USER")
"""The name of the user who is authorized to use this application"""

MAX_CLIENTS: typing.Final[int] = int(os.environ.get("PVIEW_MAX_CLIENTS", 5))
"""The maximum number of clients that may be connected at a given time"""

LOG_LEVEL: typing.Final[str] = os.environ.get("PVIEW_LOG_LEVEL", "INFO")
"""The logging level for messaging"""

if ALLOW_REMOTE:
    logging.warning(
        f"{APPLICATION_NAME} has been configured to allow remote connections. "
        f"Ensure https is enabled or else risk internal file inspection from remote sources."
        f"Use at your own risk."
    )