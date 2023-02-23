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

from abc import ABC, abstractmethod

from mtc_api_utils.api_types import ApiType
from pydantic import Field

from mtc_ape_web_editor.api_types.api_types import generate_id


class TextSegment(ApiType, ABC):
    id: str = Field(default_factory=generate_id, alias="_id")
    src_text: str = Field(example="Dies ist ein Beispielsatz.", alias="srcText")

    @staticmethod
    @abstractmethod
    def example() -> TextSegment:
        pass

    @abstractmethod
    def get_printable_representation(self) -> str:
        pass


class TextSegmentMTInput(TextSegment):

    @staticmethod
    def example() -> TextSegmentMTInput:
        return TextSegmentMTInput(
            src_text="Dies ist ein Beispielsatz.",
        )

    def get_printable_representation(self) -> str:
        return f"src_text: {self.src_text}"

    def add_text(self, mt_text: str) -> TextSegmentMTOutput:
        return TextSegmentMTOutput(
            id=self.id,
            src_text=self.src_text,
            mt_text=mt_text,
        )


class TextSegmentMTOutput(TextSegmentMTInput):
    mt_text: str = Field(example="Voici une phrase d'exemple.", alias="mtText")  # Not required for translation request

    @staticmethod
    def example() -> TextSegmentMTOutput:
        return TextSegmentMTInput.example().add_text(mt_text="Voici une phrase d'exemple.")

    def add_text(self, ape_text: str) -> TextSegmentAPEOutput:
        return TextSegmentAPEOutput(
            id=self.id,
            src_text=self.src_text,
            mt_text=self.mt_text,
            ape_text=ape_text,
        )

    def get_printable_representation(self) -> str:
        return f"src_text: {self.src_text}\n  mt_text: {self.mt_text}"


class TextSegmentAPEOutput(TextSegmentMTOutput):
    ape_text: str = Field(example="Ceci est une phrase d'exemple.", alias="apeText")  # Not required for translation request

    @staticmethod
    def example() -> TextSegmentAPEOutput:
        return TextSegmentMTOutput.example().add_text(ape_text="Ceci est une phrase d'exemple.")

    def add_text(self, hpe_text: str) -> TextSegmentHPE:
        return TextSegmentHPE(
            id=self.id,
            src_text=self.src_text,
            mt_text=self.mt_text,
            ape_text=self.ape_text,
            hpe_text=hpe_text,
        )

    def get_printable_representation(self) -> str:
        return f"src_text: {self.src_text}\n  mt_text: {self.mt_text}\n  ape_text: {self.ape_text}"


class TextSegmentHPE(TextSegmentAPEOutput):
    hpe_text: str = Field(example="Ceci est une phrase d'exemple.", alias="hpeText")  # Not required for translation request

    @staticmethod
    def example() -> TextSegmentHPE:
        return TextSegmentAPEOutput.example().add_text(hpe_text="Ceci est une phrase d'exemple.")

    def get_printable_representation(self) -> str:
        return f"src_text: {self.src_text}\n  mt_text: {self.mt_text}\n  ape_text: {self.ape_text}\n  hpe_text: {self.hpe_text}"
