"""
@TODO: Put a module wide description here
"""
from __future__ import annotations
import typing
import pathlib

from aiohttp import web

from messages.responses import ErrorResponse
from pview.utilities.common import local_only
from pview.utilities import mimetypes
from pview.utilities.route import RouteInfo

RESOURCE_DIRECTORY = pathlib.Path(__file__).parent.parent / "static"
SCRIPT_DIRECTORY = RESOURCE_DIRECTORY / "scripts"
STYLE_DIRECTORY = RESOURCE_DIRECTORY / "style"
IMAGE_DIRECTORY = RESOURCE_DIRECTORY / "images"
FAVICON_PATH = IMAGE_DIRECTORY / "favicon.ico"

RESOURCE_MAP = {
    "scripts": SCRIPT_DIRECTORY,
    "script": SCRIPT_DIRECTORY,
    "style": STYLE_DIRECTORY,
    "styles": STYLE_DIRECTORY,
    "images": IMAGE_DIRECTORY,
    "image": IMAGE_DIRECTORY
}


def get_content_type(resource_type: str, filename: pathlib.Path) -> typing.Optional[str]:
    return mimetypes.get(filename.suffix)


def get_resource_directory(resource_type: str) -> pathlib.Path:
    return RESOURCE_MAP[resource_type]


@local_only
async def get_resource(request: web.Request) -> web.Response:
    resource_type: str = request.match_info['resource_type']

    if resource_type not in RESOURCE_MAP:
        not_valid = ErrorResponse(code=406, error_message=f"{resource_type} is not a valid type of resource")
        return not_valid.create_web_response()

    resource_name: str = request.match_info['name']
    resource_directory = get_resource_directory(resource_type)
    resource_path = resource_directory / resource_name

    if resource_path.exists():
        content_type = get_content_type(resource_type, resource_path)

        if content_type.startswith("image") or content_type.startswith("video"):
            return web.Response(
                body=resource_path.read_bytes(),
                content_type=content_type
            )
        else:
            return web.Response(
                text=resource_path.read_text(),
                content_type=content_type
            )

    not_found = ErrorResponse(code=404, error_message=f"No resource was found at '{resource_path}'")
    return not_found.create_web_response()


@local_only
async def get_favicon(request: web.Request) -> web.Response:
    return web.Response(
        body=FAVICON_PATH.read_bytes()
    )

RESOURCE_ROUTES = [
    RouteInfo(path="/{resource_type}/{name:.*}", handler=get_resource, name="get_resource"),
    RouteInfo(path="/favicon.ico", handler=get_favicon, name="get_favicon"),
]


def register_resource_handlers(application: web.Application):
    for route in RESOURCE_ROUTES:
        if not route.is_local_only():
            raise Exception(
                f"Only local views may be registered - the view for {route.path} isn't local only. "
                f"Please decorate it with '@local_only'"
            )

        route.register_get(application=application)