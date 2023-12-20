"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import typing
from datetime import datetime

from psutil import Process
from pydantic import Field

from .base import PViewResponse


def add_field_to_dict(
    process: Process,
    accessor: typing.Callable[[Process], typing.Any],
    backup_fields: typing.Dict[str, typing.Any],
    result_fields: typing.Dict[str, typing.Any],
    to_field: str,
    from_field: str = None,
    is_live: bool = None,
    post_process: typing.Callable[[typing.Any], typing.Any] = None,
    default: typing.Any = None
) -> bool:
    if is_live is None:
        is_live = True

    if from_field is None:
        from_field = to_field

    value = None

    if is_live:
        try:
            value = accessor(process)
        except:
            is_live = False

    if value is None:
        value = backup_fields.get(from_field, default)

    if isinstance(post_process, typing.Callable):
        value = post_process(value)

    result_fields[to_field] = value

    return is_live


class ProcessInformationResponse(PViewResponse):
    operation: typing.Literal['get_process']
    process_id: int = Field(description="The ID for this process")
    parent_process_id: int = Field(description="The process ID for the process that launched this")
    status: str = Field(description="The status of the process")
    username: str = Field(description="The user who owns this process")

    command: typing.Optional[str] = Field(default=None, description="The command that started this process")
    cpu_percent: typing.Optional[float] = Field(
        default=None,
        description="The percent of all CPU processing resources this process is consuming"
    )
    memory_percent: typing.Optional[float] = Field(
        default=None,
        description="The percent of all memory this process is consuming"
    )
    memory_usage: typing.Optional[float] = Field(
        default=None,
        description="The number of bytes of memory that this process is consuming"
    )
    working_directory: typing.Optional[str] = Field(
        default=None,
        description="The path to what the process considers the current working directory"
    )
    name: typing.Optional[str] = Field(
        default="<Unknown Process>",
        description="The name of the process"
    )
    thread_count: typing.Optional[int] = Field(
        default=1,
        description="The number of threads that this process is currently consuming"
    )
    file_descriptors: typing.Optional[int] = Field(
        default=0,
        description="The number of open file descriptors that this process is currently using"
    )
    open_file_count: typing.Optional[int] = Field(
        default=0,
        description="The number of files that this process currently has open"
    )
    start_time: typing.Optional[str] = Field(
        default=None,
        description="When this process started"
    )

    @classmethod
    def from_process(cls, process: Process) -> ProcessInformationResponse:
        safety_data: typing.Dict[str, typing.Any] = process.as_dict()

        constructor_arguments: typing.Dict[str, typing.Any] = {}

        process_is_live = add_field_to_dict(
            process=process,
            accessor=lambda proc: proc.cmdline(),
            backup_fields=safety_data,
            result_fields=constructor_arguments,
            to_field="command",
            from_field="exe",
        )

        process_is_live = add_field_to_dict(
            process=process,
            accessor=lambda proc: proc.cpu_percent(),
            backup_fields=safety_data,
            result_fields=constructor_arguments,
            to_field='cpu_percent',
            is_live=process_is_live,
            post_process=lambda val: round(val, 2) if isinstance(val, float) else val
        )

        process_is_live = add_field_to_dict(
            process=process,
            accessor=lambda proc: proc.memory_percent(),
            backup_fields=safety_data,
            result_fields=constructor_arguments,
            to_field='memory_percent',
            is_live=process_is_live,
            post_process=lambda val: round(val, 2) if isinstance(val, float) else val
        )

        process_is_live = add_field_to_dict(
            process=process,
            accessor=lambda proc: proc.memory_info().rss,
            backup_fields=safety_data,
            result_fields=constructor_arguments,
            from_field='memory_info',
            to_field='memory_usage',
            is_live=process_is_live,
            post_process=lambda val: val[1] if isinstance(val, typing.Sequence) else val
        )

        process_is_live = add_field_to_dict(
            process=process,
            accessor=lambda proc: proc.cwd(),
            backup_fields=safety_data,
            result_fields=constructor_arguments,
            from_field='cwd',
            to_field='working_directory',
            is_live=process_is_live,
        )

        process_is_live = add_field_to_dict(
            process=process,
            accessor=lambda proc: proc.name(),
            backup_fields=safety_data,
            result_fields=constructor_arguments,
            to_field='name',
            is_live=process_is_live
        )

        process_is_live = add_field_to_dict(
            process=process,
            accessor=lambda proc: proc.num_threads(),
            backup_fields=safety_data,
            result_fields=constructor_arguments,
            from_field='num_threads',
            to_field='thread_count',
            is_live=process_is_live,
            default=1
        )

        process_is_live = add_field_to_dict(
            process=process,
            accessor=lambda proc: proc.num_fds(),
            backup_fields=safety_data,
            result_fields=constructor_arguments,
            from_field='num_fds',
            to_field='file_descriptors',
            is_live=process_is_live
        )

        process_is_live = add_field_to_dict(
            process=process,
            accessor=lambda proc: proc.open_files(),
            backup_fields=safety_data,
            result_fields=constructor_arguments,
            from_field="open_files",
            to_field="open_file_count",
            is_live=process_is_live,
            post_process=lambda files: len(files) if isinstance(files, typing.Sequence) else files,
            default=0
        )

        process_is_live = add_field_to_dict(
            process=process,
            accessor=lambda proc: proc.create_time(),
            backup_fields=safety_data,
            result_fields=constructor_arguments,
            from_field="create_time",
            to_field="start_time",
            is_live=process_is_live,
            post_process=lambda val: datetime.fromtimestamp(val).strftime("%Y-%m-%d %H:%M%z") if isinstance(val, (int, float)) else val
        )

        process_is_live = add_field_to_dict(
            process=process,
            accessor=lambda proc: proc.pid,
            backup_fields=safety_data,
            result_fields=constructor_arguments,
            from_field="pid",
            to_field="process_id",
            is_live=process_is_live
        )

        process_is_live = add_field_to_dict(
            process=process,
            accessor=lambda proc: proc.ppid(),
            backup_fields=safety_data,
            result_fields=constructor_arguments,
            from_field="ppid",
            to_field="parent_process_id",
            is_live=process_is_live
        )

        process_is_live = add_field_to_dict(
            process=process,
            accessor=lambda proc: proc.status(),
            backup_fields=safety_data,
            result_fields=constructor_arguments,
            to_field="status",
            is_live=process_is_live
        )

        add_field_to_dict(
            process=process,
            accessor=lambda proc: proc.username(),
            backup_fields=safety_data,
            result_fields=constructor_arguments,
            to_field="username",
            is_live=process_is_live
        )


        return cls(**constructor_arguments)




