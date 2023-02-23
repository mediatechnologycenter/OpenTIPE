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

from abc import abstractmethod

from mtc_api_utils.base_model import MLBaseModel

from mtc_ape_web_editor.api_types.translations import MTInputTranslation, MTOutputTranslation


class MTModel(MLBaseModel):

    def __init__(self, pretrained_model_name: str, gpu_enabled: bool = False):
        self.pretrained_model_name = pretrained_model_name
        self.gpu_enabled = gpu_enabled

        super().__init__()

    @abstractmethod
    def init_model(self):
        pass

    @abstractmethod
    def inference(self, translation: MTInputTranslation) -> MTOutputTranslation:
        pass
