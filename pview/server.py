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
from handlers import ps_with_self
from handlers import ps_without_self
from handlers import register_resource_handlers
from handlers import get_process
from launch_parameters import ApplicationArguments

from pview.handlers import handle_index


def serve(arguments: ApplicationArguments):
    application = LocalApplication()

    application.add_routes([
        web.get("/pid/{pid:\d+}", handler=get_process)
    ])

    register_resource_handlers(application)

    application.add_routes([
        web.get(f"/{INDEX_PAGE}", handler=handle_index),
        web.get(f"/ps", handler=ps_with_self if arguments.include_self else ps_without_self),
    ])

    print(f"Access {APPLICATION_NAME} from http://0.0.0.0:{arguments.port}/{INDEX_PAGE}")

    web.run_app(application, port=arguments.port)


if __name__ == "__main__":
    serve(ApplicationArguments(*sys.argv[1:]))