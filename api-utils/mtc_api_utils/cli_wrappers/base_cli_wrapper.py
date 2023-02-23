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


import subprocess
from enum import Enum
from typing import List


class Executable(Enum):
    value: str
    git = "git"
    helm = "helm"
    kubectl = "kubectl"


class CLIWrapperException(Exception):
    """
    Exception raised by an MTC CLIWrapper
    """

    @property
    def error(self) -> str:
        return str(self)


class BaseCLIWrapper:

    @classmethod
    def _run_command(cls, executable: Executable, args: List[str], working_dir: str = None) -> subprocess.CompletedProcess:
        full_args = [
            executable.value,
            *args,
        ]

        # print(f"Running the following command: {' '.join(full_args)}")  # DEBUG log
        try:
            completed_process = subprocess.run(
                args=full_args,
                check=True,
                cwd=working_dir,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise CLIWrapperException(e.stderr.decode("utf-8"))

        return completed_process
