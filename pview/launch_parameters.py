"""
The argument parser for the application
"""
from __future__ import annotations

import argparse
import typing

import application_details


class ApplicationArguments:
    def __init__(self, *argv):
        self.__port: typing.Optional[int] = None
        self.__index_page: typing.Optional[str] = None

        self.__parse_arguments(*argv)

    @property
    def port(self) -> int:
        return self.__port

    @property
    def index_page(self) -> str:
        return self.__index_page

    def __parse_arguments(self, *argv):
        parser = argparse.ArgumentParser(
            prog=application_details.APPLICATION_NAME,
            description=application_details.APPLICATION_DESCRIPTION
        )

        parser.add_argument(
            "-p",
            "--port",
            dest="port",
            default=application_details.DEFAULT_PORT,
            help="The port to run the application on"
        )

        parser.add_argument(
            "-i",
            "--index",
            dest="index_page",
            default=application_details.INDEX_PAGE,
            help="The path to the index page"
        )

        parameters = parser.parse_args(argv)

        self.__port = parameters.port
        self.__index_page = parameters.index_page

