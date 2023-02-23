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
from __future__ import annotations

from abc import ABC
from http import HTTPStatus
from typing import List, Optional, Dict

from fastapi import HTTPException
from mtc_ape_web_editor.api_types.api_types import Language, generate_id, TermDict
from mtc_ape_web_editor.api_types.text_segments import TextSegment, TextSegmentMTInput, TextSegmentMTOutput, TextSegmentAPEOutput, TextSegmentHPE
from mtc_api_utils.api_types import ApiType
from pydantic import Field


class Translation(ApiType, ABC):
    id: Optional[str] = Field(default_factory=generate_id, alias="_id")

    src_lang: Language = Field(example=Language.DE, alias="srcLang")
    trg_lang: Language = Field(example=Language.FR, alias="trgLang")
    # TODO: Use dynamic example once it is clear how to do this
    text_segments: List[TextSegment] = Field(example=[TextSegment.example()], alias="textSegments")

    selected_dicts: Optional[List[str]] = Field(default=[], example=None, alias="selectedDicts")
    user_dict: Optional[Dict] = Field(default={}, example=None, alias="userDict")

    def get_printable_representation(self):
        return "".join([f"Segment {i}:\n{segment.get_printable_representation()}\n" for i, segment in enumerate(self.text_segments)])

    def raise_for_invalid_dicts(self, available_dicts: list[str]):
        if self.selected_dicts:
            for unrecognized_dicts in [selected_dict for selected_dict in self.selected_dicts if selected_dict not in available_dicts]:
                if unrecognized_dicts:
                    raise HTTPException(detail=f"selected_dicts contained unrecognized dictionaries: {unrecognized_dicts}", status_code=HTTPStatus.BAD_REQUEST)

    def merged_dicts(self, available_dicts: Dict[str, TermDict]):
        selected_dicts: List[Dict] = [available_dicts[d] for d in self.selected_dicts]
        selected_dicts.append(self.user_dict)

        return TermDict.from_dicts(selected_dicts)


class MTInputTranslation(Translation):
    text_segments: List[TextSegmentMTInput] = Field(example=[TextSegmentMTInput.example()], alias="textSegments")

    def with_segments(self, segments: List[TextSegmentMTOutput]) -> MTOutputTranslation:
        return MTOutputTranslation(
            id=self.id,
            src_lang=self.src_lang,
            trg_lang=self.trg_lang,
            text_segments=segments,
            selected_dicts=self.selected_dicts,
            user_dict=self.user_dict,
        )


class MTOutputTranslation(Translation):
    text_segments: List[TextSegmentMTOutput] = Field(example=[TextSegmentMTOutput.example()], alias="textSegments")

    def with_segments(self, segments: List[TextSegmentAPEOutput]) -> APEOutputTranslation:
        return APEOutputTranslation(
            id=self.id,
            src_lang=self.src_lang,
            trg_lang=self.trg_lang,
            text_segments=segments,
            selected_dicts=self.selected_dicts,
            user_dict=self.user_dict,
        )


class APEOutputTranslation(Translation):
    text_segments: List[TextSegmentAPEOutput] = Field(example=[TextSegmentAPEOutput.example()], alias="textSegments")

    def with_segments(self, segments: List[TextSegmentHPE]) -> HPEOutputTranslation:
        return HPEOutputTranslation(
            id=self.id,
            src_lang=self.src_lang,
            trg_lang=self.trg_lang,
            text_segments=segments,
            selected_dicts=self.selected_dicts,
            user_dict=self.user_dict,
        )


class HPEOutputTranslation(Translation):
    text_segments: List[TextSegmentHPE] = Field(example=[TextSegmentHPE.example()], alias="textSegments")

    ape_accepted: Optional[bool] = Field(default=None, example=None, alias="apeAccepted")  # Not required for translation request
