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
import shutil
import unittest
from copy import deepcopy
from datetime import datetime

from mtc_ape_web_editor.api_clients.mongodb_client import DatasetKey, DatasetOptions, MongoDBClient, DbTranslation
from mtc_ape_web_editor.api_types.api_types import Language, UserEvent, EventLogType
from mtc_ape_web_editor.api_types.text_segments import TextSegmentHPE
from mtc_ape_web_editor.api_types.translations import HPEOutputTranslation
from mtc_ape_web_editor.config import BackendConfig

# Test constants
SRC_LANG = "DE"
TARGET_LANG = "FR"

TEST_SEGMENTS = [
    TextSegmentHPE(
        id="0",
        src_text="Dies ist ein Textsegment.",
        mt_text="Il s'agit d'un segment de texte",
        ape_text="C'est un segment de texte",
        hpe_text="Ceci est un segment de texte",

    ),
    TextSegmentHPE(
        id="1",
        src_text="Der alte Esel soll geschlachtet werden. Deshalb flieht er und will Stadtmusikant in Bremen werden. Unterwegs trifft er nacheinander auf den "
                 "Hund, die Katze und den Hahn. Auch diese drei sind schon alt und sollen sterben. Sie folgen dem Esel und wollen ebenfalls Stadtmusikanten "
                 "werden. Auf ihrem Weg kommen sie in einen Wald und beschließen, dort zu übernachten. Sie entdecken ein Räuberhaus. Indem sie sich vor dem "
                 "Fenster aufeinanderstellen und mit lautem „Gesang“ einbrechen, erschrecken und vertreiben sie die Räuber. Die Tiere setzen sich an die Tafel "
                 "und übernehmen das Haus als Nachtlager. Ein Räuber, der später in der Nacht erkundet, ob das Haus wieder betreten werden kann, wird von den "
                 "Tieren nochmals und damit endgültig verjagt. Den Bremer Stadtmusikanten gefällt das Haus so gut, dass sie nicht wieder fort wollen und dort "
                 "bleiben.",
        mt_text="Le vieil âne doit être abattu. C'est pourquoi il s'enfuit et veut devenir un musicien de ville à Brême. En chemin, il "
                "rencontre successivement le chien, le chat et le coq. Ces trois-là sont aussi vieux et vont mourir. Ils suivent l'âne "
                "et veulent aussi devenir des musiciens de la ville. Sur leur chemin, ils arrivent dans une forêt et décident d'y "
                "passer la nuit. Ils découvrent la maison d'un voleur. En se plaçant devant la fenêtre et en entrant par effraction en "
                "\"chantant\" fort, ils effraient et font fuir les voleurs. Les animaux s'assoient à table et font de la maison leur "
                "camp de nuit. Un voleur qui explore plus tard dans la nuit pour voir s'il est possible d'entrer à nouveau dans la "
                "maison est chassé par les animaux une fois de plus et ainsi pour de bon. Les musiciens de la ville de Brême aiment "
                "tellement la maison qu'ils ne veulent plus la quitter et y rester.",
        ape_text="Le vieil âne doit être abattu. C'est pourquoi il s'enfuit et veut devenir un musicien de ville à Brême. En chemin, il "
                 "rencontre successivement le chien, le chat et le coq. Ces trois-là sont aussi vieux et vont mourir. Ils suivent l'âne "
                 "et veulent aussi devenir des musiciens de la ville. Sur leur chemin, ils arrivent dans une forêt et décident d'y "
                 "passer la nuit. Ils découvrent la maison d'un voleur. En se plaçant devant la fenêtre et en entrant par effraction en "
                 "\"chantant\" fort, ils effraient et font fuir les voleurs. Les animaux s'assoient à table et font de la maison leur "
                 "camp de nuit. Un voleur qui explore plus tard dans la nuit pour voir s'il est possible d'entrer à nouveau dans la "
                 "maison est chassé par les animaux une fois de plus et ainsi pour de bon. Les musiciens de la ville de Brême aiment "
                 "tellement la maison qu'ils ne veulent plus la quitter et y rester.",
        hpe_text="Le vieil âne doit être abattu. C'est pourquoi il s'enfuit et veut devenir un musicien de ville à Brême. En chemin, il "
                 "rencontre successivement le chien, le chat et le coq. Ces trois-là sont aussi vieux et vont mourir. Ils suivent l'âne "
                 "et veulent aussi devenir des musiciens de la ville. Sur leur chemin, ils arrivent dans une forêt et décident d'y "
                 "passer la nuit. Ils découvrent la maison d'un voleur. En se plaçant devant la fenêtre et en entrant par effraction en "
                 "\"chantant\" fort, ils effraient et font fuir les voleurs. Les animaux s'assoient à table et font de la maison leur "
                 "camp de nuit. Un voleur qui explore plus tard dans la nuit pour voir s'il est possible d'entrer à nouveau dans la "
                 "maison est chassé par les animaux une fois de plus et ainsi pour de bon. Les musiciens de la ville de Brême aiment "
                 "tellement la maison qu'ils ne veulent plus la quitter et y rester.",
    ),
]

TEST_DICT = {
    "key": "value",
    "key2": "value2",
}

DATASET_PATH = BackendConfig.dataset_path


class TestDbClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        BackendConfig.print_config()

        cls.db_client = MongoDBClient(BackendConfig.db_connection_string, translations_collection_name="test_translations")

    def test_db_liveness(self):
        try:
            liveness = self.db_client.get_liveness()
            self.assertTrue(liveness)
        except Exception as e:
            self.fail(e)

    def test_post_editing_and_dataset(self):
        self.create_post_editing()
        self.create_dataset()
        self.create_partial_dataset()

    def test_events(self):
        self.db_client.insert_event(
            event=UserEvent(
                event=EventLogType.accept_event,
                userEmail="test@email.ch",
                timestamp=str(datetime.now()),
            ),
        )

        events = self.db_client.get_events()

        self.assertEqual(1, len(events))

    def create_post_editing(self):
        test_translation = DbTranslation.from_hpe_translation(
            HPEOutputTranslation(
                src_lang=Language(SRC_LANG),
                trg_lang=Language(TARGET_LANG),
                text_segments=TEST_SEGMENTS,
            ),
        )

        self.db_client.insert_or_update_text_segment(test_translation)

        # Add mt, ape, hpe & dict to translation & update
        updated_segment = deepcopy(TEST_SEGMENTS)

        # Fully update first segment
        updated_segment[0].mt_text = "Il s'agit d'un segment de texte nouveau"
        updated_segment[0].ape_text = "C'est un segment de texte nouveau"
        updated_segment[0].hpe_text = "Ceci est un segment de texte nouveau"

        # Partially update second segment
        updated_segment[1].hpe_text = "Le vieil âne doit être abattu. C'est pourquoi il s'enfuit et veut devenir un musicien de ville à Brême. En chemin, il " \
                                      "rencontre successivement le chien, le chat et le coq. Ces trois-là sont aussi vieux et vont mourir. Ils suivent l'âne " \
                                      "et veulent aussi devenir des musiciens de la ville. Sur leur chemin, ils arrivent dans une forêt et décident d'y " \
                                      "passer la nuit. Ils découvrent la maison d'un voleur. En se plaçant devant la fenêtre et en entrant par effraction en " \
                                      "\"chantant\" fort, ils effraient et font fuir les voleurs. Les animaux s'assoient à table et font de la maison leur " \
                                      "camp de nuit. Un voleur qui explore plus tard dans la nuit pour voir s'il est possible d'entrer à nouveau dans la " \
                                      "maison est chassé par les animaux une fois de plus et ainsi pour de bon. Les musiciens de la ville de Brême aiment " \
                                      "tellement la maison qu'ils ne veulent plus la quitter et y rester. (This text has been updated)"

        # Add dict to translation
        updated_translation = DbTranslation.from_hpe_translation(
            HPEOutputTranslation(
                src_lang=Language(SRC_LANG),
                trg_lang=Language(TARGET_LANG),
                text_segments=updated_segment,
                user_dict=TEST_DICT, selected_dicts=[],
            ),
        )

        self.db_client.insert_or_update_text_segment(updated_translation)

    def create_dataset(self):
        print(f"test: {self._testMethodName}")
        self.db_client.export_text_segment_dataset(dataset_dir=DATASET_PATH)

        # Assert that 4 files have been created, one for each Dataset Key (SRC, MT, APE, HPE)
        self.assertEqual(4, len(os.listdir(DATASET_PATH)))

        # Cleanup
        shutil.rmtree(DATASET_PATH)

    def create_partial_dataset(self):
        self.db_client.export_text_segment_dataset(dataset_dir=DATASET_PATH, options=DatasetOptions(keys=[DatasetKey.SRC]))
        self.db_client.export_text_segment_dataset(dataset_dir=DATASET_PATH, options=DatasetOptions(keys=[DatasetKey.MT]))

        # Assert that 2 files have been created, one for each given Dataset Key (SRC, MT)
        self.assertEqual(2, len(os.listdir(DATASET_PATH)))

        # Cleanup
        shutil.rmtree(DATASET_PATH)
