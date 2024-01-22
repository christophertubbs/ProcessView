"""
Views that reflect the results of the 'ps' command
"""
from __future__ import annotations

import os
import re
import typing
from datetime import datetime

import psutil
from aiohttp import web
from psutil import Process

import application_details
from handlers.http import RegisteredLocalOnlyView
from messages.responses import ErrorResponse
from messages.responses import PViewResponse
from messages.responses import access_denied
from messages.responses import invalid_message_response
from messages.responses.error import item_missing
from messages.responses.process import KillResponse
from pview.models.tree import ProcessTree
from pview.utilities.common import to_bool
from utilities.ps import ProcessEntry
from utilities.ps import ProcessStatus
from utilities.ps import SizeUnit
from utilities.ps import describe_memory

POSITIVE_INTEGER_PATTERN = re.compile(r"^\d+$")


def get_tree_payload(include_self: bool = None) -> typing.Dict[str, typing.Any]:
    include_self = to_bool(value=include_self)

    process_tree = ProcessTree.load(include_self=include_self)
    data = process_tree.plot_dict()
    data['memory_usage'] = describe_memory(process_tree.memory_usage, SizeUnit.KB)
    data['cpu_percent'] = f"{round(process_tree.cpu_percent, 2)}%"

    return data


class PS(RegisteredLocalOnlyView):
    @property
    def operation(self) -> str:
        return "Process Status"

    async def process_request(self, request: web.Request, *args, **kwargs) -> typing.Union[PViewResponse, web.Response]:
        data = get_tree_payload(include_self=getattr(request.app, "include_self", False))
        return web.json_response(data=data)


class KillProcess(RegisteredLocalOnlyView):
    @property
    def operation(self) -> str:
        return "Kill Process"

    async def process_request(self, request: web.Request, *args, **kwargs) -> typing.Union[PViewResponse, web.Response]:
        potential_process_id = request.match_info['pid']

        if potential_process_id is None or not POSITIVE_INTEGER_PATTERN.search(potential_process_id):
            not_found = ErrorResponse(
                code=404,
                operation=self.operation,
                error_message=f"'{potential_process_id}' is not a valid process id"
            )
            return not_found.create_web_response()

        process_id = int(float(potential_process_id))

        process: typing.Optional[psutil.Process] = None
        response: typing.Optional[PViewResponse] = None

        try:
            process = psutil.Process(process_id)
        except BaseException as exception:
            response = ErrorResponse(
                code=500,
                operation=self.operation,
                error_message=str(exception)
            )

        # TODO: This doesn't check if the given process id or the pid of the app are ancestors or grandchildren
        if response is None and os.getpid() == process_id:
            response = access_denied(
                operation=self.operation,
                process_data=process.as_dict(),
                error_message=f"Cannot kill the '{process.name()} ({process_id})' process - "
                              f"that is the application you are currently interacting with"
            )

        if response is None and process and process.username().strip() != application_details.USERNAME.strip():
            response = access_denied(
                operation=self.operation,
                process_data=process.as_dict(),
                error_message=f"{application_details.USERNAME} cannot kill {process.name()} ({process_id}) - "
                              f"it is owned by {process.username()}"
            )

        if response is None and process is not None and not process.is_running():
            response = KillResponse.for_process(
                operation=self.operation,
                process=process,
                success=False,
                message=f"{process.name()} ({process_id}) is no longer running"
            )
        elif response is None and process is not None:
            try:
                response = KillResponse.for_process(
                    operation=self.operation,
                    process=process,
                    success=True,
                    message=f"The process '{process.name()} ({process_id})' has been killed"
                )
                process.kill()
            except BaseException as exception:
                response = ErrorResponse(
                    code=500,
                    operation=self.operation,
                    error_message=f"Could not kill {process.name()} ({process_id}) - {exception}"
                )

        return response


class GetProcessView(RegisteredLocalOnlyView):
    @property
    def operation(self) -> str:
        return "Get Process"

    async def process_request(self, request: web.Request, *args, **kwargs) -> typing.Union[PViewResponse, web.Response]:
        potential_process_id = request.match_info['pid']

        if potential_process_id is None or not POSITIVE_INTEGER_PATTERN.search(potential_process_id):
            invalid_process_id = invalid_message_response(
                error_message=f"'{potential_process_id}' is not a valid process id"
            )
            return invalid_process_id.create_web_response()

        process_id = int(float(potential_process_id))

        data: typing.Dict[str, typing.Any] = {}

        if psutil.pid_exists(process_id):
            process = Process(int(float(process_id)))
            process_data = process.as_dict()

            required_fields = [
                "exe",
                "cpu_percent",
                "memory_info",
                "memory_percent"
            ]

            process_is_accessible = all([
                process_data.get(field) is not None
                for field in required_fields
            ])

            if process_is_accessible:
                children: typing.List[typing.Dict[str, typing.Any]] = []
                try:
                    children = [
                        child.as_dict()
                        for child in process.children(recursive=True)
                        if child is not None
                    ]
                except:
                    pass

                cpu_percent = sum([
                    child.get("cpu_percent") or 0
                    for child in children
                    if child.get("cpu_percent")
                ])
                cpu_percent += process_data.get("cpu_percent") if process_data.get("cpu_percent") is not None else 0

                memory_percent = sum([
                    child.get("memory_percent") or 0
                    for child in children
                ])
                memory_percent += process_data.get("memory_percent") if process_data.get("memory_percent") is not None else 0

                memory_usage = sum([
                    child.get("memory_info")[0] if child.get("memory_info") and child.get("memory_info")[0] else 0
                    for child in children
                ])
                memory_usage += process_data.get("memory_info")[0] or 0

                data.update({
                    "command": process_data.get("exe"),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "memory_usage": memory_usage,
                    "working_directory": process_data.get("cwd"),
                    "name": process_data.get("name"),
                    "create_time": None,
                    "process_id": process_data.get("pid"),
                    "parent_process_id": process_data.get("ppid"),
                    "status": process_data.get("status"),
                    "username": process_data.get("username"),
                    "can_modify": True
                })

                if isinstance(process_data.get("create_time"), (int, float)):
                    data['create_time'] = datetime.fromtimestamp(process_data['create_time']).strftime("%Y-%m-%d %H:%M%z")
            else:
                latest_status = ProcessStatus.latest()
                current_process_state: typing.Optional[ProcessEntry] = latest_status.get_by_pid(process_id)

                if current_process_state is None:
                    return item_missing(
                        operation=self.operation,
                        message=f"Data for process '{process_id}' could not be loaded"
                    )

                child_processes = latest_status.get_child_processes(process_id)

                memory_usage = sum([
                    child_process.memory_usage
                    for child_process in child_processes
                ])
                memory_usage += current_process_state.memory_usage

                cpu_percent = sum([
                    child_process.current_cpu_percent
                    for child_process in child_processes
                ])
                cpu_percent += current_process_state.current_cpu_percent

                memory_percent = sum([
                    child_process.memory_percent
                    for child_process in child_processes
                ])
                memory_percent += current_process_state.memory_percent

                data.update({
                    "command": current_process_state.executable,
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "memory_usage": memory_usage,
                    "name": current_process_state.executable_parts[-1],
                    "process_id": current_process_state.process_id,
                    "parent_process_id": current_process_state.parent_process_id,
                    "status": current_process_state.status,
                    "username": current_process_state.user,
                    "can_modify": False
                })
        else:
            response = item_missing(
                operation=self.operation,
                message=f"There are no processes with an ID of '{process_id}'"
            )
            return response

        return web.json_response(data=data)
