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
from typing import List

from mtc_api_utils.config import Config
from mtc_mt_api.config import MTModelLibrary


class BackendConfig(Config):
    # Model configs
    mt_model: MTModelLibrary = Config.parse_env_var("MT_MODEL_LIBRARY", default="DeepL", convert_type=MTModelLibrary)
    language_pairs: list[str] = Config.parse_env_var("LANGUAGE_PAIRS", convert_type=list)

    # Dictionaries configs
    dictionaries: List[str] = Config.parse_env_var("DICTIONARIES", convert_type=list)

    # API configs
    backend_url: str = Config.parse_env_var("BACKEND_URL")
    mt_backend_url: str = Config.parse_env_var("MT_BACKEND_URL")
    ape_backend_url: str = Config.parse_env_var("APE_BACKEND_URL")
    db_connection_string: str = Config.parse_env_var("DB_CONNECTION_STRING")

    deepl_api_url: str = Config.parse_env_var("DEEPL_API_URL", default="https://api-free.deepl.com/v2/translate")
    deepl_api_key: str = Config.parse_env_var("DEEPL_API_KEY")

    # Miscellaneous configs
    dataset_path = Config.parse_env_var("DATASET_PATH", default="/data/datasets")
