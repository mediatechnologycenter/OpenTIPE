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

from enum import Enum
from http import HTTPStatus
from typing import List

from fastapi import Depends
from mtc_api_utils.api import BaseApi
from mtc_api_utils.api_types import FirebaseUser
from mtc_api_utils.clients.firebase_client import firebase_user_auth
from mtc_api_utils.debug import initialize_api_debugger

from api_clients.api_client import TranslationClient
from mtc_ape_api.api_client import APEClient
from mtc_ape_web_editor.api_clients.deepl_client import DeeplClient
from mtc_ape_web_editor.api_clients.mongodb_client import DatasetOptions, MongoDBClient, Dataset, DbTranslation
from mtc_ape_web_editor.api_types.api_types import UserEvent
from mtc_ape_web_editor.api_types.translations import MTInputTranslation, APEOutputTranslation, HPEOutputTranslation
from mtc_ape_web_editor.config import BackendConfig
from mtc_mt_api.api_client import MTClient
from mtc_mt_api.config import MTModelLibrary

BackendConfig.print_config()

if BackendConfig.debug and BackendConfig.debug_port is not None:
    initialize_api_debugger(BackendConfig.debug_port)

# Clients
ape_client = APEClient(BackendConfig.ape_backend_url)
db_client = MongoDBClient(BackendConfig.db_connection_string)
mt_client: TranslationClient

if BackendConfig.mt_model == MTModelLibrary.DeepL:
    mt_client = DeeplClient(deepl_api_key=BackendConfig.deepl_api_key)
else:
    mt_client = MTClient(BackendConfig.mt_backend_url)


def models_are_ready():
    resp, ape_ready = ape_client.get_readiness()
    resp, mt_ready = mt_client.get_readiness()
    db_ready = db_client.get_liveness()

    all_ready = all([ape_ready, mt_ready, db_ready])
    print(f"readiness: {all_ready}")  # Debug print
    return all_ready


app = BaseApi(models_are_ready, config=BackendConfig)
user_auth = firebase_user_auth(config=BackendConfig)


class RouteTags(Enum):
    value: str

    translation = "Translation"
    dataset = "Dataset"
    events = "Events"


@app.post(
    "/api/translate",
    response_model=APEOutputTranslation,
    response_model_exclude_none=True,  # skip None attributes in Translation object
    tags=[RouteTags.translation.value],
)
def translate(
        translation: MTInputTranslation,
        user: FirebaseUser = Depends(user_auth.with_roles(BackendConfig.required_roles))) -> APEOutputTranslation:
    """
        Expects a Translation object as a body
        Calls the MT model to get an MT Translation, then calls the APE model to get and return an APE Translation
    """

    # Assert selected dicts are valid
    translation.raise_for_invalid_dicts(BackendConfig.dictionaries)

    # Machine Translation (MT)
    resp, mt_translation = mt_client.translate(translation, access_token=user.access_token if user else user)
    resp.raise_for_status()

    # Automatic Post Editing (APE)
    resp, ape_translation = ape_client.translate(mt_translation, access_token=user.access_token if user else user)
    resp.raise_for_status()

    return ape_translation


@app.post(
    "/api/post-edition",
    dependencies=[Depends(user_auth.with_roles(["admin"]))],
    response_model=str,
    response_model_exclude_none=True,  # skip None attributes in Translation object
    status_code=HTTPStatus.CREATED,
    tags=[RouteTags.translation.value],
)
def create_post_editing(translation: HPEOutputTranslation):
    """
        Expects a Translation object as a body
        Persists the received Translation in the DB
    """
    update_result = db_client.insert_or_update_text_segment(translation=DbTranslation.from_hpe_translation(translation))

    return "Translation successfully persisted"


@app.get(
    "/api/dataset",
    dependencies=[Depends(user_auth.with_roles(["admin"]))],
    response_model=Dataset,
    response_model_exclude_none=True,  # skip None attributes in Translation object
    tags=[RouteTags.dataset.value],
)
def get_dataset():
    # Specify Dataset creation options here
    options = DatasetOptions()

    dataset = db_client.export_text_segment_dataset(dataset_dir=BackendConfig.dataset_path, options=options)

    return dataset


@app.post(
    "/api/events",
    dependencies=[Depends(user_auth.with_roles(["admin"]))],
    response_model=str,
    response_model_exclude_none=True,  # skip None attributes in Translation object
    status_code=HTTPStatus.CREATED,
    tags=[RouteTags.events.value],
)
def log_event(user_event: UserEvent):
    db_client.insert_event(user_event)

    return f"Inserted {user_event.event} for user {user_event.userEmail}"


@app.get(
    "/api/events",
    dependencies=[Depends(user_auth.with_roles(["admin"]))],
    response_model=List[UserEvent],
    response_model_exclude_none=True,  # skip None attributes in Translation object
    tags=[RouteTags.events.value],
)
def get_events() -> List[UserEvent]:
    return db_client.get_events()
