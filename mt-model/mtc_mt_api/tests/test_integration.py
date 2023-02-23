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

import datetime
import time
import unittest

from firebase_admin.auth import EmailAlreadyExistsError
from mtc_ape_web_editor.api_types.api_types import Language
from mtc_ape_web_editor.api_types.text_segments import TextSegmentMTInput
from mtc_ape_web_editor.api_types.translations import MTInputTranslation
from mtc_api_utils.clients.firebase_client import FirebaseClient

from mtc_mt_api.api_client import MTClient
from mtc_mt_api.config import MTConfig

# Auth constants
TEST_EMAIL = "test@mtc-mail.ch"
TEST_PW = "mtc-test-pw-321"

# Translation constants
SRC_LANG = "DE"
TARGET_LANG = "EN"
TRANSLATION_ID = "translation-id"

TEST_SEGMENTS = [
    TextSegmentMTInput(src_text="Dies ist ein Textsegment"),
    TextSegmentMTInput(src_text="Noch ein Textsegment"),
    TextSegmentMTInput(
        src_text="Der alte Esel soll geschlachtet werden. Deshalb flieht er und will Stadtmusikant in Bremen werden. Unterwegs trifft er nacheinander auf den "
                 "Hund, die Katze und den Hahn. Auch diese drei sind schon alt und sollen sterben. Sie folgen dem Esel und wollen ebenfalls Stadtmusikanten "
                 "werden. Auf ihrem Weg kommen sie in einen Wald und beschließen, dort zu übernachten. Sie entdecken ein Räuberhaus. Indem sie sich vor dem "
                 "Fenster aufeinanderstellen und mit lautem „Gesang“ einbrechen, erschrecken und vertreiben sie die Räuber. Die Tiere setzen sich an die Tafel "
                 "und übernehmen das Haus als Nachtlager. Ein Räuber, der später in der Nacht erkundet, ob das Haus wieder betreten werden kann, wird von den "
                 "Tieren nochmals und damit endgültig verjagt. Den Bremer Stadtmusikanten gefällt das Haus so gut, dass sie nicht wieder fort wollen und dort "
                 "bleiben.")
]

STATUS_OK_MESSAGE = "status: [ok]"


# Helper functions
def print_time(test_name, start_time, end_time):
    delta_t = datetime.timedelta(microseconds=(end_time - start_time) / 1e3)

    print("[{}] completed in {}".format(test_name, delta_t))


# Test cases
class TestMTIntegration(unittest.TestCase):
    # Initialize clients
    firebase_client = FirebaseClient(firebase_admin_credentials_url=MTConfig.firebase_test_admin_credentials_url,
                                     auth=MTConfig.credentials)

    # Create & login user
    try:
        test_user = firebase_client.create_user(email=TEST_EMAIL, password=TEST_PW)
    except EmailAlreadyExistsError:
        test_user = firebase_client.get_user(email=TEST_EMAIL)
        print("Test user already exists")

    test_user_auth_key = firebase_client.login_user(email=TEST_EMAIL,
                                                    password=TEST_PW,
                                                    firebase_project_api_key=MTConfig.firebase_test_project_key)

    mt_client = MTClient(MTConfig.mt_backend_url)

    @classmethod
    def setUpClass(cls) -> None:
        cls.mt_client.wait_for_service_readiness()

    def test_liveness(self):
        # Test call & timer
        start_time = time.perf_counter_ns()
        print(f"Performing liveness check on route: {self.mt_client._liveness_route}")
        resp, liveness = self.mt_client.get_liveness()
        end_time = time.perf_counter_ns()

        # Assertions
        self.assertTrue(liveness, resp.reason)

        # Result
        print_time(self._testMethodName, start_time, end_time)

    def test_translate_all_segments(self):
        # Test constants
        test_request = MTInputTranslation(src_lang=Language(SRC_LANG), trg_lang=Language(TARGET_LANG), text_segments=TEST_SEGMENTS)

        # Test call & timer
        start_time = time.perf_counter_ns()

        resp, _ = self.mt_client.translate(test_request, access_token=self.test_user_auth_key)
        end_time = time.perf_counter_ns()

        # Assertions
        self.assertTrue(resp.ok, "HTTP response was {}: \n{}".format(resp.reason, resp.text))

        # Result
        print_time(self._testMethodName, start_time, end_time)

    def test_translate_many_short_segments(self):
        # Test constants
        segment_no = 30
        test_request = MTInputTranslation(src_lang=Language(SRC_LANG), trg_lang=Language(TARGET_LANG), text_segments=TEST_SEGMENTS[:2] * (segment_no // 2))

        # Test call & timer
        start_time = time.perf_counter_ns()
        resp, _ = self.mt_client.translate(test_request, access_token=self.test_user_auth_key)
        end_time = time.perf_counter_ns()

        # Assertions
        self.assertTrue(resp.ok, "HTTP response was {}: \n{}".format(resp.reason, resp.text))

        # Result
        print_time(self._testMethodName, start_time, end_time)

    def test_translate_single_long_segment(self):
        # Test constants
        test_request = MTInputTranslation(src_lang=Language(SRC_LANG), trg_lang=Language(TARGET_LANG), text_segments=TEST_SEGMENTS[2:3])

        # Test call & timer
        start_time = time.perf_counter_ns()
        resp, _ = self.mt_client.translate(test_request, access_token=self.test_user_auth_key)
        end_time = time.perf_counter_ns()

        # Assertions
        self.assertTrue(resp.ok, "HTTP response was {}: \n{}".format(resp.reason, resp.text))

        # Result
        print_time(self._testMethodName, start_time, end_time)

    def test_translate_multiple_long_segments(self):
        # Test constants
        segment_no = 5
        test_request = MTInputTranslation(src_lang=Language(SRC_LANG), trg_lang=Language(TARGET_LANG), text_segments=TEST_SEGMENTS[2:3] * segment_no)

        # Test call & timer
        start_time = time.perf_counter_ns()
        resp, _ = self.mt_client.translate(test_request, access_token=self.test_user_auth_key)
        end_time = time.perf_counter_ns()

        # Assertions
        self.assertTrue(resp.ok, "HTTP response was {}: \n{}".format(resp.reason, resp.text))

        # Result
        print_time(self._testMethodName, start_time, end_time)


if __name__ == '__main__':
    unittest.main()
