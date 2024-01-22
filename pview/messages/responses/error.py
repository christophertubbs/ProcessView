"""
Defines error messages to return to clients
"""
from __future__ import annotations

import json
import logging
import typing

import pydantic
from aiohttp import web

from . import PViewResponse


class ErrorResponse(PViewResponse):
    def __init__(self, **kwargs):
        if 'message_type' not in kwargs:
            kwargs['message_type'] = kwargs.get('operation', "Error")

        kwargs['operation'] = 'error'
        super().__init__(**kwargs)

        logging.error(json.dumps(self.model_dump(), indent=4))

    error_message: str = pydantic.Field(description="A description of the error")
    code: int
    message_type: typing.Optional[str] = pydantic.Field(
        default=None,
        description="The name of the type of message that caused the error"
    )

    def create_web_response(self) -> web.Response:
        data = self.model_dump()
        return web.json_response(data=data, status=self.code)


class ProcessErrorResponse(ErrorResponse):
    process_data: typing.Dict[str, typing.Any]

    def __init__(self, process_data: typing.Dict[str, typing.Any], **kwargs):
        kwargs['code'] = 403
        super().__init__(**kwargs)
        self.process_data = process_data


def invalid_message_response(**kwargs) -> ErrorResponse:
    if "error_message" not in kwargs:
        kwargs['error_message'] = "The received message was not valid JSON and/or could not be interpreted"

    kwargs['code'] = 400
    return ErrorResponse(
        **kwargs
    )


def unrecognized_message_response(**kwargs) -> ErrorResponse:
    if "error_message" not in kwargs:
        kwargs['error_message'] = "The received message was not valid"

    kwargs['code'] = 406
    return ErrorResponse(
        **kwargs
    )


def access_denied(operation: str, process_data: typing.Dict[str, typing.Any], **kwargs) -> ErrorResponse:
    return ProcessErrorResponse(
        operation=operation,
        process_data=process_data,
        **kwargs
    )


def item_missing(operation: str, message: str, **kwargs) -> web.Response:
    response_message = ErrorResponse(
        code=404,
        operation=operation,
        error_message=message,
        **kwargs
    )
    return response_message.create_web_response()
