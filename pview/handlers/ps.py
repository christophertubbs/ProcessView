"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import platform
import typing

from pathlib import Path

from aiohttp import web

from ..utilities.common import local_only

PS_KEYWORDS = (
    "pid",
    "ppid",
    "%cpu",
    "%mem",
    "rss",
    "state",
    "ruser",
    "command"
)


def _get_ps_command() -> str:
    operating_system_name = platform.system().lower()

    if operating_system_name in ("darwin", "linux"):
        return f"ps axo {','.join(PS_KEYWORDS)}"
    else:
        raise OSError(f"ProcessView is only valid for MacOS and Linux - Windows support has not been implemented")


def _read_ps() -> typing.Sequence[str]:
    pass


def _format_ps() -> typing.Dict[str, typing.Any]:
    pass


@local_only
async def ps(request: web.Request) -> web.Response:
    paths = []

    term = request.query.get("term")

    if term:
        term_path = Path(term)

        if term_path.exists() and term_path.is_dir():
            paths.extend([
                str(child)
                for child in term_path.iterdir()
                if (child.is_dir() or str(child).endswith("nc"))
                   and not str(child.name).startswith(".")
            ])
        elif not term_path.exists():
            match_name = str(term_path)
            term_path = term_path.parent

            if term_path.exists():
                paths.extend([
                    str(child)
                    for child in term_path.iterdir()
                    if str(child).startswith(match_name)
                        and (child.is_dir() or str(child).endswith("nc"))
                ])

    return web.json_response(data=paths)
