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

from mtc_ape_web_editor.api_types.hard_coded_responses import mock_ape_output_with_id
from mtc_ape_web_editor.api_types.translations import MTInputTranslation, MTOutputTranslation
from mtc_mt_api.models.abstract_mt_model import MTModel


class MockMTModel(MTModel):

    def __init__(self, pretrained_model_name: str, gpu_enabled=False, hard_coded_response: bool = False):
        self.hard_coded_response = hard_coded_response

        super().__init__(pretrained_model_name=pretrained_model_name, gpu_enabled=gpu_enabled)

    def init_model(self):
        print(
            f"Initializing MockMTModel hard_coded_response={self.hard_coded_response}.\nThis model is only meant to showcase the demo application and does not perform any actual translation")

    def inference(self, translation: MTInputTranslation) -> MTOutputTranslation:
        if self.hard_coded_response:
            mock_mt = mock_ape_output_with_id(translation_id=translation.id)

            for mock_segment, input_segment in zip(mock_mt.text_segments, translation.text_segments):
                mock_segment.id = input_segment.id

            return MTOutputTranslation(**mock_mt.json_dict)

        else:
            # The following simply returns the src text as the translation
            return translation.with_segments(segments=[segment.add_text(mt_text=segment.src_text) for segment in translation.text_segments])
