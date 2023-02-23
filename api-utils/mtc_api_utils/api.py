# Copyright 2022 ETH Zurich, Media Technology Center
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
from http import HTTPStatus
from typing import Callable, Type, Tuple, Union, Awaitable, TypeVar

from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp

from mtc_api_utils.api_types import ApiStatus, StandardTags
from mtc_api_utils.config import Config

service_unavailable_exception = HTTPException(
    status_code=HTTPStatus.SERVICE_UNAVAILABLE,
    detail="The api is currently not ready to accept requests. It may still be initializing",
)

IsReady = Callable[[], bool]
IsReadyAsync = Callable[[], Awaitable[bool]]

Res = TypeVar("Res")
SyncFunc = Callable[..., Res]
AsyncFunc = Callable[..., Awaitable[Res]]


class BaseApi(FastAPI):
    def __init__(
            self,
            is_ready: Union[IsReady, IsReadyAsync],
            config: Type[Config],
            index_message: str = "Welcome to the MTC Api",
            liveness_message: str = "liveness check: [ok]",
            docs_route_prefix: str = "/api",
            tags: Tuple[str] = (StandardTags.demo.value,)
    ):
        super().__init__(docs_url=f"{docs_route_prefix}/docs", redoc_url=f"{docs_route_prefix}/redoc", openapi_url=f"{docs_route_prefix}/openapi.json")

        self._is_ready = is_ready
        self.config = config

        self.index_message = index_message

        self.liveness_message = liveness_message

        self.liveness_path = "/api/liveness"
        self.readiness_path = "/api/readiness"

        self.tags = tags

        # Create and include shared base routes
        self.include_router(self.create_base_router())

        self.add_middleware(ReadinessMiddleware, base_api=self)

        if config.cors_allow_origins:
            self.add_middleware(
                CORSMiddleware,
                allow_origins=config.cors_allow_origins,
                allow_credentials=True,
                allow_methods=["GET", "POST", "DELETE", "PATCH"],  # ["*"],
                allow_headers=["*", "access-control-allow-credentials", "access-control-allow-origin", "authorization", "content-type"],  # ["*"],
            )

    @staticmethod
    async def maybe_await(func: Union[SyncFunc, AsyncFunc]) -> Res:
        if inspect.iscoroutinefunction(func):
            return await func()
        else:
            return func()

    async def is_ready(self) -> bool:
        return await self.maybe_await(self._is_ready)

    @property
    async def readiness_message(self):
        return f"Service readiness: [{await self.is_ready()}]"

    def create_base_router(self):
        base_router = APIRouter(tags=["Base Operations"])

        @base_router.get("/api")
        async def index():
            return self.index_message

        @base_router.get(self.liveness_path)
        async def liveness():
            return self.liveness_message

        @base_router.get(self.readiness_path)
        async def readiness() -> str:
            if await self.is_ready():
                return await self.readiness_message
            else:
                raise HTTPException(
                    detail="Service is not yet ready",
                    status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                )

        @base_router.get("/api/status")
        async def project_status() -> ApiStatus:
            return ApiStatus(
                readiness=await self.is_ready(),
                gpu_supported=self.config.gpu_supported,
                gpu_enabled=self.config.gpu_enabled,
                tags=self.tags,
            )

        return base_router

    async def assert_readiness(self):
        if not await self.is_ready():
            raise service_unavailable_exception


class ReadinessMiddleware(BaseHTTPMiddleware):

    def __init__(self, app: ASGIApp, base_api: BaseApi):
        super().__init__(app)
        self.baseApi = base_api

    async def dispatch(self, request, call_next):
        if self.baseApi.liveness_path not in str(request.url) and not await self.baseApi.is_ready():
            return JSONResponse(
                content=service_unavailable_exception.detail,
                status_code=service_unavailable_exception.status_code,
            )

        response = await call_next(request)
        return response
