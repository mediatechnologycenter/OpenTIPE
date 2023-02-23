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

from mtc_ape_web_editor.api_clients.api_client import ApeWebEditorClient
from mtc_ape_web_editor.api_types.api_types import Language
from mtc_ape_web_editor.api_types.text_segments import TextSegmentMTInput
from mtc_ape_web_editor.api_types.translations import MTInputTranslation
from mtc_ape_web_editor.config import BackendConfig
from firebase_admin.auth import EmailAlreadyExistsError
from mtc_api_utils.clients.firebase_client import FirebaseClient

# Auth constants
TEST_EMAIL = "test@mtc-mail.ch"
TEST_PW = "mtc-test-pw-321"
TEST_ROLES = ["machine-translation-325512"]

# Translation constantsTRANSLATION_ID = "translation-id"
SRC_LANG = "DE"
TARGET_LANG = "FR"

TEST_SEGMENTS = [
    TextSegmentMTInput(
        src_text="Dies ist ein Textsegment",
    ),
    TextSegmentMTInput(
        src_text="Noch ein Textsegment"
    ),
    TextSegmentMTInput(
        src_text="Der alte Esel soll geschlachtet werden. Deshalb flieht er und will Stadtmusikant in Bremen werden. Unterwegs trifft er nacheinander auf den "
                 "Hund, die Katze und den Hahn. Auch diese drei sind schon alt und sollen sterben. Sie folgen dem Esel und wollen ebenfalls Stadtmusikanten "
                 "werden. Auf ihrem Weg kommen sie in einen Wald und beschließen, dort zu übernachten. Sie entdecken ein Räuberhaus. Indem sie sich vor dem "
                 "Fenster aufeinanderstellen und mit lautem „Gesang“ einbrechen, erschrecken und vertreiben sie die Räuber. Die Tiere setzen sich an die Tafel "
                 "und übernehmen das Haus als Nachtlager. Ein Räuber, der später in der Nacht erkundet, ob das Haus wieder betreten werden kann, wird von den "
                 "Tieren nochmals und damit endgültig verjagt. Den Bremer Stadtmusikanten gefällt das Haus so gut, dass sie nicht wieder fort wollen und dort "
                 "bleiben."
    )
]

TEST_NONSTANDARD_SEGMENTS = [
    TextSegmentMTInput(
        src_text="  Dies ist ein Textsegment mit extra white space und ohne    Satzzeichen "
    ),
    TextSegmentMTInput(
        src_text=" - Dies ist ein Textsegment, welches ein Listenelement darstellt"
    ),
    TextSegmentMTInput(
        src_text="Dieses Textsegment stellt einen code block dar. `def does_this_work():`"
    )
]


# Helper functions
def print_time(test_name, start_time, end_time):
    delta_t = datetime.timedelta(microseconds=(end_time - start_time) / 1e3)

    print("[{}] completed in {}".format(test_name, delta_t))


# Test cases
class TestIntegration(unittest.TestCase):
    firebase_client = FirebaseClient(
        config=BackendConfig
    )

    # Create & login user
    try:
        test_user = firebase_client.create_user(email=TEST_EMAIL, password=TEST_PW, roles=TEST_ROLES)
    except EmailAlreadyExistsError:
        test_user = firebase_client.get_user(email=TEST_EMAIL)
        print("Test user already exists")
        firebase_client.update_user_roles(test_user.uid, roles=TEST_ROLES)

    test_user_auth_key = firebase_client.login_user(
        email=TEST_EMAIL,
        password=TEST_PW,
        firebase_project_api_key=BackendConfig.firebase_test_project_key
    )

    backend_client = ApeWebEditorClient(BackendConfig.backend_url)

    @classmethod
    def setUpClass(cls) -> None:
        print("Running tests against backend url: [{}]".format(BackendConfig.backend_url))
        cls.backend_client.wait_for_service_readiness()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.firebase_client.delete_user(cls.test_user.uid)

    def test_liveness(self):
        # Test call & timer
        start_time = time.perf_counter_ns()
        resp, liveness = self.backend_client.get_liveness()
        end_time = time.perf_counter_ns()

        # Assertions
        self.assertTrue(liveness, resp.reason)

        # Result
        print_time(self._testMethodName, start_time, end_time)

    def test_get_readiness(self):
        start_time = time.perf_counter_ns()
        resp, readiness = self.backend_client.get_readiness()
        end_time = time.perf_counter_ns()

        # Assertions
        self.assertTrue(readiness, resp.reason)

        # Result
        print_time(self._testMethodName, start_time, end_time)

    def test_translate_all_segments(self):
        # Test constants
        test_translation = MTInputTranslation(src_lang=Language(SRC_LANG), trg_lang=Language(TARGET_LANG), text_segments=TEST_SEGMENTS)

        # Test call & timer
        start_time = time.perf_counter_ns()

        resp, _ = self.backend_client.translate(translation=test_translation, access_token=self.test_user_auth_key)
        end_time = time.perf_counter_ns()

        # Assertions
        self.assertTrue(resp.ok, "HTTP response was {}: \n{}".format(resp.reason, resp.text))

        # Result
        print_time(self._testMethodName, start_time, end_time)

    def test_translate_many_short_segments(self):
        # Test constants
        segment_no = 30
        test_translation = MTInputTranslation(src_lang=Language(SRC_LANG), trg_lang=Language(TARGET_LANG), text_segments=TEST_SEGMENTS[:2] * (segment_no // 2))

        # Test call & timer
        start_time = time.perf_counter_ns()
        resp, _ = self.backend_client.translate(translation=test_translation, access_token=self.test_user_auth_key)
        end_time = time.perf_counter_ns()

        # Assertions
        self.assertTrue(resp.ok, "HTTP response was {}: \n{}".format(resp.reason, resp.text))

        # Result
        print_time(self._testMethodName, start_time, end_time)

    def test_translate_single_long_segment(self):
        # Test constants
        test_translation = MTInputTranslation(src_lang=Language(SRC_LANG), trg_lang=Language(TARGET_LANG), text_segments=TEST_SEGMENTS[2:3])

        # Test call & timer
        start_time = time.perf_counter_ns()
        resp, _ = self.backend_client.translate(translation=test_translation, access_token=self.test_user_auth_key)
        end_time = time.perf_counter_ns()

        # Assertions
        self.assertTrue(resp.ok, "HTTP response was {}: \n{}".format(resp.reason, resp.text))

        # Result
        print_time(self._testMethodName, start_time, end_time)

    def test_translate_multiple_long_segments(self):
        # Test constants
        segment_no = 5
        test_translation = MTInputTranslation(src_lang=Language(SRC_LANG), trg_lang=Language(TARGET_LANG), text_segments=TEST_SEGMENTS[2:3] * segment_no)

        # Test call & timer
        start_time = time.perf_counter_ns()
        resp, _ = self.backend_client.translate(translation=test_translation, access_token=self.test_user_auth_key)
        end_time = time.perf_counter_ns()

        # Assertions
        self.assertTrue(resp.ok, "HTTP response was {}: \n{}".format(resp.reason, resp.text))

        # Result
        print_time(self._testMethodName, start_time, end_time)

    def test_translate_non_standard_segments(self):
        # Test constants
        test_translation = MTInputTranslation(src_lang=Language(SRC_LANG), trg_lang=Language(TARGET_LANG), text_segments=TEST_NONSTANDARD_SEGMENTS)

        # Test call & timer
        start_time = time.perf_counter_ns()
        resp, _ = self.backend_client.translate(translation=test_translation, access_token=self.test_user_auth_key)
        end_time = time.perf_counter_ns()

        # Assertions
        self.assertTrue(resp.ok, "HTTP response was {}: \n{}".format(resp.reason, resp.text))

        # Result
        print_time(self._testMethodName, start_time, end_time)


if __name__ == '__main__':
    unittest.main()
