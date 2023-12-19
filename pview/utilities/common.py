"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import logging
import os
import typing
import inspect
import re

from aiohttp import web

from pview.application_details import ALLOW_REMOTE


_CLASS_TYPE = typing.TypeVar("_CLASS_TYPE")


LOCAL_HOST_PATTERN = re.compile(r"([Ll][Oo][Cc][Aa][Ll][Hh][Oo][Ss][Tt]|127\.0\.0\.1|0\.0\.0\.0)")
"""A regular expression that matches on 'Localhost', 127.0.0.1, and 0.0.0.0, case insensitive"""

LOCAL_ONLY_IDENTIFIER = "local_only"

VIEW_FUNCTION = typing.Callable[[web.Request], typing.Coroutine[typing.Any, typing.Any, web.Response]]


def local_only(view_function: VIEW_FUNCTION) -> VIEW_FUNCTION:
    """
    Ensures that a view function is only accessible via the local machine

    :param view_function: The view function that may only serve data locally
    :return: A wrapped view function that may only accept local requests and is labeled as being local only
    """
    if ALLOW_REMOTE:
        new_view_function = view_function
    else:
        async def wrapper(request: web.Request) -> web.Response:
            if not LOCAL_HOST_PATTERN.search(request.remote):
                raise web.HTTPNotFound()
            return await view_function(request)

        new_view_function = wrapper

    setattr(new_view_function, LOCAL_ONLY_IDENTIFIER, True)
    return new_view_function


def get_subclasses(base: typing.Type[_CLASS_TYPE]) -> typing.List[typing.Type[_CLASS_TYPE]]:
    """
    Gets a collection of all concrete subclasses of the given class in memory

    A subclass that has not been imported will not be returned

    Example:
        >>> import numpy
        >>> get_subclasses(float)
        [numpy.float64]

    Args:
        base: The base class to get subclasses from

    Returns:
        All implemented subclasses of a specified types
    """
    concrete_classes = [
        subclass
        for subclass in base.__subclasses__()
        if not inspect.isabstract(subclass)
    ]

    for subclass in base.__subclasses__():
        concrete_classes.extend([
            cls
            for cls in get_subclasses(subclass)
            if cls not in concrete_classes
               and not inspect.isabstract(cls)
        ])

    return concrete_classes


def get_html_response_from_text(
    text: str,
    context: typing.Dict[str, typing.Any] = None,
    headers: typing.Mapping[str, str] = None
) -> web.Response:
    """
    Create a response containing HTML directly from text

    :param text: HTML text to render
    :param context: Contextual data used to manipulate the HTML
    :param headers: Header data to add to the response
    :return: A response prepared to send HTML to a client
    """
    if context:
        logging.warning("Context management for HTML responses has not been implemented yet")

    return web.Response(text=text, content_type="text/html", headers=headers)


def get_html_response(
    html_file: os.PathLike,
    context: typing.Dict[str, typing.Any] = None,
    headers: typing.Mapping[str, str] = None
) -> web.Response:
    """
    Load data directly from an HTML file into a response

    :param html_file: The path to the HTML file
    :param context: Contextual data used to manipulate the HTML file
    :param headers: Header data to add to the response
    :return: A response prepared to send HTML to a client
    """
    with open(html_file) as html_data:
        return get_html_response_from_text(
            text=html_data.read(),
            context=context,
            headers=headers
        )