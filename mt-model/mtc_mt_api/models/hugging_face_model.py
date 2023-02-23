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

from transformers.models.auto.modeling_auto import AutoModelForSeq2SeqLM
from transformers.models.auto.tokenization_auto import AutoTokenizer
from transformers.models.marian.modeling_marian import MarianMTModel
from transformers.models.marian.tokenization_marian import MarianTokenizer

from mtc_ape_web_editor.api_types.translations import MTInputTranslation, MTOutputTranslation
from mtc_mt_api.models.abstract_mt_model import MTModel


class HuggingFaceModel(MTModel):
    mt_tokenizer: MarianTokenizer
    mt_model: MarianMTModel

    def init_model(self):
        self.mt_tokenizer: MarianTokenizer = AutoTokenizer.from_pretrained(self.pretrained_model_name)
        self.mt_model: MarianMTModel = AutoModelForSeq2SeqLM.from_pretrained(self.pretrained_model_name)

        if self.gpu_enabled:
            self.mt_model = self.mt_model.cuda()

    def inference(self, translation: MTInputTranslation) -> MTOutputTranslation:
        batch = self.mt_tokenizer([segment.src_text for segment in translation.text_segments], padding="longest", return_tensors="pt")
        if self.gpu_enabled:
            batch = batch.to("cuda:0")

        tokenized = self.mt_model.generate(**batch)
        translated_segments = self.mt_tokenizer.batch_decode(tokenized, skip_special_tokens=True)

        assert len(translation.text_segments) == len(translated_segments)

        output_segments = [
            segment.add_text(mt_text=tr_segment)
            for segment, tr_segment
            in zip(translation.text_segments, translated_segments)
        ]

        output_translation = translation.with_segments(output_segments)

        return output_translation
