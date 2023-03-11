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

import os
from http import HTTPStatus
from typing import Dict, List

from fastapi import HTTPException
from mtc_api_utils.base_model import MLBaseModel

from mtc_ape_api.config import ApeConfig
from mtc_ape_model.translator import APETranslator
from mtc_ape_web_editor.api_types.api_types import Language, TermDict
from mtc_ape_web_editor.api_types.translations import MTOutputTranslation, APEOutputTranslation


class ApeModel(MLBaseModel):

    def __init__(self):
        self.dictionaries: Dict[str, TermDict] = {}
        self.ape_translators: Dict[str, APETranslator] = {}

        super().__init__()

    def init_model(self) -> None:
        for i, lang_pair in enumerate(ApeConfig.language_pairs):
            print(f"Initializing model {i + 1}/{len(ApeConfig.language_pairs)}: {lang_pair} \n")

            model_dir = f"{ApeConfig.model_path}/{ApeConfig.model_name(lang_pair)}"

            for model_file in ApeConfig.model_files:
                model_path = os.path.join(model_dir, model_file)

                if not os.path.isfile(model_path):
                    raise RuntimeError(f"Unable to find required file {model_file}. Make sure it is available under the model path: {model_dir}")

            self.ape_translators[lang_pair] = APETranslator(model_path=model_dir, gpu=ApeConfig.gpu, verbose=True)

        self.init_dictionaries()

        print("Initialization complete, model is available")

    def init_dictionaries(self) -> None:
        print(f"Initializing dictionaries: {ApeConfig.dictionaries}")
        for dictionary in ApeConfig.dictionaries:
            dict_path = f"{ApeConfig.dictionary_dir}/{dictionary}.csv"

            if not os.path.isfile(dict_path):
                raise RuntimeError(f"Unable to find required file {dictionary}. Make sure it is available under the model path: {ApeConfig.dictionary_dir}")

            self.dictionaries[dictionary] = TermDict.from_csv(dict_path)

            if not ApeConfig.enable_n_to_n_dicts:
                self.dictionaries[dictionary] = self.dictionaries[dictionary].filter_n_to_n_entries()

    def inference(self, translation: MTOutputTranslation) -> APEOutputTranslation:
        # Assert selected dicts are valid
        translation.raise_for_invalid_dicts(ApeConfig.dictionaries)

        # APE Inference
        src_segments, mt_segments = zip(*[(segment.src_text, segment.mt_text) for segment in translation.text_segments])

        # Prepare dicts
        merged_dict = translation.merged_dicts(self.dictionaries)

        language_pair = Language.pair(translation.src_lang, translation.trg_lang)

        try:
            translator = self.ape_translators[language_pair]
        except KeyError:
            raise HTTPException(detail=f"Language pair [{language_pair}] is not available", status_code=HTTPStatus.UNPROCESSABLE_ENTITY)

        pe_segments: List[str] = translator.post_edit(
            src=src_segments,
            mt=mt_segments,
            terminology_dict=merged_dict
        )

        output_segments = [
            textSegment.add_text(ape_text=pe_segment)
            for textSegment, pe_segment
            in zip(translation.text_segments, pe_segments)
        ]

        translation_output = translation.with_segments(segments=output_segments)

        print(f"translation_output: {translation_output}")

        return translation_output
