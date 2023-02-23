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

# Library imports
import threading
from http import HTTPStatus
from typing import Dict

import uvicorn
from fastapi import Depends, HTTPException
from mtc_api_utils.api import BaseApi
from mtc_api_utils.clients.firebase_client import firebase_user_auth
from mtc_api_utils.debug import initialize_api_debugger

from models.abstract_mt_model import MTModel
from models.fairseq_model import FairseqModel
from models.hugging_face_model import HuggingFaceModel
from mtc_ape_web_editor.api_types.api_types import Language
from mtc_ape_web_editor.api_types.translations import MTInputTranslation, MTOutputTranslation
from mtc_mt_api.config import MTConfig, MTModelLibrary
from mtc_mt_api.models.mock_mt_model import MockMTModel

MTConfig.print_config()

mt_models: Dict[str, MTModel] = {}

idle_message = f"MT_MODEL is {MTConfig.mt_model_library} -> mtc-mt-model not initialized"

if MTConfig.debug and MTConfig.debug_port is not None:
    initialize_api_debugger(MTConfig.debug_port)


def print_if_debug(message):
    if MTConfig.debug:
        print(message)


def init_models():
    global mt_models

    for i, lang_pair in enumerate(MTConfig.language_pairs):
        print(f"Initializing model {i + 1}/{len(MTConfig.language_pairs)}: {lang_pair} \n")

        if MTConfig.mock_model:
            mt_models[lang_pair] = MockMTModel(pretrained_model_name="MockModel", gpu_enabled=False, hard_coded_response=MTConfig.hard_coded_response)

        elif MTConfig.mt_model_library == MTModelLibrary.DeepL:
            print(idle_message)

        elif MTConfig.mt_model_library == MTModelLibrary.HuggingFace:
            mt_models[lang_pair] = HuggingFaceModel(
                pretrained_model_name=MTConfig.mt_model_name_prefixes[MTConfig.mt_model_library] + lang_pair,
                gpu_enabled=MTConfig.gpu >= 0,
            )

        elif MTConfig.mt_model_library == MTModelLibrary.FairSeq:
            mt_models[lang_pair] = FairseqModel(
                pretrained_model_name=MTConfig.mt_model_name_prefixes[MTConfig.mt_model_library] + lang_pair,
                gpu_enabled=MTConfig.gpu >= 0,
            )

    print("Initialization complete, models are ready")


# Init model
init_thread = threading.Thread(target=init_models, name="init")
init_thread.start()


def model_is_ready():
    if MTConfig.mt_model_library == MTModelLibrary.DeepL:
        print(idle_message)
    return len(mt_models) == len(MTConfig.language_pairs)


# Init app
app = BaseApi(is_ready=model_is_ready, config=MTConfig)
user_auth = firebase_user_auth(config=MTConfig)


@app.post(
    "/translate",
    dependencies=[Depends(user_auth.with_roles(MTConfig.required_roles))],
    response_model=MTOutputTranslation,
    response_model_exclude_none=True,  # skip None attributes in Translation object
)
def translate(translation: MTInputTranslation) -> MTOutputTranslation:
    """
    Expects a body of type api_types.Translation
    """

    lang_pair = Language.pair(translation.src_lang, translation.trg_lang)

    # MT Inference
    try:
        return mt_models[lang_pair].inference(translation)
    except KeyError as e:
        raise HTTPException(detail=f"Language pair [{lang_pair}] is not available", status_code=HTTPStatus.UNPROCESSABLE_ENTITY)


print('API server is listening on {}'.format(MTConfig.mt_backend_url))

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000, log_level="info")
