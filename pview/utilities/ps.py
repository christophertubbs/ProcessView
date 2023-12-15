"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import dataclasses
import math
import os
import typing
from typing import Iterator

import psutil
from psutil import Process


B_IN_KB = 1000
B_IN_MB = B_IN_KB * 1000
B_IN_GB = B_IN_MB * 1000


@dataclasses.dataclass
class PSField:
    keyword: str
    name: str
    type_conversion: typing.Optional[typing.Callable[[str], typing.Any]] = dataclasses.field(default=lambda v: v)
    average: bool = dataclasses.field(default=False)
    is_last: bool = dataclasses.field(default=False)

    @property
    def raw_regex(self) -> str:
        if self.is_last:
            return f"(?P<{self.name}>.+)"
        return f"(?P<{self.name}>\S+)"

    @property
    def copy(self) -> PSField:
        return PSField(
            keyword=self.keyword,
            name=self.name,
            type_conversion=self.type_conversion,
            average=self.average,
            is_last=self.is_last
        )

    def __call__(self, value) -> typing.Any:
        return self.type_conversion(value)

    def __str__(self):
        return self.raw_regex

    def __repr__(self):
        return f"name: {self.name}, keyword: {self.keyword}, used in average: {self.average}, is last: {self.is_last}"


@dataclasses.dataclass
class ProcessEntry:
    process_id: int
    parent_process_id: int
    name: str
    current_cpu_percent: float
    thread_count: int
    user: str
    memory_usage: float
    memory_percent: float
    open_file_count: int
    file_descriptor_count: int
    status: str
    executable: str
    arguments: typing.Optional[typing.List[str]] = dataclasses.field(default_factory=list)

    @property
    def copy(self):
        return ProcessEntry(
            process_id=self.process_id,
            parent_process_id=self.parent_process_id,
            name=self.name,
            current_cpu_percent=self.current_cpu_percent,
            thread_count=self.thread_count,
            user=self.user,
            memory_percent=self.memory_percent,
            memory_usage=self.memory_usage,
            open_file_count=self.open_file_count,
            file_descriptor_count=self.file_descriptor_count,
            status=self.status,
            executable=self.executable,
            arguments=self.arguments
        )

    @property
    def memory_amount(self) -> str:
        memory_usage = self.memory_usage
        memory_unit = "B"

        if memory_usage > 1000:
            memory_unit = "KB"
            memory_usage /= 1000

        if memory_usage > 1000:
            memory_unit = "MB"
            memory_usage /= 1000

        if memory_usage > 1000:
            memory_unit = "GB"
            memory_usage /= 1000

        return f"{memory_usage}{memory_unit}"

    @classmethod
    def from_process(cls, process: Process) -> typing.Optional[ProcessEntry]:
        try:
            safe_data = process.as_dict()
        except psutil.NoSuchProcess:
            return None

        cpu_percent = round(safe_data['cpu_percent'], 2) if safe_data['cpu_percent'] is not None else None
        memory_usage = safe_data['memory_info'].rss if safe_data['memory_info'] is not None else None
        memory_percent = round(safe_data['memory_percent'], 2) if safe_data['memory_percent'] is not None else None
        thread_count = safe_data['num_threads'] if safe_data['num_threads'] else 1
        file_descriptor_count = safe_data['num_fds'] if safe_data['num_fds'] is not None else 0
        open_file_count = len(safe_data['open_files']) if safe_data['open_files'] is not None else 0
        arguments = safe_data['cmdline'][1:] if safe_data['cmdline'] is not None else ""

        try:
            return cls(
                process_id=process.pid,
                parent_process_id=process.ppid(),
                name=process.name(),
                current_cpu_percent=cpu_percent,
                thread_count=thread_count,
                user=process.username(),
                memory_usage=memory_usage,
                memory_percent=memory_percent,
                open_file_count=open_file_count,
                file_descriptor_count=file_descriptor_count,
                status=process.status(),
                executable=process.exe(),
                arguments=arguments
            )
        except Exception as e:
            print(process.as_dict())
            raise

    @classmethod
    def from_pid(cls, pid: typing.Union[str, int, float]) -> ProcessEntry:
        if isinstance(pid, str):
            pid = float(pid)

        pid = int(pid)

        return cls.from_process(Process(pid))

    @property
    def executable_parts(self) -> typing.Sequence[str]:
        return self.executable.strip().strip("/").split("/")


class ProcessStatus:
    @classmethod
    def latest(cls) -> ProcessStatus:
        return cls()

    def __init__(self):
        recorded_processes: typing.Dict[int, ProcessEntry] = {
            process.pid: ProcessEntry.from_process(process)
            for process in psutil.process_iter()
            if process.pid > 1
        }

        self.__processes: typing.Dict[int, ProcessEntry] = {
            pid: process
            for pid, process in recorded_processes.items()
            if process is not None
        }

        current_pid = os.getpid()

        while current_pid != 1 and current_pid in self.__processes:
            current_process = self.__processes.pop(current_pid, None)

            if current_process is None:
                current_pid = 1
            else:
                current_pid = current_process.parent_process_id

    def __contains__(self, item):
        return item in self.__processes

    def __getitem__(self, __k: int) -> ProcessEntry:
        return self.__processes[__k]

    def __len__(self) -> int:
        return len(self.__processes)

    def __iter__(self) -> Iterator[ProcessEntry]:
        return iter(self.__processes.values())

    @property
    def processes(self) -> typing.Sequence[ProcessEntry]:
        return [
            process.copy
            for process in self.__processes.values()
        ]

    @property
    def pids(self) -> typing.Sequence[int]:
        return [pid for pid in self.__processes.keys()]
