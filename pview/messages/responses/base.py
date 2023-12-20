"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import abc
import typing

from ..base import PViewMessage


class PViewResponse(PViewMessage, abc.ABC):
    ...