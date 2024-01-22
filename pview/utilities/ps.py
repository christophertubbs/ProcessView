"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import dataclasses
import enum
import json
import os
import typing
from typing import Iterator

from typing_extensions import ParamSpec
from typing_extensions import Concatenate

import pandas
import psutil
from psutil import Process

from utilities.common import ProcessOutput
from utilities.common import run_shell_command

ARGS_AND_KWARGS = ParamSpec("ARGS_AND_KWARGS")

SIZE_UNITS = {
    "B": 1,
    "KB": 2,
    "MB": 3,
    "GB": 4
}

class SizeUnit(enum.IntEnum):
    B = 1024**0
    KB = 1024**1
    MB = 1024**2
    GB = 1024**3


def convert_memory_size(
    amount: typing.Union[float, int, None],
    from_unit: SizeUnit,
    to_unit: SizeUnit = None
) -> typing.Optional[float]:
    if amount is None:
        return None

    bytes_in_amount = amount * from_unit

    if to_unit is None:
        to_unit = SizeUnit.B

    return bytes_in_amount / to_unit


def describe_memory(amount: typing.Union[float, int, None], from_unit: SizeUnit, to_unit: SizeUnit = None) -> str:
    if amount is None:
        if to_unit is None:
            return "??"

        return f"??{to_unit.name}"

    if to_unit is None:
        unit_index = 0
        current_unit = SizeUnit.B
        current_amount = convert_memory_size(amount=amount, from_unit=from_unit, to_unit=current_unit)

        while current_amount > 1024 and unit_index < len(SizeUnit) - 1:
            next_unit_name = SizeUnit._member_names_[unit_index + 1]
            next_unit = SizeUnit[next_unit_name]
            current_amount = convert_memory_size(amount=current_amount, from_unit=current_unit, to_unit=next_unit)
            current_unit = next_unit
            unit_index += 1
    else:
        current_unit = to_unit
        current_amount = convert_memory_size(amount=amount, from_unit=from_unit, to_unit=to_unit)

    return f"{current_amount:.2f}{current_unit.name}"


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
    user: str
    memory_usage: float
    memory_percent: float
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
            user=self.user,
            memory_percent=self.memory_percent,
            memory_usage=self.memory_usage,
            status=self.status,
            executable=self.executable,
            arguments=self.arguments
        )

    @property
    def memory_amount(self) -> str:
        return describe_memory(self.memory_usage, from_unit=SizeUnit.KB)

    @classmethod
    def from_process(cls, process: Process) -> typing.Optional[ProcessEntry]:
        try:
            safe_data = process.as_dict()
        except psutil.NoSuchProcess:
            return None

        cpu_percent = round(safe_data['cpu_percent'], 2) if safe_data['cpu_percent'] is not None else None
        memory_usage = safe_data['memory_info'].rss if safe_data['memory_info'] is not None else None
        memory_percent = round(safe_data['memory_percent'], 2) if safe_data['memory_percent'] is not None else None
        arguments = safe_data['cmdline'][1:] if safe_data['cmdline'] is not None else []
        exe = safe_data.get("exe")

        if isinstance(exe, str) and "/" in exe:
            name = exe.strip().split("/")[-1]
        else:
            name = safe_data.get("name")

        ppid = safe_data.get("ppid")
        username = safe_data.get("username")
        pid = safe_data.get("pid")
        status = safe_data.get("status")

        try:
            return cls(
                process_id=pid,
                parent_process_id=ppid,
                name=name,
                current_cpu_percent=cpu_percent,
                user=username,
                memory_usage=memory_usage,
                memory_percent=memory_percent,
                status=status,
                executable=exe,
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
        if not self.executable:
            return []
        return self.executable.strip().strip("/").split("/")


class ProcessStatus:
    """
    A programmatic implementation of the `ps` command
    """
    @classmethod
    def latest(cls) -> ProcessStatus:
        return cls()

    def __init__(self, include_self: bool = None):
        recorded_processes: typing.Dict[int, ProcessEntry] = PSTableGenerator.get_entries()

        self.__processes: typing.Dict[int, ProcessEntry] = {
            pid: process
            for pid, process in recorded_processes.items()
            if process is not None
        }

        if not include_self:
            current_pid = os.getpid()

            while current_pid != 1 and current_pid in self.__processes:
                current_process = self.__processes.pop(current_pid, None)
                print(f"Ignoring {current_process}")
                if current_process is None:
                    current_pid = 1
                else:
                    current_pid = current_process.parent_process_id

    def get_child_processes(self, parent_id: int) -> typing.Iterable[ProcessEntry]:
        ids_to_check: typing.List[int] = [parent_id]
        checked_ids: typing.List[int] = []
        child_processes: typing.List[ProcessEntry] = []

        while ids_to_check:
            id_to_check = ids_to_check.pop()

            for process in self.processes:
                if process.parent_process_id == id_to_check and process not in child_processes:
                    child_processes.append(process)
                    ids_to_check.append(process.process_id)

            checked_ids.append(id_to_check)

        return child_processes

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

    def get_by_pid(self, pid: int) -> typing.Optional[ProcessEntry]:
        return self.__processes.get(pid)


def interpret_state(state: str) -> str:
    """
    Interpret the STATE value of a `ps` result

    The state is given by a sequence of characters, for example, “RWNA”.  The first character indicates the run state of the process:

    - I       Marks a process that is idle (sleeping for longer than about 20 seconds).
    - R       Marks a runnable process.
    - S       Marks a process that is sleeping for less than about 20 seconds.
    - T       Marks a stopped process.
    - U       Marks a process in uninterruptible wait.
    - Z       Marks a dead process (a “zombie”).

    Additional characters after these, if any, indicate additional state information:

    - +       The process is in the foreground process group of its control terminal.
    - <       The process has raised CPU scheduling priority.
    - >       The process has specified a soft limit on memory requirements and is currently exceeding that limit; such a process is (necessarily) not swapped.
    - A       the process has asked for random page replacement (VA_ANOM, from vadvise(2), for example, lisp(1) in a garbage collect).
    - E       The process is trying to exit.
    - L       The process has pages locked in core (for example, for raw I/O).
    - N       The process has reduced CPU scheduling priority (see setpriority(2)).
    - S       The process has asked for FIFO page replacement (VA_SEQL, from vadvise(2), for example, a large image processing program using virtual memory to sequentially address voluminous data).
    - s        The process is a session leader.
    - V       The process is suspended during a vfork(2).
    - W       The process is swapped out.
    - X       The process is being traced or debugged.


    :param state: The identifier from `ps`
    :return: A plain english description of what the state meant
    """
    if not state:
        return ''

    overall_map = {
        "I": "Idle",
        "R": "Runnable",
        "S": "Sleeping",
        "T": "Stopped",
        "U": "Waiting",
        "Z": "Zombie"
    }

    additional_status_map = {
        "+": "In foreground of terminal",
        "<": "Raised CPU Priority",
        ">": "Exceeded soft memory limits",
        "A": "Asking for page replacement",
        "E": "Trying to exit",
        "L": "Has pages that are locked",
        "N": "Has reduced CPU Priority",
        "S": "Asked for FIFO page replacement",
        "s": "Is the session leader",
        "V": "Suspended during a fork",
        "W": "Was swapped out",
        "X": "Currently debugging"
    }

    status = overall_map[state[0]]

    for character in state[1:]:
        if character in additional_status_map:
            status += f", {additional_status_map[character]}"

    return status


class PSTableGenerator:
    """
    Structure used to form results from the `ps` command
    """
    @classmethod
    def user_column(cls) -> str:
        """
        The name of the column containing data about the user that ran a process
        """
        return "USER"

    @classmethod
    def user_format(cls) -> str:
        """
        The formatting string used to identify the user in the `ps` command
        """
        return f"user={cls.user_column()}"

    @classmethod
    def cpu_percent_column(cls) -> str:
        """
        The name of the column containing information on what percentage of the CPU is being used by a process
        """
        return "%cpu"

    @classmethod
    def cpu_percent_format(cls) -> str:
        """
        The formatting string used to identify the percentage of total compute used by a process from the `ps` command
        """
        return f"%cpu={cls.cpu_percent_column()}"

    @classmethod
    def memory_percent_column(cls) -> str:
        """
        The name of the column containing information on what percentage of the systems memory is being used by a process
        """
        return "%mem"

    @classmethod
    def memory_percent_format(cls) -> str:
        """
        The formatting string used to identify the percentage of total memory used by a process from the `ps` command
        """
        return f"%mem={cls.memory_percent_column()}"

    @classmethod
    def process_id_column(cls) -> str:
        """
        The name of the column containing the process ID of a process
        """
        return "PID"

    @classmethod
    def process_id_format(cls) -> str:
        """
        The formatting string used to identify the process ID of a process from the `ps` command
        """
        return f"pid={cls.process_id_column()}"

    @classmethod
    def parent_process_id_column(cls) -> str:
        """
        The name of the column containing the process ID of the parent of a process
        """
        return "PPID"

    @classmethod
    def parent_process_id_format(cls) -> str:
        """
        The formatting string used to identify the process ID of the parent of a process from the `ps` command
        """
        return f"ppid={cls.parent_process_id_column()}"

    @classmethod
    def state_column(cls) -> str:
        """
        The name of the column containing the state of the process
        """
        return "STATE"

    @classmethod
    def state_format(cls) -> str:
        return f"state={cls.state_column()}"

    @classmethod
    def command_and_args_column(cls) -> str:
        return "COMMAND"

    @classmethod
    def command_and_args_format(cls) -> str:
        return f"command={cls.command_column()}"

    @classmethod
    def command_column(cls) -> str:
        return "COMMAND"

    @classmethod
    def command_format(cls) -> str:
        return f"comm={cls.command_column()}"

    @classmethod
    def memory_column(cls) -> str:
        """
        The name of the column containing how much memory is being used by a process
        """
        return "MEMORY"

    @classmethod
    def memory_format(cls) -> str:
        return f"rss={cls.memory_column()}"

    @classmethod
    def arguments_column(cls) -> str:
        """
        The column of the PS Table that will contain arguments passed to the given command
        """
        return "ARGUMENTS"

    @classmethod
    def command_shell_command(cls) -> str:
        """
        The shell command used to get the pid and process command only (i.e. no command arguments)

        Utilizes `ps axo`. This means it will get every process, for all users, with or without a terminal,
        with the following format.
        """
        return f"ps axo {cls.process_id_format()},{cls.command_format()}"

    @classmethod
    def ps_shell_command(cls) -> str:
        """
        The shell command used to call `ps` and get almost all important values
        (getting isolated commands and commands with arguments at the same time will result in value truncation)

        Utilizes `ps axwwo`. This means it will get every process, for all users, with or without a terminal,
        without any truncation on the final value, with the following format.
        """
        return f"ps axwwo " \
               f"{cls.user_format()}," \
               f"{cls.process_id_format()}," \
               f"{cls.parent_process_id_format()}," \
               f"{cls.cpu_percent_format()}," \
               f"{cls.memory_percent_format()}," \
               f"{cls.memory_format()}," \
               f"{cls.state_format()}," \
               f"{cls.command_and_args_format()}"

    def __init__(self, run_command: typing.Callable[Concatenate[str, ARGS_AND_KWARGS], ProcessOutput] = None):
        """
        Constructor

        Prepare the generator to run `ps` and interpret the results

        :param run_command: The function used to call the `ps` Shell command
        """
        if run_command is None:
            run_command = run_shell_command

        self.__run_command = run_command

    def _parse_ps(self, command: str = None) -> typing.Tuple[int, typing.List[typing.Dict[str, typing.Any]]]:
        """
        Call `ps` and interpret the result individual lines

        :param command: The shell command that will yield data to be parsed
        :return: A list of all the rows returned by `ps` with each column value matched to its column name
        """
        ps_output = self.__run_command(command=command)

        # Split stdout from `ps` into the individual lines represented on screen
        output = ps_output.stdout.splitlines()

        # Separate the data that represents the header from the actual process data
        header_line = output[0].strip()

        # Replace gaps in the header line with a single space
        header_line = " ".join(header_line.split())

        data_lines = [
            line.strip()
            for line in output[1:]
        ]

        # Identify the names of each column in the header
        columns = [
            column_name
            for column_name in header_line.split()
            if column_name
        ]

        # Map each line in the data lines to the desired number of values
        #   The number of values is limited in order to account for spaces in the name of a command
        split_rows = (
            line.split(maxsplit=len(columns) - 1)
            for line in data_lines
        )

        # Match each value from each row with its corresponding column name
        processes = [
            {
                key: value
                for key, value in zip(columns, row)
            }
            for row in split_rows
        ]

        return ps_output.process_id, processes

    def look_up_commands(self) -> typing.Dict[int, str]:
        """
        Map the command name to their process ID for every active process

        Given::

            $ ps
              PID TTY          TIME CMD
            21329 pts/0    00:00:00 bash
            21353 pts/0    00:00:00 ps


        Results in::

            {
                21329: "bash",
                21353: "ps"
            }
        """
        command_id, result = self._parse_ps(self.command_shell_command())
        command_map = {
            int(float(pid_and_command[self.process_id_column()])): pid_and_command[self.command_column()]
            for pid_and_command in result
            if int(float(pid_and_command[self.process_id_column()])) != command_id
        }
        return command_map

    def create_process_list(
        self,
        exclude_ids: typing.Union[int, typing.Collection[int]] = None
    ) -> typing.List[typing.Dict[str, typing.Any]]:
        """
        Get a list of each entry from a `ps` command

        :param exclude_ids: process IDs to exclude
        :return: A list of details for each process from a `ps` command invocation
        """
        command_id, all_processes = self._parse_ps(self.ps_shell_command())
        commands = self.look_up_commands()

        final_processes: typing.Dict[int, typing.Dict[str, typing.Any]] = {}

        for process in all_processes:
            process = {key: value for key, value in process.items()}

            process_id = int(float(process[self.process_id_column()]))

            if process_id == command_id:
                continue

            if exclude_ids and process_id in exclude_ids:
                continue

            command = commands.get(process_id)

            if not command:
                continue

            parent_process_id = int(float(process[self.parent_process_id_column()]))

            process[self.process_id_column()] = process_id
            process[self.arguments_column()] = process[self.command_column()].replace(command, "").strip()
            process[self.command_column()] = command
            process[self.cpu_percent_column()] = float(process[self.cpu_percent_column()])
            process[self.parent_process_id_column()] = parent_process_id
            process[self.memory_column()] = int(float(process[self.memory_column()]))
            process[self.memory_percent_column()] = float(process[self.memory_percent_column()])

            if self.state_column() in process:
                state = process[self.state_column()]
                process[self.state_column()] = interpret_state(state)

            if parent_process_id > 2 and parent_process_id in final_processes:
                parent_process = final_processes.get(parent_process_id)
                parent_process[self.cpu_percent_column()] += process[self.cpu_percent_column()]
                parent_process[self.memory_column()] += process[self.memory_column()]
                parent_process[self.memory_percent_column()] += process[self.memory_percent_column()]
            else:
                final_processes[process_id] = process

                if process_id > 2:
                    processes_to_remove: typing.List[typing.Dict[str, typing.Any]] = [
                        existing_process
                        for existing_process in final_processes.values()
                        if existing_process[self.parent_process_id_column()] == process_id
                    ]

                    for process_to_remove in processes_to_remove:
                        process[self.cpu_percent_column()] += process_to_remove[self.cpu_percent_column()]
                        process[self.memory_column()] += process_to_remove[self.memory_column()]
                        process[self.memory_percent_column()] += process_to_remove[self.memory_percent_column()]

                        del final_processes[process_to_remove[self.process_id_column()]]

        return list(final_processes.values())

    def create_frame(self, exclude_ids: typing.Union[int, typing.Collection[int]] = None) -> pandas.DataFrame:
        return pandas.DataFrame(self.create_process_list(exclude_ids=exclude_ids))

    @classmethod
    def get_frame(
        cls,
        run_command: typing.Callable[Concatenate[str, ARGS_AND_KWARGS], ProcessOutput] = None,
        exclude_ids: typing.Union[int, typing.Collection[int]] = None
    ) -> pandas.DataFrame:
        generator = cls(run_command=run_command)
        return generator.create_frame(exclude_ids=exclude_ids)

    def create_dict(self, exclude_ids: typing.Union[int, typing.Collection[int]] = None) -> typing.Dict[int, typing.Any]:
        dictionary_representation = {
            process_id: dataclasses.asdict(process)
            for process_id, process in self.create_entries(exclude_ids=exclude_ids).items()
        }
        return dictionary_representation

    @classmethod
    def get_dict(
        cls,
        run_command: typing.Callable[Concatenate[str, ARGS_AND_KWARGS], ProcessOutput] = None,
        exclude_ids: typing.Union[int, typing.Collection[int]] = None
    ) -> typing.Dict[int, typing.Any]:
        generator = cls(run_command=run_command)
        return generator.create_dict(exclude_ids=exclude_ids)

    def create_entries(
        self,
        exclude_ids: typing.Union[int, typing.Collection[int]] = None
    ) -> typing.Dict[int, ProcessEntry]:
        entries: typing.Dict[int, ProcessEntry] = {}

        for process in self.create_process_list(exclude_ids=exclude_ids):
            entry = ProcessEntry(
                process_id=process[self.process_id_column()],
                parent_process_id=process[self.parent_process_id_column()],
                name=process[self.command_column()],
                current_cpu_percent=process[self.cpu_percent_column()],
                user=process[self.user_column()],
                memory_usage=process[self.memory_column()],
                memory_percent=process[self.memory_percent_column()],
                status=process[self.state_column()],
                executable=process[self.command_column()],
                arguments=process[self.arguments_column()]
            )
            entries[entry.process_id] = entry

        return entries

    @classmethod
    def get_entries(
        cls,
        run_command: typing.Callable[Concatenate[str, ARGS_AND_KWARGS], ProcessOutput] = None,
        exclude_ids: typing.Union[int, typing.Collection[int]] = None
    ) -> typing.Dict[int, ProcessEntry]:
        generator = cls(run_command=run_command)
        return generator.create_entries(exclude_ids=exclude_ids)

    def create_json(self, exclude_ids: typing.Union[int, typing.Collection[int]] = None) -> str:
        return json.dumps(self.create_dict(exclude_ids=exclude_ids))

    @classmethod
    def get_json(
        cls,
        run_command: typing.Callable[Concatenate[str, ARGS_AND_KWARGS], ProcessOutput] = None,
        exclude_ids: typing.Union[int, typing.Collection[int]] = None
    ) -> str:
        generator = cls(run_command=run_command)
        return generator.create_json(exclude_ids=exclude_ids)