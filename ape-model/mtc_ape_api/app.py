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

import uvicorn
from fastapi import Depends
from mtc_api_utils.api import BaseApi
from mtc_api_utils.clients.firebase_client import firebase_user_auth
from mtc_api_utils.debug import initialize_api_debugger

from mtc_ape_api.config import ApeConfig
from mtc_ape_api.models.ape_model import ApeModel
from mtc_ape_api.models.mock_ape_model import MockApeModel
from mtc_ape_web_editor.api_types.translations import MTOutputTranslation, APEOutputTranslation

ApeConfig.print_config()

ape_model = MockApeModel(hard_coded_response=ApeConfig.hard_coded_response) if ApeConfig.mock_model else ApeModel()

if ApeConfig.debug and ApeConfig.debug_port is not None:
    initialize_api_debugger(ApeConfig.debug_port)

user_auth = firebase_user_auth(config=ApeConfig)


def print_if_debug(message):
    if ApeConfig.debug:
        print(message)


# Init app
api = BaseApi(is_ready=ape_model.is_ready, config=ApeConfig)


@api.post(
    "/translate",
    dependencies=[Depends(user_auth.with_roles(ApeConfig.required_roles))],
    response_model=APEOutputTranslation,
    response_model_exclude_none=True,  # skip None attributes in Translation object
)
def translate(translation: MTOutputTranslation) -> APEOutputTranslation:
    """
    Expects a body of type api_types.Translation
    """
    return ape_model.inference(translation=translation)


print('API server is listening on {}'.format(ApeConfig.ape_backend_url))

if __name__ == '__main__':
    uvicorn.run(api, host='0.0.0.0', port=5000, log_level="info")
