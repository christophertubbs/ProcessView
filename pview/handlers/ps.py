"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import re
import typing
from datetime import datetime

import psutil
from aiohttp import web
from aiohttp import http_exceptions
from psutil import Process

from pview.models.tree import ProcessTree
from pview.utilities.common import local_only
from pview.utilities.common import to_bool
from pview.utilities.ps import byte_size_to_text

POSITIVE_INTEGER_PATTERN = re.compile(r"^\d+$")


def get_tree_payload(include_self: bool = None) -> typing.Dict[str, typing.Any]:
    include_self = to_bool(value=include_self)

    process_tree = ProcessTree.load(include_self=include_self)
    data = process_tree.plot_dict()
    data['memory_usage'] = byte_size_to_text(process_tree.memory_usage)
    data['cpu_percent'] = f"{round(process_tree.cpu_percent, 2)}%"

    return data


@local_only
async def ps_without_self(request: web.Request) -> web.Response:
    data = get_tree_payload(include_self=False)
    return web.json_response(data=data)


@local_only
async def ps_with_self(request: web.Request) -> web.Response:
    data = get_tree_payload(include_self=True)
    return web.json_response(data=data)


@local_only
async def get_process(request: web.Request) -> web.Response:
    potential_process_id = request.match_info['pid']

    if potential_process_id is None or not POSITIVE_INTEGER_PATTERN.search(potential_process_id):
        raise http_exceptions.HttpBadRequest(f"'{potential_process_id}' is not a valid process id")

    process_id = int(float(potential_process_id))

    data: typing.Dict[str, typing.Any] = {}

    if psutil.pid_exists(process_id):
        try:
            process = Process(int(float(process_id)))
            process_data = process.as_dict()

            data.update({
                "command": process_data.get("exe"),
                "cpu_percent": process_data.get("cpu_percent"),
                "memory_percent": process_data.get("memory_percent"),
                "memory_usage": process_data.get("memory_info")[1],
                "working_directory": process_data.get("cwd"),
                "name": process_data.get("name"),
                "thread_count": process_data.get("num_threads"),
                "file_descriptors": process_data.get("num_fds"),
                "open_file_count": 0,
                "create_time": None,
                "process_id": process_data.get("pid"),
                "parent_process_id": process_data.get("ppid"),
                "status": process_data.get("status"),
                "username": process_data.get("username")
            })

            open_files = process_data.get("open_files")
            if isinstance(open_files, typing.Sequence) and not isinstance(open_files, (str, bytes)):
                data['open_file_count'] = len(open_files)

            if isinstance(process_data.get("create_time"), (int, float)):
                data['create_time'] = datetime.fromtimestamp(process_data['create_time']).strftime("%Y-%m-%d %H:%M%z")
        except BaseException as exception:
            pass

    return web.json_response(data=data)
