"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

from aiohttp import web

from pview.models.tree import ProcessTree
from pview.utilities.common import local_only


@local_only
async def ps(request: web.Request) -> web.Response:
    process_tree = ProcessTree.load()
    data = process_tree.plot_dict()

    return web.json_response(data=data)
