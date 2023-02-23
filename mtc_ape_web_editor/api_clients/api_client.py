# Copyright 2022 ETH Zurich, Media Technology Center

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from abc import ABC, abstractmethod
from typing import Any, Tuple

import requests
from mtc_ape_web_editor.api_types.translations import Translation, MTInputTranslation, APEOutputTranslation, HPEOutputTranslation, MTOutputTranslation
from mtc_api_utils.clients.api_client import ContentType, ApiClient


class TranslationClient(ApiClient, ABC):

    def __init__(self, backend_url: str):
        super().__init__(backend_url)

        self._translate_route = f"{backend_url}/translate"

    @abstractmethod
    def translate(self, translation: Translation, access_token: str = None) -> Tuple[requests.Response, MTOutputTranslation]:
        pass


class ApeWebEditorClient(TranslationClient):

    def translate(self, translation: MTInputTranslation, access_token: str = None) -> Tuple[requests.Response, APEOutputTranslation]:
        resp = requests.post(
            url=self._translate_route,
            json=translation.json_dict,
            headers=self.get_headers(
                access_token=access_token,
                content_type=ContentType.JSON
            ),
        )

        resp.raise_for_status()
        translation_output = APEOutputTranslation.parse_obj(resp.json())

        return resp, translation_output

    def __init__(self, backend_url: str):
        super().__init__(backend_url)

        self._translate_route = f"{backend_url}/api/translate"
        self._post_edition_route = f"{backend_url}/api/post-edition"
        self._dataset_route = f"{backend_url}/api/dataset"

    def create_post_editing(self, translation: HPEOutputTranslation, access_token: str = None) -> Tuple[requests.Response, Any]:
        resp = requests.post(
            url=self._post_edition_route,
            json=translation.json_dict,
            headers=self.get_headers(
                access_token=access_token,
                content_type=ContentType.JSON,
            ),
        )

        resp.raise_for_status()

        # TODO: Define & implement return type
        return resp, resp.json()

    def create_dataset(self, access_token: str = None) -> Tuple[requests.Response, Any]:
        resp = requests.post(
            url=self._dataset_route,
            headers=self.get_headers(
                access_token=access_token,
                content_type=ContentType.JSON,
            ),
        )

        resp.raise_for_status()

        # TODO: Define & implement return type
        return resp, resp.json()
