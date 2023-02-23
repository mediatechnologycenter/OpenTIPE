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

# This config script is supposed to be used in order to pass environment variables set by docker &/ local
# environments to python applications. Required environment variables can be definded as instance variables using
# os.getenv(). The constructor then asserts that all required variables have been provided.
import inspect
import logging
import os
from time import tzset, tzname
from typing import Any, Callable, TypeVar, Dict, List

from mtc_api_utils.api_types import AuthenticationRole

_T = TypeVar("_T")

uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.disabled = True
uvicorn_access_logger.propagate = False

os.environ['TZ'] = 'Europe/Zurich'
tzset()

print(f"Timezone set to {tzname}")


class ConfigBuilder:
    @staticmethod
    def parse_env_var(env_var_name: str, default: str = None, convert_type: _T = None, transformation: Callable[[Any], _T] = None) -> _T:
        """
        Reads an environment variable, parses it and performs error handling
        :param env_var_name: The env variable to be read
        :param default: The default value for the env variable if it is not defined
        :param convert_type: A type
        """
        val: str = os.getenv(env_var_name)

        if val is None:
            if default is None:
                raise ValueError(
                    f"{env_var_name} environment variable not defined."
                    f"Make sure to specify all environment variables in your .env file and EXPORT any env variables passed from your host system")
            else:
                val = default

        if convert_type is not None:
            if convert_type == bool:
                return ConfigBuilder.parse_bool(val)

            elif convert_type == list:
                try:
                    return ConfigBuilder.parse_list(val)
                except Exception as e:
                    print(
                        f"Environment variable transformation failed for {env_var_name}:")
                    raise e

            # Converts the file
            else:
                try:
                    val = convert_type(val)
                except Exception as e:
                    print(
                        f"Environment variable transformation failed for {env_var_name}:")
                    raise e

        if transformation is not None:
            try:
                val = transformation(val)
            except Exception as e:
                print(
                    f"Environment variable transformation failed for {env_var_name}:")
                raise e

        return val

    @staticmethod
    def parse_bool(bool_string: str) -> bool:
        if bool_string.lower() in ["True", "true"]:
            return True
        elif bool_string.lower() in ["False", "false"]:
            return False
        else:
            raise ValueError(
                f"{bool_string} could not be parsed to boolean value")

    @staticmethod
    def parse_list(list_string: str):
        if len(list_string) == 0:
            return []
        else:
            return [string.strip() for string in list_string.split(',') if string]


class Config(ConfigBuilder):
    """
    Provides required environment variables to configure the application

    Example usage:
        # In config.py file:
            from mtc_api_utils.config import Config

            class APIConfig(Config):
                gpu = os.getenv("GPU", default=gpu)
                backend_url = os.getenv("BACKEND_URL", default=backend_url)

        # In module using config:
            from config import APIConfig

            APIConfig.backend_url
    """

    # Init global vars

    # Deployment
    gpu_supported = ConfigBuilder.parse_env_var("GPU_SUPPORTED", convert_type=bool)
    gpu_enabled = ConfigBuilder.parse_env_var("GPU_ENABLED", convert_type=bool)
    backend_url: str = ConfigBuilder.parse_env_var("BACKEND_URL", default="http://localhost:5000")

    # Auth
    cors_allow_origins: List[str] = ConfigBuilder.parse_env_var("CORS_ALLOW_ORIGINS", convert_type=list, default="")
    auth_enabled: bool = ConfigBuilder.parse_env_var("AUTH_ENABLED", convert_type=bool, default="True")

    # Firebase
    # Required for firebase auth verification
    firebase_auth_service_account_url = ConfigBuilder.parse_env_var(
        "FIREBASE_AUTH_SERVICE_ACCOUNT_CREDENTIALS_URL",
    )
    service_account_dir: str = ConfigBuilder.parse_env_var(env_var_name="SERVICE_ACCOUNT_DIR", default="/tmp/gcloud")

    required_roles: List[str] = ConfigBuilder.parse_env_var(
        "REQUIRED_AUTH_ROLES",
        default=f"",
        convert_type=list
    )
    required_roles.append(AuthenticationRole.admin.value)
    required_roles.append(AuthenticationRole.viewer.value)

    # Debug
    debug = ConfigBuilder.parse_env_var("DEBUG", default="False", convert_type=bool)
    debug_port = ConfigBuilder.parse_env_var("DEBUG_PORT", default="5050")

    @classmethod
    def get_env_variables(cls) -> Dict[str, Any]:
        """Returns a list of all ENV variables"""

        attributes = inspect.getmembers(
            cls,
            lambda a: not inspect.isroutine(a),
        )

        return {
            key: value
            for key, value
            in attributes
            if not key.startswith('_')
        }

    @classmethod
    def print_config(cls) -> None:
        print("Config values:")
        for attr, value in cls.get_env_variables().items():
            print("{}: {}".format(attr, value))
