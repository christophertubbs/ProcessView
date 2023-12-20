"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import abc
import typing

from pydantic import BaseModel
from pydantic import Field


class PViewMessage(BaseModel, abc.ABC):
    """
    A common base class for all messages
    """
    operation: str = Field(description="The name of the operation to perform")
    message_id: typing.Optional[str] = Field(default=None, description="A trackable ID for the message")