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

from http import HTTPStatus
from typing import Tuple

import deepl
from mtc_ape_web_editor.api_types.api_types import Language
from mtc_ape_web_editor.api_types.translations import MTInputTranslation, MTOutputTranslation

from mtc_ape_web_editor.api_clients.api_client import TranslationClient
from requests import Response


class DeeplClient(TranslationClient):

    def __init__(self, deepl_api_key):
        super().__init__("")
        self.deepl_translator = deepl.Translator(auth_key=deepl_api_key)

        self.readiness = self.get_liveness()

    def get_liveness(self) -> Tuple[Response, bool]:
        """
        Asserts backend availability. Do not perform this regularly as it uses up the quota.

        Returns:
            response: the http response
            bool: true if liveness check successful
        """
        resp = Response()

        try:
            self.deepl_translator.get_usage()
        except Exception as e:
            print("Deepl Exception occurred: \n{}".format(e))
            resp.status_code = HTTPStatus.SERVICE_UNAVAILABLE
            resp.reason = "DeepL could not be reached"

            return resp, False

        resp.status_code = HTTPStatus.OK
        resp.reason = "status: [ok]"

        return resp, True

    def get_readiness(self) -> Tuple[Response, bool]:
        return self.readiness

    def translate(self, translation: MTInputTranslation, access_token: str = None) -> Tuple[Response, MTOutputTranslation]:
        # DeepL translation request
        text_segments = [sentence.src_text for sentence in translation.text_segments]
        deepl_translation = self.deepl_translator.translate_text(
            text=text_segments,
            source_lang="EN-US" if translation.src_lang == Language.EN else translation.src_lang.value,
            target_lang="EN-US" if translation.trg_lang == Language.EN else translation.trg_lang.value,
        )

        # Enrich TextSegment with translation
        output_segments = [
            textSegment.add_text(mt_text=translated_segment.text)
            for textSegment, translated_segment
            in zip(translation.text_segments, deepl_translation)
        ]

        output_translation = translation.with_segments(output_segments)

        resp = Response()
        resp.status_code = HTTPStatus.OK
        resp.reason = "Translation OK"

        return resp, output_translation
