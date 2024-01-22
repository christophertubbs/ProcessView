"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import typing
import collections
import uuid
import logging

from aiohttp import web
from aiohttp.web_routedef import AbstractRoute
from aiohttp.web_routedef import RouteDef

from application_details import ALLOW_REMOTE
from application_details import LOG_LEVEL

from utilities.common import LOCAL_ONLY_IDENTIFIER


class LocalApplication(web.Application):
    def __init__(self, include_self: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.__include_self = bool(include_self)
        self.__current_client_ids: collections.deque[str] = collections.deque(maxlen=5)

        log_level = logging.getLevelName(LOG_LEVEL)
        logging.root.setLevel(log_level)

    @property
    def include_self(self) -> bool:
        return self.__include_self

    def is_valid_client_id(self, client_id: typing.Optional[str]) -> bool:
        return client_id in self.__current_client_ids

    def issue_client_id(self) -> str:
        new_client_id = str(uuid.uuid4())
        self.__current_client_ids.append(new_client_id)
        return new_client_id

    """
    A webserver application that may only serve data accessible exclusively to the local environment
    """
    def add_routes(self, routes: typing.Iterable[RouteDef]) -> typing.List[AbstractRoute]:
        if not ALLOW_REMOTE:
            invalid_routes: typing.List[str] = list()
            for route in routes:
                handler = route.handler

                if not getattr(handler, LOCAL_ONLY_IDENTIFIER, False):
                    invalid_routes.append(route.path)

            if len(invalid_routes) > 0:
                message = f"Cannot register routes - " \
                          f"the following routes were not marked as local only: {', '.join(invalid_routes)}"
                raise ValueError(message)

        return super().add_routes(routes)