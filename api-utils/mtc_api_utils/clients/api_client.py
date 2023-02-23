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

import time
from datetime import datetime, timedelta
from enum import Enum
from http import HTTPStatus
from typing import Tuple, Optional

import httpx
import requests
from fastapi import HTTPException
from requests import Timeout

from mtc_api_utils.api_types import ApiStatus


class ContentType(Enum):
    value: str
    JSON = "application/json"
    TEXT = "text/plain"


class ApiBaseRoutes(Enum):
    liveness = "/api/liveness"
    readiness = "/api/readiness"
    status = "/api/status"


class ApiClient:
    def __init__(self, backend_url: str, base_route_timeout_seconds: int = 2, http_client: requests = requests):
        self._backend_url = backend_url
        self._base_route_timeout_seconds = base_route_timeout_seconds
        self.http_client = http_client

        self._liveness_route = backend_url + ApiBaseRoutes.liveness.value
        self._readiness_route = backend_url + ApiBaseRoutes.readiness.value
        self._status_route = backend_url + ApiBaseRoutes.status.value

    def get_liveness(self) -> Tuple[Optional[requests.Response], bool]:
        """
        Asserts backend availability.

        Returns:
            response: the http response
            bool: true if liveness check successful
        """
        try:
            resp = self.http_client.get(self._liveness_route, timeout=self._base_route_timeout_seconds)
        except (Timeout, requests.exceptions.ConnectionError, httpx.ConnectError):
            return None, False

        return resp, resp.status_code == HTTPStatus.OK

    def get_readiness(self) -> Tuple[Optional[requests.Response], bool]:
        """
        Asserts project readiness (Usually mostly reliant on model readiness).

        Returns:
            response: the http response
            bool: true if readiness check successful
        """
        try:
            resp = self.http_client.get(self._readiness_route, timeout=self._base_route_timeout_seconds)
        except (Timeout, requests.exceptions.ConnectionError, httpx.ConnectError) as e:
            print(f"An error occurred when requesting service readiness: {e}")
            return None, False

        return resp, resp.status_code == HTTPStatus.OK

    def get_status(self) -> Tuple[Optional[requests.Response], ApiStatus]:
        """
        Returns project Status as follows:
        \n - If the readiness key has a value of `false`, the project is running but not ready. This is most likely because some models are still initializing
        \n - The gpu_supported flag specifies if the service can make use of GPU resources
        \n - The gpu_supported flag specifies whether the current deployment is running with GPU resources enabled
        """
        try:
            resp = self.http_client.get(self._status_route, timeout=self._base_route_timeout_seconds)
        except (Timeout, requests.exceptions.ConnectionError, httpx.ConnectError):
            return None, ApiStatus(readiness=False, gpu_supported=False, gpu_enabled=False)

        resp.raise_for_status()

        status = ApiStatus.parse_obj(resp.json())

        return resp, status

    # TODO: Implement async wait -> minor API change
    def wait_for_service_readiness(self, timeout: timedelta = timedelta(minutes=3)) -> None:
        """
        Wait for a given service to be ready. This method should only ever be used in tests as it implements a busy wait.
        """
        start = datetime.now()

        while datetime.now() - start <= timeout:
            _, is_ready = self.get_readiness()

            if is_ready:
                return
            else:
                time.sleep(2)

        raise HTTPException(detail=f"Service did not become ready before timeout: {timeout}", status_code=HTTPStatus.SERVICE_UNAVAILABLE)

    @staticmethod
    def get_headers(access_token: str = None, content_type: ContentType = None) -> dict:
        auth_header = {
            'Authorization': f'Bearer {access_token}',
        }

        if content_type:
            auth_header["Content-Type"]: content_type.value

        return auth_header
