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

from typing import Tuple

import requests
from mtc_ape_web_editor.api_clients.api_client import TranslationClient
from mtc_ape_web_editor.api_types.translations import MTInputTranslation, MTOutputTranslation
from mtc_api_utils.clients.api_client import ContentType


class MTClient(TranslationClient):
    def translate(self, translation: MTInputTranslation, access_token: str = None) -> Tuple[requests.Response, MTOutputTranslation]:
        """
        Sends passed Translation to backend for translation

        Returns:
            response: the http response
            list[TextSegment]: a list of TextSegment objects representing the translated input
        """

        resp = requests.post(
            url=self._translate_route,
            json=translation.json_dict,
            headers=self.get_headers(
                access_token=access_token,
                content_type=ContentType.JSON
            ),
        )

        resp.raise_for_status()
        translation_output = MTOutputTranslation.parse_obj(resp.json())

        return resp, translation_output
