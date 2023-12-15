"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import typing

from aiohttp import web
from aiohttp.web_routedef import AbstractRoute
from aiohttp.web_routedef import RouteDef

from application_details import ALLOW_REMOTE


class LocalApplication(web.Application):
    """
    A webserver application that may only serve data accessible exclusively to the local environment
    """
    def add_routes(self, routes: typing.Iterable[RouteDef]) -> typing.List[AbstractRoute]:
        if not ALLOW_REMOTE:
            invalid_routes: typing.List[str] = list()
            for route in routes:
                handler = route.handler

                if not getattr(handler, common.LOCAL_ONLY_IDENTIFIER, False):
                    invalid_routes.append(route.path)

            if len(invalid_routes) > 0:
                message = f"Cannot register routes - " \
                          f"the following routes were not marked as local only: {', '.join(invalid_routes)}"
                raise ValueError(message)

        return super().add_routes(routes)