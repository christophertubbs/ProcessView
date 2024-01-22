"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import abc
import pathlib
import types
import typing

from aiohttp import web
from aiohttp.web_routedef import RouteDef

from messages.responses import ErrorResponse
from messages.responses import PViewResponse
from pview.utilities.common import get_html_response
from utilities.common import CLIENT_ID_IDENTIFIER
from utilities.common import LOCAL_ONLY_IDENTIFIER

INDEX_PATH = (pathlib.Path(__file__).parent.parent / "static" / "templates" / "index.html").resolve()


EXC_INFO = typing.Union[
    bool,
    tuple[typing.Type[BaseException], BaseException, typing.Optional[types.TracebackType]],
    tuple[None, None, None],
    BaseException
]

WEB_METHOD_DEFINITIONS = {
    "post": web.post,
    "get": web.get,
    "del": web.delete,
    "put": web.put,
}


class LocalOnlyView(abc.ABC, typing.Callable[[web.Request], typing.Awaitable[web.Response]]):
    @classmethod
    def create_route(cls, method: typing.Literal["post", "get", "del", "put"], path: str, *args, **kwargs) -> RouteDef:
        method = method.strip().lower()

        if method not in WEB_METHOD_DEFINITIONS:
            raise Exception(f"'{method}' is not a valid web method for view classes")

        return WEB_METHOD_DEFINITIONS[method](path=path, handler=cls(*args, **kwargs))

    def __init__(self, *args, **kwargs):
        setattr(self, LOCAL_ONLY_IDENTIFIER, True)

    @property
    @abc.abstractmethod
    def operation(self) -> str:
        pass

    @abc.abstractmethod
    async def process_request(self, request: web.Request, *args, **kwargs) -> typing.Union[PViewResponse, web.Response]:
        pass

    async def __call__(self, request: web.Request, *args, **kwargs) -> web.Response:
        try:
            response = await self.process_request(request=request, *args, **kwargs)
        except BaseException as exception:
            response = ErrorResponse(
                code=500,
                operation=self.operation,
                error_message=f"Error occurred in '{self}' - {exception}"
            )

        if isinstance(response, PViewResponse):
            response = response.create_web_response()

        return response

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()


class RegisteredLocalOnlyView(LocalOnlyView, abc.ABC):
    def __init__(self, require_browser: bool = None, require_client_id: bool = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__require_browser = bool(require_browser) if require_browser is not None else True
        self.__require_client_id = bool(require_client_id) if require_client_id is not None else True

    def __is_from_browser(self, request: web.Request) -> bool:
        user_agent = request.headers['User-Agent']

        if user_agent is None:
            return False

        if not user_agent.startswith("Mozilla/5.0"):
            return False

        search_terms = [
            'Chrome/',
            'Chromium/',
            'Firefox/',
            'Safari/',
            'Konqueror/',
            'Edge/',
        ]

        return next(filter(lambda term: term in user_agent, search_terms), None) is not None

    async def __call__(self, request: web.Request, *args, **kwargs) -> web.Response:
        if self.__require_browser and not self.__is_from_browser(request=request):
            return ErrorResponse(
                code=403,
                operation=self.operation,
                error_message=f"The '{self}' operation is only accessible from a browser"
            ).create_web_response()

        if self.__require_client_id:
            client_id = request.cookies.get(CLIENT_ID_IDENTIFIER)

            if not client_id:
                return ErrorResponse(
                    code=403,
                    operation=self.operation,
                    error_message=f"A client ID is required to perform a(n) '{self}' operation"
                ).create_web_response()

            client_id_is_valid: typing.Callable[[str], bool] = getattr(
                request.app,
                "is_valid_client_id",
                lambda cookie: True
            )

            if not client_id_is_valid(client_id):
                return ErrorResponse(
                    code=403,
                    operation=self.operation,
                    error_message=f"A valid client ID is required to perform a(n) '{self}' operation. "
                                  f"The one provided may be stale."
                ).create_web_response()

        return await super().__call__(request=request, *args, **kwargs)


class Index(LocalOnlyView):
    @property
    def operation(self) -> str:
        return "Index Page"

    async def process_request(self, request: web.Request, *args, **kwargs) -> typing.Union[PViewResponse, web.Response]:
        response = get_html_response(INDEX_PATH)
        response.set_cookie(
            name=CLIENT_ID_IDENTIFIER,
            value=getattr(request.app, "issue_client_id", lambda: "no-id")(),
            samesite="Strict"
        )
        return response
