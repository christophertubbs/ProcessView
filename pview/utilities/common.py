"""
Functions and objects that may be used as simple utility functions throughout the application

The *ONLY* application file/library that should be referenced should be `application_details`.
Anything else may result in circular references.
"""
from __future__ import annotations

import logging
import os
import typing
import inspect
import re
import subprocess

import psutil
from aiohttp import web
from pydantic import BaseModel

from pview.application_details import ALLOW_REMOTE


_CLASS_TYPE = typing.TypeVar("_CLASS_TYPE")
"""Any sort of class"""

LOCAL_HOST_PATTERN = re.compile(r"([Ll][Oo][Cc][Aa][Ll][Hh][Oo][Ss][Tt]|127\.0\.0\.1|0\.0\.0\.0)")
"""A regular expression that matches on 'Localhost', 127.0.0.1, and 0.0.0.0, case insensitive"""

LOCAL_ONLY_IDENTIFIER = "local_only"
"""The key that will be placed on objects marked as only being valid locally"""

CLIENT_ID_IDENTIFIER = "PVIEW-CLIENT-ID"
"""The name that will be keyed to an ID value and attached to a cookie"""

VIEW_FUNCTION = typing.Callable[[web.Request], typing.Coroutine[typing.Any, typing.Any, web.Response]]
"""The signature for a function that may serve as a view"""


class ProcessOutput:
    """
    Represents the results of a completed process
    """
    def __init__(
        self,
        process_id: int,
        stdout: typing.Union[str, bytes],
        stderr: typing.Union[str, bytes],
        return_code: int,
        command: str
    ):
        self.__process_id = process_id
        self.__stdout = stdout.decode() if isinstance(stdout, bytes) else str(stdout)
        self.__stderr = stderr.decode() if isinstance(stderr, bytes) else str(stderr)
        self.__return_code = return_code
        self.__command = command

    @property
    def process_id(self) -> int:
        """
        The ID of the process that ran
        """
        return self.__process_id

    @property
    def stdout(self) -> str:
        """
        Data written to the stdout stream
        """
        return self.__stdout

    @property
    def stderr(self) -> str:
        """
        Data written to the stderr stream
        """
        return self.__stderr

    @property
    def return_code(self) -> int:
        """
        The return code of the process
        """
        return self.__return_code

    @property
    def command(self) -> str:
        """
        The command that initiated the process
        """
        return self.__command

    def __str__(self):
        return f"(pid: {self.process_id}) {self.command} => {self.return_code}"

    def __bool__(self):
        return self.return_code == 0

    def __repr__(self):
        return self.__str__()


def clean_input_list(inputs: typing.Iterable) -> typing.List[str]:
    """
    Correctly clean a collection of inputs used to influence the outcome of a shell command

    Example:
        >>> clean_input_list(9)
        ["9"]
        >>> clean_input_list(b'9')
        ["9"]
        >>> clean_input_list("9 3 2 4")
        ["9 3 2 4"]
        >>> clean_input_list(["echo", "1"])
        ["echo", "1"]
        >>> clean_input_list(["echo", 1])
        ["echo", "1"]
        >>> clean_input_list(["echo", "this is a statement"])
        ["echo", '"this is a statement"']

    :param inputs: The given inputs to a shell command
    :return: Correctly formatted inputs to a shell command
    """
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, typing.Iterable):
        return [inputs.decode() if isinstance(inputs, bytes) else str(inputs)]

    cleaned_inputs = []

    for entry in inputs:
        if isinstance(entry, str) and " " in entry:
            if entry.startswith('"') and entry.endswith('"'):
                cleaned_inputs.append(str(entry))
            elif entry.startswith("'") and entry.endswith("'"):
                cleaned_inputs.append(str(entry))
            elif '"' in entry:
                cleaned_inputs.append(f"'{entry}'")
            else:
                cleaned_inputs.append(f'"{entry}"')
        else:
            cleaned_inputs.append(str(entry))

    return cleaned_inputs


def run_shell_command(command: typing.Union[str, typing.Sequence[str]], *args) -> ProcessOutput:
    """
    Run a shell command

    Example:
        >>> single_string = run_shell_command("echo 'look at this example'")
        >>> print(single_string.stdout)
        look at this example
        >>> string_and_arg = run_shell_command("echo", "look at this example")
        >>> print(string_and_arg.stdout)
        look at this example
        >>> in_sequence = run_shell_command(["echo", "look at this example"])

    :param command: The command to call
    :return: Output data from the shell command
    """
    use_shell = False

    cleaned_args = clean_input_list(args)

    if isinstance(command, (bytes, str)) or not isinstance(command, typing.Iterable):
        command = clean_input_list(command)
        use_shell = True
    elif not isinstance(command, typing.List):
        command = [entry for entry in command]

    command = command + cleaned_args

    # subprocess.Popen is used instead of subprocess.run because Popen returns more information
    shell_process = subprocess.Popen(command, shell=use_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # stdout and stderr have to be caught separately since the buffers on the Popen close
    stdout, stderr = shell_process.communicate()

    return ProcessOutput(
        process_id=shell_process.pid,
        stdout=stdout,
        stderr=stderr,
        return_code=shell_process.returncode,
        command=shell_process.args
    )


def to_bool(value: typing.Union[int, str, float, bool, bytes] = None) -> bool:
    """
    Interpret the intention of given value to a matching boolean

    Example::
        >>> to_bool(True)
        True
        >>> to_bool(False)
        False
        >>> to_bool("True")
        True
        >>> to_bool("False")
        False
        >>> to_bool(1)
        True
        >>> to_bool(0)
        False
        >>> to_bool("Yes")
        True
        >>> to_bool("no")
        False
        >>> to_bool("ON")
        True
        >>> to_bool("off")
        False
        >>> to_bool("y")
        True
        >>> to_bool("n")
        False

    :param value: The value to test
    :return: True if the intention was True, False otherwise
    """
    if isinstance(value, bytes):
        value = value.decode()

    if isinstance(value, str):
        value = value.lower()
        return value in ('y', 't', 'yes', 'true', 'on', '1')

    return bool(value)


def local_only(view_function: VIEW_FUNCTION) -> VIEW_FUNCTION:
    """
    Ensures that a view function is only accessible via the local machine

    :param view_function: The view function that may only serve data locally
    :return: A wrapped view function that may only accept local requests and is labeled as being local only
    """
    if ALLOW_REMOTE:
        new_view_function = view_function
    else:
        async def wrapper(request: web.Request) -> web.Response:
            if not LOCAL_HOST_PATTERN.search(request.remote):
                raise web.HTTPNotFound()
            return await view_function(request)

        new_view_function = wrapper

    setattr(new_view_function, LOCAL_ONLY_IDENTIFIER, True)
    return new_view_function


def get_subclasses(base: typing.Type[_CLASS_TYPE]) -> typing.List[typing.Type[_CLASS_TYPE]]:
    """
    Gets a collection of all concrete subclasses of the given class in memory

    A subclass that has not been imported will not be returned

    Example:
        >>> import numpy
        >>> get_subclasses(float)
        [numpy.float64]

    Args:
        base: The base class to get subclasses from

    Returns:
        All implemented subclasses of a specified types
    """
    concrete_classes = [
        subclass
        for subclass in base.__subclasses__()
        if not inspect.isabstract(subclass)
    ]

    for subclass in base.__subclasses__():
        concrete_classes.extend([
            cls
            for cls in get_subclasses(subclass)
            if cls not in concrete_classes
               and not inspect.isabstract(cls)
        ])

    return concrete_classes


def get_html_response_from_text(
    text: str,
    context: typing.Dict[str, typing.Any] = None,
    headers: typing.Mapping[str, str] = None
) -> web.Response:
    """
    Create a response containing HTML directly from text

    :param text: HTML text to render
    :param context: Contextual data used to manipulate the HTML
    :param headers: Header data to add to the response
    :return: A response prepared to send HTML to a client
    """
    if context:
        logging.warning("Context management for HTML responses has not been implemented yet")

    return web.Response(text=text, content_type="text/html", headers=headers)


def get_html_response(
    html_file: os.PathLike,
    context: typing.Dict[str, typing.Any] = None,
    headers: typing.Mapping[str, str] = None
) -> web.Response:
    """
    Load data directly from an HTML file into a response

    :param html_file: The path to the HTML file
    :param context: Contextual data used to manipulate the HTML file
    :param headers: Header data to add to the response
    :return: A response prepared to send HTML to a client
    """
    with open(html_file) as html_data:
        return get_html_response_from_text(
            text=html_data.read(),
            context=context,
            headers=headers
        )


SERIALIZABLE_TYPES: typing.Tuple[typing.Type, ...] = (
    int,
    float,
    str,
    bool,
    type(None)
)


def serialize_value(
    container: typing.Union[typing.Dict[str, typing.Any], typing.List[typing.Any]],
    value_name: typing.Union[str, typing.Hashable],
    value: typing.Any
) -> typing.Union[typing.Dict[str, typing.Any], typing.List[typing.Any]]:
    if isinstance(value, SERIALIZABLE_TYPES):
        if isinstance(container, typing.List):
            container.append(value)
        else:
            container[value_name] = value
        return container

    if isinstance(value, typing.Mapping):
        new_map = {}

        for key, inner_value in value.items():
            serialize_value(new_map, key, inner_value)

        if isinstance(container, typing.List):
            container.append(new_map)
        else:
            container[value_name] = new_map

        return container
    elif isinstance(value, typing.MutableSequence):
        new_collection = []

        for index, inner_value in enumerate(value):
            serialize_value(new_collection, index, inner_value)

        if isinstance(container, typing.List):
            container.append(new_collection)
        else:
            container[value_name] = new_collection
        return container
    elif isinstance(value, typing.Callable):
        return container
    if isinstance(value, BaseModel) and hasattr(value, 'model_dump') and isinstance(value.model_dump, typing.Callable):
        signature = inspect.signature(value.model_dump)

        has_required_parameters = False

        for name, parameter in signature.parameters.items():
            has_required_parameters = has_required_parameters or parameter.default == parameter.empty

            if has_required_parameters:
                break

        if not has_required_parameters:
            new_value = value.model_dump()
            serialize_value(container=container, value_name=value_name, value=new_value)
            return container

    if hasattr(value, 'as_dict') and isinstance(value.as_dict, typing.Callable):
        signature = inspect.signature(value.as_dict)

        has_required_parameters = False

        for name, parameter in signature.parameters.items():
            has_required_parameters = has_required_parameters or parameter.default == parameter.empty

            if has_required_parameters:
                break

        if not has_required_parameters:
            new_value = value.as_dict()
            serialize_value(container=container, value_name=value_name, value=new_value)
            return container

    if hasattr(value, '_as_dict') and isinstance(value._as_dict, typing.Callable):
        signature = inspect.signature(value._as_dict)

        has_required_parameters = False

        for name, parameter in signature.parameters.items():
            has_required_parameters = has_required_parameters or parameter.default == parameter.empty

            if has_required_parameters:
                break

        if not has_required_parameters:
            new_value = value._as_dict()
            serialize_value(container=container, value_name=value_name, value=new_value)
            return container

    if hasattr(value, 'dict') and isinstance(value.dict, typing.Callable):
        signature = inspect.signature(value.dict)

        has_required_parameters = False

        for name, parameter in signature.parameters.items():
            has_required_parameters = has_required_parameters or parameter.default == parameter.empty

            if has_required_parameters:
                break

        if not has_required_parameters:
            new_value = value.dict()
            serialize_value(container=container, value_name=value_name, value=new_value)
            return container

    serialized_object = {}
    fields = [
        (name, inner_value)
        for name, inner_value in inspect.getmembers(value)
        if not name.startswith("_")
    ]

    for name, inner_value in fields:
        serialize_value(serialized_object, name, inner_value)

    if isinstance(container, typing.List):
        container.append(serialized_object)
    else:
        container[value_name] = serialized_object

    return container


def serialize_process(process: psutil.Process) -> typing.Dict[str, typing.Any]:
    process_key = "process"
    serialized_process = serialize_value({}, process_key, process)
    return serialized_process[process_key]