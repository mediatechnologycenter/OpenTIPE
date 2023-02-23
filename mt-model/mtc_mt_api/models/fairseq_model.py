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

import re
from typing import Any

import torch

from mtc_ape_web_editor.api_types.translations import MTInputTranslation, MTOutputTranslation
from mtc_mt_api.models.abstract_mt_model import MTModel


class FairseqModel(MTModel):
    model: Any

    def init_model(self):
        # Fairseq repo changed their primary branch from "master" to "main" from version 16..
        try:
            pattern = re.compile("wmt([0-9]*)")
            version = int(pattern.search(self.pretrained_model_name).group(1))
        except Exception as e:
            print(e)
            raise RuntimeError(f"MT_MODEL_NAME={self.pretrained_model_name} is invalid.")

        if version < 19:
            self.model = torch.hub.load(repo_or_dir=f"pytorch/fairseq:main",
                                        model=self.pretrained_model_name,
                                        tokenizer="moses",
                                        bpe="subword_nmt")

        else:
            self.model = torch.hub.load(repo_or_dir=f"pytorch/fairseq:main",
                                        model=self.pretrained_model_name,
                                        tokenizer="moses",
                                        bpe="fastBPE")

        self.model.eval()  # Disable dropout in evaluation mode

        if self.gpu_enabled:
            self.model.cuda()

    def inference(self, translation: MTInputTranslation) -> MTOutputTranslation:
        src_segments = [segment.src_text for segment in translation.text_segments]
        translated_segments = self.model.inference(src_segments)

        output_segments = [
            segment.add_text(mt_text=tr_segment)
            for segment, tr_segment
            in zip(translation.text_segments, translated_segments)
        ]

        output_translation = translation.with_segments(output_segments)

        return output_translation
