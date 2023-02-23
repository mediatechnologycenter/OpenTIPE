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

from enum import Enum
from typing import List, Dict

from mtc_api_utils.config import Config


class MTModelLibrary(Enum):
    DeepL = "DeepL"
    HuggingFace = "HuggingFace"
    FairSeq = "FairSeq"


class MTConfig(Config):
    # Model configs
    mt_model_library: MTModelLibrary = Config.parse_env_var("MT_MODEL_LIBRARY", default="DeepL", convert_type=MTModelLibrary)
    mt_model_name_prefixes: Dict[MTModelLibrary, str] = {
        MTModelLibrary.HuggingFace: "Helsinki-NLP/opus-mt-",
        MTModelLibrary.FairSeq: "transformer.wmt19.",
    }

    mock_model: bool = Config.parse_env_var("MOCK_MODEL", default="False", convert_type=bool)
    hard_coded_response: bool = Config.parse_env_var("HARD_CODED_RESPONSE", default="False", convert_type=bool)

    language_pairs: List[str] = Config.parse_env_var("LANGUAGE_PAIRS", convert_type=list)

    # API configs
    mt_backend_url: str = Config.parse_env_var("MT_BACKEND_URL")

    # Auth configs
    required_roles: List[str] = Config.parse_env_var("REQUIRED_AUTH_ROLES", default="ape", convert_type=list)

    # Deployment configs
    gpu: int = Config.parse_env_var("GPU", default="-1", convert_type=int)
