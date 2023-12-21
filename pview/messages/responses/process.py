"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import re
import typing
import os

from datetime import datetime

import psutil
from aiohttp import http_exceptions
from aiohttp.web_exceptions import HTTPNotFound
from dateutil.parser import parse as parse_date

from psutil import Process
from pydantic import BaseModel
from pydantic import Field

from .base import PViewResponse


T = typing.TypeVar("T")


OBJECT_TYPE = typing.TypeVar("OBJECT_TYPE")
ACCESS_TYPE = typing.TypeVar("ACCESS_TYPE")

ACCESSOR = typing.Callable[[OBJECT_TYPE], ACCESS_TYPE]
POST_PROCESS = typing.Callable[[ACCESS_TYPE], typing.Any]


class QueryArg(typing.Callable[[typing.Any, typing.Any], bool]):
    def __init__(self, field: str, comparator: typing.Any, operation: str = None):
        self.__field = field if field.startswith("val::") or field.startswith("value::") else f"val::{field}"
        self.__operation = Comparisons.get(operation) if operation else Comparisons.default()
        self.__comparator = comparator

    @classmethod
    def query_by_args(cls, obj: typing.Any, *args: QueryArg) -> bool:
        for parameter in args:
            passed = parameter(obj)
            if not passed:
                return False
        return True

    @classmethod
    def query(
        cls,
        obj: typing.Any,
        *args: typing.Mapping[str, typing.Any]
    ) -> bool:
        query_args = [cls(**arg) for arg in args]
        return cls.query_by_args(obj, *query_args)

    def __get_field_value(self, obj: typing.Any, identifier: str) -> typing.Any:
        if isinstance(identifier, str):
            get_value = False

            if identifier.lower().startswith("val::"):
                identifier = identifier.lstrip("val::")
                get_value = True
            elif identifier.lower().startswith("value::"):
                identifier = identifier.lstrip("value::")
                get_value = True
            elif "->" in identifier:
                get_value = True

            if get_value:
                parts = [
                    part
                    for part in identifier.split("->")
                    if part
                ]

                member = obj

                for part in parts:
                    part = part.strip()

                    if isinstance(member, typing.Sequence) and re.match(r"^-?\d+$", part):
                        index = int(part)
                        member = member[index]
                    elif not hasattr(member, part):
                        raise KeyError(f"'{member} ({type(member)}' has not value named '{part}'")
                    else:
                        member = getattr(member, part)

                    if isinstance(member, typing.Callable):
                        member = member()

                identifier = member

        return identifier

    def __call__(self, obj: typing.Any) -> bool:
        field_is_invalid = not hasattr(obj, self.__field)
        field_is_invalid = field_is_invalid and not hasattr(obj, self.__field.replace("val::", ''))
        field_is_invalid = field_is_invalid and not hasattr(obj, self.__field.replace("value::", ''))

        if field_is_invalid:
            raise KeyError(f"'{obj} ({type(obj)})' has no field named '{self.__field}'")

        comparator = self.__get_field_value(obj, self.__comparator)
        value = self.__get_field_value(obj, self.__field)

        return self.__operation(value, comparator)

    def __str__(self):
        return f"{self.__operation.__name__} {self.__field}"

    def __repr__(self):
        return self.__str__()


class Comparisons:
    @classmethod
    def get_dropdown_values(cls) -> typing.Sequence[str]:
        return [
            "==",
            "!=",
            ">",
            ">=",
            "<",
            "<=",
            "AND",
            "OR"
        ]

    @classmethod
    def operation_map(cls) -> typing.Dict[str, typing.Callable[[typing.Any, typing.Any], bool]]:
        operations: typing.Dict[str, typing.Callable[[typing.Any, typing.Any], bool]] = {}

        def add_to_operations(comparison: typing.Callable[[typing.Any, typing.Any], bool], *terms):
            operations.update({
                term: comparison
                for term in terms
            })

        # Add equal
        add_to_operations(
            cls.equal,
            "=",
            "==",
            "===",
            "is",
            "equal",
            "equal_to",
            "equal to",
            "eq"
        )

        # Add not equal
        add_to_operations(
            cls.not_equal,
            "!=",
            "!==",
            "not",
            "is not",
            "isn't",
            "not equal",
            "not_equal",
            "not equal to",
            "not_equal_to",
            "ne"
        )

        # Add greater than
        add_to_operations(
            cls.greater_than,
            ">",
            "gt",
            "greater",
            "greater than",
            "greater_than",
        )

        # Add greater than or equal to
        add_to_operations(
            cls.greater_than_or_equal,
            ">=",
            "gte",
            "greater than or equal",
            "greater than or equal to",
            "greater_than_or_equal",
            "greater_than_or_equal_to",
        )

        # Add less than
        add_to_operations(
            cls.less_than,
            "<",
            "lt",
            "is less",
            "is_less",
            "less",
            "less than",
            "less_than",
        )

        # Add less than or equal to
        add_to_operations(
            cls.less_than_or_equal,
            "<=",
            "lte",
            "less than or equal",
            "less than or equal to",
            "less_than_or_equal",
            "less_than_or_equal_to",
        )

        # Add and
        add_to_operations(
            cls.both,
            "&",
            "&&",
            "both",
            "and"
        )

        # Add or
        add_to_operations(
            cls.either,
            "|",
            "||",
            "either",
            "or"
        )

        return operations

    @classmethod
    def get(cls, operation: typing.Union[typing.Callable[[typing.Any, typing.Any], bool], str]) -> typing.Callable[[typing.Any, typing.Any], bool]:
        if isinstance(operation, typing.Callable):
            return operation

        return cls.from_string(operation)

    @classmethod
    def from_string(cls, operation: str) -> typing.Callable[[typing.Any, typing.Any], bool]:
        if not operation:
            raise ValueError(f"Cannot find operation - no operation name was given")

        if isinstance(operation, bytes):
            operation = operation.decode()

        if not isinstance(operation, str):
            raise ValueError(
                f"Cannot find operation - '{operation} ({type(operation)})' is not a valid identifier for an operation"
            )

        operation = operation.strip().lower()

        operation_map = cls.operation_map()

        if operation not in operation_map:
            raise ValueError(f"'{operation}' is not a valid name for a comparison operation")

        return operation_map[operation]

    @classmethod
    def perform(cls, operation: str, first, second) -> bool:
        comparison = cls.from_string(operation)
        return comparison(first, second)

    @classmethod
    def default(cls) -> typing.Callable[[typing.Any, typing.Any], bool]:
        return cls.equal

    @classmethod
    def equal(cls, first, second) -> bool:
        return first == second

    @classmethod
    def not_equal(cls, first, second) -> bool:
        return first != second

    @classmethod
    def greater_than(cls, first, second) -> bool:
        return first > second

    @classmethod
    def greater_than_or_equal(cls, first, second) -> bool:
        return first >= second

    @classmethod
    def less_than(cls, first, second) -> bool:
        return first < second

    @classmethod
    def less_than_or_equal(cls, first, second) -> bool:
        return first <= second

    @classmethod
    def either(cls, first, second) -> bool:
        return first or second

    @classmethod
    def both(cls, first, second) -> bool:
        return first and second


def try_get(obj: OBJECT_TYPE, accessor: ACCESSOR, *backup_accessors: ACCESSOR) -> ACCESS_TYPE:
    try:
        return accessor(obj)
    except BaseException as original_exception:
        followup_exception = original_exception
        if backup_accessors:
            attempt = 1
            message = f"{original_exception}{os.linesep}. " \
                      f"Attempt {attempt} to access a value from {obj} failed - trying again"

            followup_exception = ValueError(message)

            for next_accessor in backup_accessors:
                attempt += 1
                try:
                    return next_accessor(obj)
                except BaseException as next_exception:
                    message = f"{followup_exception}{os.linesep}{next_exception} " \
                              f"Attempt {attempt} to access a value from {obj} failed - trying again"

                    followup_exception = ValueError(message)

        return followup_exception


def to_date_string(value: typing.Union[int, float, str, datetime]) -> typing.Optional[str]:
    if not isinstance(value, (int, float, str, datetime)) or isinstance(value, str) and value == '':
        return None

    if isinstance(value, (int, float)):
        value = datetime.fromtimestamp(value)
    elif isinstance(value, str):
        value = parse_date(value)

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M%z")

    return value


def add_field_to_dict(
    source: OBJECT_TYPE,
    accessor: ACCESSOR,
    backup_fields: typing.Dict[str, typing.Any],
    result_fields: typing.Dict[str, typing.Any],
    to_field: str,
    from_field: str = None,
    is_live: bool = None,
    post_process: POST_PROCESS = None,
    default: typing.Any = None
) -> bool:
    if is_live is None:
        is_live = True

    if from_field is None:
        from_field = to_field

    value = None

    if is_live:
        try:
            value = accessor(source)
        except:
            is_live = False

    if value is None:
        value = backup_fields.get(from_field, default)

    if isinstance(value, typing.Callable):
        value = value()

    if isinstance(post_process, typing.Callable):
        value = post_process(value)

    result_fields[to_field] = value

    return is_live


class SourceToConstructor(typing.Generic[OBJECT_TYPE]):
    """
    Creates constructor arguments based upon fields within a source object
    """
    def __init__(self, source_object: OBJECT_TYPE, backup_values: typing.Dict[str, typing.Any] = None):
        self.__source = source_object
        self.__backup_values = backup_values or {}
        self.__use_source = True
        self.__generated_dict: typing.Dict[str, typing.Any] = {}

    @property
    def output(self) -> typing.Dict[str, typing.Any]:
        return self.__generated_dict

    def create(self, constructor: typing.Callable[[typing.Any, ...], T]) -> T:
        return constructor(**self.__generated_dict)

    def add_field(
        self,
        to_field: str,
        accessor: ACCESSOR,
        *accessors: ACCESSOR,
        from_field: str = None,
        default: ACCESS_TYPE = None,
        post_process: POST_PROCESS = None
    ) -> SourceToConstructor:
        self.__use_source = add_field_to_dict(
            source=self.__source,
            accessor=lambda src: try_get(src, accessor, *accessors),
            backup_fields=self.__backup_values,
            result_fields=self.__generated_dict,
            to_field=to_field,
            from_field=from_field,
            is_live=self.__use_source,
            default=default,
            post_process=post_process
        )
        return self


class ProcessInformation(BaseModel):
    process_id: int = Field(description="The ID for this process")
    parent_process_id: int = Field(description="The process ID for the process that launched this")
    status: str = Field(description="The status of the process")
    username: str = Field(description="The user who owns this process")

    command: typing.Optional[str] = Field(default=None, description="The command that started this process")
    arguments: typing.Optional[typing.List[str]] = Field(
        default_factory=list,
        description="The parameters used when invoking the command"
    )
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
    def from_query(cls, *query_args: typing.Dict[str, str]) -> typing.Sequence[ProcessInformation]:
        processes = [process for process in psutil.process_iter() if QueryArg.query(process, *query_args)]
        return [cls.from_process(process) for process in processes]

    @classmethod
    def from_process_id(cls, process_id: typing.Union[int, float, str, bytes]) -> typing.Optional[ProcessInformation]:
        if isinstance(process_id, bytes):
            process_id = process_id.decode()

        if isinstance(process_id, str):
            process_id = float(process_id)

        if isinstance(process_id, float):
            process_id = int(float)

        if not isinstance(process_id, int):
            raise TypeError(
                f"'{process_id} ({type(process_id)})' is not a valid pid and cannot be used to generate process information"
            )

        try:
            process = Process(pid=process_id)
        except:
            return None

        return cls.from_process(process=process)


    @classmethod
    def from_process(cls, process: Process) -> ProcessInformation:
        safety_data: typing.Dict[str, typing.Any] = process.as_dict()

        transformer = SourceToConstructor(source_object=process, backup_values=safety_data)

        transformer.add_field(
            "command",
            Process.exe,
            lambda proc: proc.cmdline()[0],
            Process.name,
            from_field="exe",
            default=safety_data.get("name")
        )

        transformer.add_field(
            "arguments",
            Process.cmdline,
            lambda proc: [],
            from_field="cmdline",
            default=[],
            post_process=lambda cmd_array: cmd_array[1:]
        )

        transformer.add_field(
            to_field="cpu_percent",
            accessor=lambda proc: proc.cpu_percent(),
            post_process=lambda val: round(val, 2) if isinstance(val, float) else val
        )

        transformer.add_field(
            to_field="memory_percent",
            accessor=lambda proc: proc.memory_percent(),
            post_process=lambda val: round(val, 2) if isinstance(val, float) else val
        )

        transformer.add_field(
            from_field="memery_info",
            to_field="memory_usage",
            accessor=lambda proc: proc.memory_info.rss,
            post_process=lambda val: val[1] if isinstance(val, typing.Sequence) else val
        )

        transformer.add_field(
            from_field="cwd",
            to_field="working_directory",
            accessor=Process.cwd
        )

        transformer.add_field(
            to_field="name",
            accessor=Process.name
        )

        transformer.add_field(
            to_field="thread_count",
            from_field="num_threads",
            accessor=Process.num_threads,
            default=1
        )

        transformer.add_field(
            to_field="file_descriptors",
            from_field="num_fds",
            accessor=Process.num_fds,
        )

        transformer.add_field(
            to_field="open_file_count",
            from_field="open_files",
            accessor=Process.open_files,
            default=[],
            post_process=lambda files: len(files) if isinstance(files, typing.Sequence) else 0
        )

        transformer.add_field(
            to_field="start_time",
            from_field="create_time",
            accessor=Process.create_time,
            post_process=to_date_string
        )

        transformer.add_field(
            from_field="pid",
            to_field="process_id",
            accessor=lambda proc: proc.pid
        )
        
        transformer.add_field(
            from_field="ppid",
            to_field="parent_process_id",
            accessor=Process.ppid
        )

        transformer.add_field(
            to_field="status",
            accessor=Process.status
        )
        
        transformer.add_field(
            to_field="username",
            accessor=Process.username
        )

        return transformer.create(cls)


class ProcessInformationResponse(PViewResponse):
    process: ProcessInformation = Field(description="Information about the inquired process")

    @classmethod
    def for_process(cls, operation: str, process: Process, message_id: str = None) -> ProcessInformationResponse:
        information = ProcessInformation.from_process(process=process)
        return cls(operation=operation, process=information, message_id=message_id)

    @classmethod
    def for_process_id(
        cls,
        operation: str,
        process_id: typing.Union[str, int, bytes],
        message_id: str = None
    ) -> ProcessInformationResponse:
        information = ProcessInformation.from_process_id(process_id=process_id)

        if information is None:
            raise HTTPNotFound(reason=f"There are no running processes with a pid of {process_id}")

        return cls(operation=operation, process=information, message_id=message_id)


class MultipleProcessInformationResponse(PViewResponse):
    processes: typing.List[ProcessInformation] = Field(description="A collection of inquired processes")

    @classmethod
    def from_query_args(
        cls,
        operation: str,
        *args: QueryArg,
        message_id: str = None
    ) -> MultipleProcessInformationResponse:
        processes = [process for process in psutil.process_iter() if QueryArg.query_by_args(process, *args)]
        return cls(operation=operation, processes=processes, message_id=message_id)

    @classmethod
    def from_query(
        cls,
        operation: str,
        *args: typing.Dict[str, str],
        message_id: str = None
    ) -> MultipleProcessInformationResponse:
        processes = [process for process in psutil.process_iter() if QueryArg.query_by_args(process, *args)]
        return cls(operation=operation, processes=processes, message_id=message_id)
