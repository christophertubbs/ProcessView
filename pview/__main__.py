#!/usr/bin/env python3
"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import typing

import sys

from .launch_parameters import ApplicationArguments
from .server import serve

serve(ApplicationArguments(*sys.argv[1:]))