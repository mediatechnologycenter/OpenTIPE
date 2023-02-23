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
import unittest
from datetime import timedelta

from firebase_admin.auth import EmailAlreadyExistsError
from mtc_ape_api.api_client import APEClient
from mtc_ape_api.config import ApeConfig
from mtc_ape_web_editor.api_types.api_types import Language
from mtc_ape_web_editor.api_types.text_segments import TextSegmentMTOutput
from mtc_ape_web_editor.api_types.translations import MTOutputTranslation
from mtc_api_utils.clients.firebase_client import FirebaseClient

# Test constants

# Auth constants
TEST_EMAIL = "test@mtc-mail.ch"
TEST_PW = "mtc-test-pw-321"

# Translation constants
SRC_LANG = Language.DE
TARGET_LANG = Language.FR
TRANSLATION_ID = "translation-id"

TEST_SEGMENTS = [
    TextSegmentMTOutput(
        src_text="Dies ist ein Textsegment",
        mt_text="Ceci est un segment de texte"
    ),
    TextSegmentMTOutput(
        src_text="Noch ein Textsegment",
        mt_text="Un autre segment de texte"
    ),
    TextSegmentMTOutput(
        src_text="Der alte Esel soll geschlachtet werden. Deshalb flieht er und will Stadtmusikant in Bremen werden. Unterwegs trifft er nacheinander auf den "
                 "Hund, die Katze und den Hahn. Auch diese drei sind schon alt und sollen sterben. Sie folgen dem Esel und wollen ebenfalls Stadtmusikanten "
                 "werden. Auf ihrem Weg kommen sie in einen Wald und beschließen, dort zu übernachten. Sie entdecken ein Räuberhaus. Indem sie sich vor dem "
                 "Fenster aufeinanderstellen und mit lautem „Gesang“ einbrechen, erschrecken und vertreiben sie die Räuber. Die Tiere setzen sich an die Tafel "
                 "und übernehmen das Haus als Nachtlager. Ein Räuber, der später in der Nacht erkundet, ob das Haus wieder betreten werden kann, wird von den "
                 "Tieren nochmals und damit endgültig verjagt. Den Bremer Stadtmusikanten gefällt das Haus so gut, dass sie nicht wieder fort wollen und dort "
                 "bleiben.",
        mt_text="Le vieil âne doit être abattu. C'est pourquoi il s'enfuit et veut devenir un musicien de ville à Brême. En chemin, il rencontre successivement"
                " le chien, le chat et le coq. Ces trois-là sont aussi vieux et vont mourir. Ils suivent l'âne et veulent aussi devenir des musiciens de la "
                "ville. Sur leur chemin, ils arrivent dans une forêt et décident d'y passer la nuit. Ils découvrent la maison d'un voleur. En se plaçant devant"
                " la fenêtre et en entrant par effraction en „chantant“ fort, ils effraient et font fuir les voleurs. Les animaux s'assoient à table et font de"
                " la maison leur camp de nuit. Un voleur qui explore plus tard dans la nuit pour voir s'il est possible d'entrer à nouveau dans la maison est"
                " chassé par les animaux une fois de plus et ainsi pour de bon. Les musiciens de la ville de Brême aiment tellement la maison qu'ils ne veulent"
                " plus la quitter et y rester. Traduit avec www.DeepL.com/Translator (version gratuite)",
    )
]

STATUS_OK_MESSAGE = "status: [ok]"


# Helper functions
def print_time(test_name, start_time, end_time):
    delta_t = timedelta(microseconds=(end_time - start_time) / 1e3)

    print("[{}] completed in {}".format(test_name, delta_t))


# Test cases
class TestAPEIntegration(unittest.TestCase):
    # Initialize clients
    firebase_client = FirebaseClient(
        firebase_admin_credentials_url=ApeConfig.firebase_test_admin_credentials_url,
        polybox_auth=ApeConfig.polybox_credentials
    )

    # Create & login user
    try:
        test_user = firebase_client.create_user(email=TEST_EMAIL, password=TEST_PW)
    except EmailAlreadyExistsError:
        test_user = firebase_client.get_user(email=TEST_EMAIL)
        print("Test user already exists")

    test_user_auth_key = firebase_client.login_user(
        email=TEST_EMAIL,
        password=TEST_PW,
        firebase_project_api_key=ApeConfig.firebase_test_project_key
    )

    ape_client = APEClient(ApeConfig.ape_backend_url)

    @classmethod
    def setUpClass(cls) -> None:
        cls.ape_client.wait_for_service_readiness(timeout=timedelta(minutes=15))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.firebase_client.delete_user(cls.test_user.uid)

    def test_readiness(self):
        # Test call & timer
        start_time = time.perf_counter_ns()
        resp, readiness = self.ape_client.get_readiness()
        end_time = time.perf_counter_ns()

        # Assertions
        self.assertTrue(readiness, resp.reason)

        # Result
        print_time(self._testMethodName, start_time, end_time)

    def test_translate_all_segments(self):
        # Test constants
        test_request = MTOutputTranslation(src_lang=SRC_LANG, trg_lang=TARGET_LANG, text_segments=TEST_SEGMENTS)

        # Test call & timer
        start_time = time.perf_counter_ns()

        resp, translation = self.ape_client.translate(translation=test_request, access_token=self.test_user_auth_key)
        end_time = time.perf_counter_ns()

        # Assertions
        self.assertTrue(resp.ok, "HTTP response was {}: \n{}".format(resp.reason, resp.text))

        print(translation.get_printable_representation())

        # Result
        print_time(self._testMethodName, start_time, end_time)

    def test_translate_many_short_segments(self):
        # Test constants
        segment_no = 30
        test_request = MTOutputTranslation(src_lang=SRC_LANG, trg_lang=TARGET_LANG, text_segments=TEST_SEGMENTS[:2] * (segment_no // 2))

        # Test call & timer
        start_time = time.perf_counter_ns()
        resp, translation = self.ape_client.translate(translation=test_request, access_token=self.test_user_auth_key)
        end_time = time.perf_counter_ns()

        # Assertions
        self.assertTrue(resp.ok, "HTTP response was {}: \n{}".format(resp.reason, resp.text))

        print(translation.get_printable_representation())

        # Result
        print_time(self._testMethodName, start_time, end_time)

    def test_translate_single_long_segment(self):
        # Test constants
        test_request = MTOutputTranslation(src_lang=SRC_LANG, trg_lang=TARGET_LANG, text_segments=TEST_SEGMENTS[2:3])

        # Test call & timer
        start_time = time.perf_counter_ns()
        resp, translation = self.ape_client.translate(translation=test_request, access_token=self.test_user_auth_key)
        end_time = time.perf_counter_ns()

        # Assertions
        self.assertTrue(resp.ok, "HTTP response was {}: \n{}".format(resp.reason, resp.text))

        print(translation.get_printable_representation())

        # Result
        print_time(self._testMethodName, start_time, end_time)

    def test_translate_multiple_long_segments(self):
        # Test constants
        segment_no = 5
        test_request = MTOutputTranslation(src_lang=SRC_LANG, trg_lang=TARGET_LANG, text_segments=TEST_SEGMENTS[2:3] * segment_no)

        # Test call & timer
        start_time = time.perf_counter_ns()
        resp, translation = self.ape_client.translate(translation=test_request, access_token=self.test_user_auth_key)
        end_time = time.perf_counter_ns()

        # Assertions
        self.assertTrue(resp.ok, "HTTP response was {}: \n{}".format(resp.reason, resp.text))

        print(translation.get_printable_representation())

        # Result
        print_time(self._testMethodName, start_time, end_time)

    def test_multiple_languages(self):
        test_segment_multilang = TextSegmentMTOutput(src_text="Dies ist ein multilinguales Textsegment.", mt_text="This is a multi lingual text segment")
        test_request = MTOutputTranslation(src_lang=SRC_LANG, trg_lang=Language.EN, text_segments=[test_segment_multilang])

        # Translate to english
        resp, translation = self.ape_client.translate(translation=test_request, access_token=self.test_user_auth_key)

        # Assertions
        self.assertTrue(resp.ok, "HTTP response was {}: \n{}".format(resp.reason, resp.text))

        print(translation.get_printable_representation())

        # Same translation to french
        test_segment_multilang = TextSegmentMTOutput(src_text="Dies ist ein multilinguales Textsegment.",
                                                     mt_text="Il s'agit d'un segment de texte multilingue.")
        test_request = MTOutputTranslation(src_lang=SRC_LANG, trg_lang=Language.FR, text_segments=[test_segment_multilang])
        resp, translation = self.ape_client.translate(translation=test_request, access_token=self.test_user_auth_key)

        # Assertions
        self.assertTrue(resp.ok, "HTTP response was {}: \n{}".format(resp.reason, resp.text))

        print(translation.get_printable_representation())

    # Currently disabled
    def dict_is_used(self):
        dict_entry = "Textsegment"

        test_request = MTOutputTranslation(
            src_lang=Language(SRC_LANG),
            trg_lang=Language(TARGET_LANG),
            text_segments=TEST_SEGMENTS[0:2],
            user_dict={dict_entry: dict_entry}
        )

        resp, translation = self.ape_client.translate(translation=test_request, access_token=self.test_user_auth_key)

        # TODO: Adjust this once implemented
        message = "This feature is currently not yet supported by the models, therefore the test is expected to fail." \
                  "The exact output is also not guaranteed, so the test might have to be adjusted once the model supports dictionaries."

        # Assert dict entry was replaced in all TextSegments
        self.assertIn(dict_entry, translation.text_segments[0].ape_text, message)
        self.assertIn(dict_entry, translation.text_segments[1].ape_text, message)


if __name__ == '__main__':
    unittest.main()
