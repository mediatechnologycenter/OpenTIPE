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

from typing import List
from mtc_api_utils.config import Config


class ApeConfig(Config):
    # Model configs
    model_dir_url: str = Config.parse_env_var("APE_MODEL_URL_DIR")
    model_path: str = "/app/models"

    mock_model: bool = Config.parse_env_var("MOCK_MODEL", default="False", convert_type=bool)
    hard_coded_response: bool = Config.parse_env_var("HARD_CODED_RESPONSE", default="False", convert_type=bool)

    model_files = [
        "vocab.txt",
        "tokenizer_config.json",
        "pytorch_model.bin",
        "special_tokens_map.json",
        "config.json",
        "run_config.json"
    ]

    language_pairs: List[str] = Config.parse_env_var("LANGUAGE_PAIRS", convert_type=list)

    # Dictionaries configs
    dictionary_dir: str = Config.parse_env_var("DICTIONARY_DIR", default="/dictionaries")
    dictionary_repo_url: str = Config.parse_env_var(
        env_var_name="DICTIONARY_REPO_URL"
    )
    dictionaries: List[str] = Config.parse_env_var("DICTIONARIES", convert_type=list)
    enable_n_to_n_dicts: bool = Config.parse_env_var("ENABLE_N_TO_N_DICTS", default="False", convert_type=bool)

    # API configs
    ape_backend_url: str = Config.parse_env_var("APE_BACKEND_URL")

    # Auth configs
    required_roles: List[str] = Config.parse_env_var("REQUIRED_AUTH_ROLES", "ape", convert_type=list)

    # Deployment configs
    gpu: int = Config.parse_env_var("GPU", default="-1", convert_type=int)

    @staticmethod
    def model_name(language_pair: str):
        return f"ape-model-huggingface-{language_pair}"
