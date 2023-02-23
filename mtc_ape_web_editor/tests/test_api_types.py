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
import os
import unittest

from fastapi import HTTPException

from mtc_ape_web_editor.api_types.api_types import Language, TermDict
from mtc_ape_web_editor.api_types.text_segments import TextSegmentHPE, TextSegmentMTInput, TextSegmentAPEOutput
from mtc_ape_web_editor.api_types.translations import MTInputTranslation, APEOutputTranslation

# Test Constants
TRANSLATION_ID: str = "Translation-ID"
SEGMENT_ID: str = "Segment-ID"
SRC_TXT = "Source Text"
MT_TXT = "MT text"
APE_TXT = "APE text"
HPE_TXT = "HPE text"

TEST_KEY = "test-key"
TEST_VALUE = "test-value"

dir_path = os.path.dirname(__file__)
testfile_path = os.path.join(dir_path, 'test_dict.csv')


class TestTranslationAndSegments(unittest.TestCase):

    def test_language(self):
        lang_de = Language.DE
        lang_fr = Language.FR

        lang_pair = Language.pair(lang_de, lang_fr)

        self.assertIn(lang_de.value, lang_pair)
        self.assertIn(lang_fr.value, lang_pair)

        self.assertEqual("de-fr", lang_pair)

        translation = MTInputTranslation(src_lang=lang_de, trg_lang=lang_fr, text_segments=[])
        translation_lang_pair = Language.pair(translation.src_lang, translation.trg_lang)

        self.assertEqual(lang_pair, translation_lang_pair)

    def test_create_segment(self):
        segment = TextSegmentHPE(id=SEGMENT_ID, src_text=SRC_TXT, mt_text=MT_TXT, ape_text=APE_TXT, hpe_text=HPE_TXT)

        expected_dict = {
            "id": SEGMENT_ID,
            "src_text": SRC_TXT,
            "mt_text": MT_TXT,
            "ape_text": APE_TXT,
            "hpe_text": HPE_TXT,
        }

        segment_dict = segment.dict()
        self.assertEqual(expected_dict, segment_dict)

    def test_create_segment_mt_input(self):
        segment = TextSegmentMTInput(src_text=SRC_TXT)

        expected_dict = {
            "id": segment.id,
            "src_text": SRC_TXT,
        }

        segment_dict = segment.dict(exclude_none=True)
        self.assertEqual(expected_dict, segment_dict)

    def test_create_translation(self):
        segment = TextSegmentMTInput(src_text=SRC_TXT)
        translation = MTInputTranslation(src_lang=Language.DE, trg_lang=Language.FR, text_segments=[segment])

        self.assertEqual(Language.DE, translation.src_lang)
        self.assertEqual(Language.FR, translation.trg_lang)
        self.assertEqual(SRC_TXT, segment.src_text)

    def test_from_dict(self):
        test_dict = {
            "id": TRANSLATION_ID,
            "src_lang": "DE",
            "trg_lang": "fr",
            "text_segments": [
                {
                    "id": SEGMENT_ID,
                    "src_text": SRC_TXT
                }
            ]
        }

        MTInputTranslation.parse_obj(test_dict)

    def test_print_translation(self):
        segment = TextSegmentAPEOutput(src_text=SRC_TXT, mt_text=MT_TXT, ape_text=APE_TXT)
        translation = APEOutputTranslation(src_lang=Language.DE, trg_lang=Language.FR, text_segments=[segment])

        self.assertIn(f"src_text: {SRC_TXT}", translation.get_printable_representation())
        self.assertIn(f"mt_text: {MT_TXT}", translation.get_printable_representation())
        self.assertIn(f"ape_text: {APE_TXT}", translation.get_printable_representation())

    def test_raise_for_invalid_dicts_translation(self):
        test_dict_1 = "test-dict"
        test_dict_2 = "another-test-dict"

        test_dicts = [test_dict_1, test_dict_2]

        segment = TextSegmentAPEOutput(src_text=SRC_TXT, mt_text=MT_TXT, ape_text=APE_TXT)
        translation = APEOutputTranslation(src_lang=Language.DE, trg_lang=Language.FR, text_segments=[segment])

        # Empty dicts
        translation.raise_for_invalid_dicts(available_dicts=[])

        # One valid entry
        translation.selected_dicts = [test_dict_1]
        translation.raise_for_invalid_dicts(available_dicts=test_dicts)

        # Multiple valid entries
        translation.selected_dicts = test_dicts
        translation.raise_for_invalid_dicts(available_dicts=test_dicts)

        # Invalid entries
        translation.selected_dicts = test_dicts
        self.assertRaises(HTTPException, lambda: translation.raise_for_invalid_dicts(available_dicts=[]))

    def test_merge_dict_translation(self):
        test_user_dict = TermDict({
            "user": "user",
            "test": "test",
        })

        test_dict_name = "test_dict"
        test_selected_dicts = [test_dict_name]
        available_dicts = {test_dict_name: TermDict.from_csv(testfile_path)}

        segment = TextSegmentMTInput(src_text=SRC_TXT)
        translation = MTInputTranslation(
            src_lang=Language.DE,
            trg_lang=Language.FR,
            text_segments=[segment],
            user_dict=test_user_dict,
            selected_dicts=test_selected_dicts
        )

        merged_dicts = translation.merged_dicts(available_dicts)

        self.assertEqual(merged_dicts["A"], "A")
        self.assertEqual(merged_dicts["AAP"], "APD")
        self.assertEqual(merged_dicts["ABC-Schutz"], "NBC protection")

        self.assertEqual(merged_dicts["user"], "user")
        self.assertEqual(merged_dicts["test"], "test")


class TestTermDictionary(unittest.TestCase):

    def test_create_TermDictionary(self):
        term_dict = TermDict.from_csv(testfile_path)
        self.assertIsNotNone(term_dict)

        term_dict = TermDict.from_csv(testfile_path)
        self.assertIsNotNone(term_dict)

    def test_access_TermDictionary(self):
        term_dict = TermDict.from_csv(testfile_path)

        self.assertEqual(term_dict["A"], "A")
        self.assertEqual(term_dict["AAP"], "APD")
        self.assertEqual(term_dict["ABC-Schutz"], "NBC protection")

    def test_merged_dict(self):
        test_user_dict = {
            "user": "user",
            "test": "test",
        }

        term_dict = TermDict.from_csv(testfile_path)
        term_dict.merge_dict(test_user_dict)

        self.assertEqual(term_dict["A"], "A")
        self.assertEqual(term_dict["AAP"], "APD")
        self.assertEqual(term_dict["ABC-Schutz"], "NBC protection")

        self.assertEqual(term_dict["user"], "user")
        self.assertEqual(term_dict["test"], "test")

    def test_chain_create_text_segments(self):
        mt_input = TextSegmentMTInput(src_text=SRC_TXT)
        mt_output = mt_input.add_text(mt_text=MT_TXT)
        ape_output = mt_output.add_text(ape_text=APE_TXT)
        hpe_output = ape_output.add_text(hpe_text=HPE_TXT)

        self.assertEqual(SRC_TXT, hpe_output.src_text)
        self.assertEqual(MT_TXT, hpe_output.mt_text)
        self.assertEqual(APE_TXT, hpe_output.ape_text)
        self.assertEqual(HPE_TXT, hpe_output.hpe_text)

    def test_generic_translation(self):
        mt_input = TextSegmentMTInput(src_text=SRC_TXT)

        translation = MTInputTranslation(
            src_lang=Language.DE,
            trg_lang=Language.FR,
            text_segments=[mt_input]
        )
        self.assertEqual(SRC_TXT, translation.text_segments[0].src_text)

        mt_output = mt_input.add_text(mt_text=MT_TXT)
        translation_mt = translation.with_segments(segments=[mt_output])
        self.assertEqual(MT_TXT, translation_mt.text_segments[0].mt_text)

        ape_output = mt_output.add_text(ape_text=APE_TXT)
        translation_ape = translation_mt.with_segments(segments=[ape_output])
        self.assertEqual(APE_TXT, translation_ape.text_segments[0].ape_text)

        hpe_output = ape_output.add_text(hpe_text=HPE_TXT)
        translation_hpe = translation_ape.with_segments(segments=[hpe_output])
        self.assertEqual(HPE_TXT, translation_hpe.text_segments[0].hpe_text)
