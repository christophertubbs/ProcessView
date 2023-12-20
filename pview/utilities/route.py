"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import typing
from dataclasses import dataclass

from aiohttp import web


@dataclass
class RouteInfo:
    path: str
    handler: typing.Callable[[web.Request], typing.Coroutine[typing.Any, typing.Any, web.Response]]
    name: typing.Optional[str]

    def is_local_only(self) -> bool:
        return getattr(self.handler, "local_only", False)

    def register_get(self, application: web.Application):
        if not self.is_local_only():
            raise Exception(
                f"Only local views may be registered - the view for {self.path} isn't local only. "
                f"Please decorate it with '@local_only'"
            )

        application.add_routes([
            web.get(self.path, handler=self.handler)
        ])