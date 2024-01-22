#!/usr/bin/env python3
"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import sys

from aiohttp import web

from application import LocalApplication
from application_details import APPLICATION_NAME
from application_details import INDEX_PAGE

from handlers import Index
from handlers import GetProcessView
from handlers import PS
from handlers import KillProcess
from handlers import register_resource_handlers
from launch_parameters import ApplicationArguments


def serve(arguments: ApplicationArguments):
    application = LocalApplication(include_self=arguments.include_self)

    application.add_routes([
        GetProcessView.create_route(method="get", path="/pid/{pid:\d+}"),
        Index.create_route(method="get", path=f"/{INDEX_PAGE}"),
        KillProcess.create_route(method="get", path="/kill/{pid:\d+}"),
        PS.create_route(method="get", path="/ps"),
    ])

    register_resource_handlers(application)

    print(f"Access {APPLICATION_NAME} from http://0.0.0.0:{arguments.port}/{INDEX_PAGE}")

    web.run_app(application, port=arguments.port)


if __name__ == "__main__":
    serve(ApplicationArguments(*sys.argv[1:]))