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

from mtc_ape_api.models.ape_model import ApeModel
from mtc_ape_web_editor.api_types.hard_coded_responses import mock_ape_output_with_id
from mtc_ape_web_editor.api_types.translations import APEOutputTranslation, MTOutputTranslation


class MockApeModel(ApeModel):

    def __init__(self, hard_coded_response: bool = False):
        self.hard_coded_response = hard_coded_response

        super().__init__()

    def init_model(self):
        print(
            f"Initializing MockApeModel with hard_coded_response={self.hard_coded_response}.\nThis model is only meant to showcase the demo application and does not perform any actual AutomaticPostEditing")

    def inference(self, translation: MTOutputTranslation) -> APEOutputTranslation:
        if self.hard_coded_response:
            mock_mt = mock_ape_output_with_id(translation_id=translation.id)

            for mock_segment, input_segment in zip(mock_mt.text_segments, translation.text_segments):
                mock_segment.id = input_segment.id

            return mock_mt

        else:
            # The following line sets ape_text = mt_text
            return translation.with_segments(segments=[segment.add_text(ape_text=segment.mt_text) for segment in translation.text_segments])
