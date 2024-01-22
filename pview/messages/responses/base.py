"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import abc
import typing

from aiohttp import web

from ..base import PViewMessage


class PViewResponse(PViewMessage, abc.ABC):
    def create_web_response(self) -> web.Response:
        data = self.model_dump()
        return web.json_response(data=data)


class InfoResponse(PViewResponse):
    message: str

    def __init__(self, **kwargs):
        kwargs['message_type'] = 'info'
        super().__init__(**kwargs)
