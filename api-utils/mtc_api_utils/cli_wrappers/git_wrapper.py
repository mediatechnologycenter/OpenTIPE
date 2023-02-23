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

import os
import re
from datetime import datetime
from subprocess import CompletedProcess

from mtc_api_utils.cli_wrappers.base_cli_wrapper import BaseCLIWrapper, Executable


class GitWrapper(BaseCLIWrapper):

    def __init__(self, repo_base_path: str = "/tmp/gitRepos"):
        self.repo_base_path = repo_base_path

    def get_full_repo_path(self, repo_url) -> str:
        regex = re.search(r".*/([\d\w\-_]*)(?:\.git)?", repo_url)
        full_repo_path = os.path.join(self.repo_base_path, regex.group(1))
        return full_repo_path

    def clone_repository(self, repo_url: str, branch: str) -> CompletedProcess:
        try:
            os.makedirs(name=self.repo_base_path, exist_ok=True)
        except FileExistsError:
            pass

        # Clone repository
        return self._run_git_command(
            full_repo_path=self.repo_base_path,
            args=[
                "clone",
                "-b",
                branch,
                repo_url
            ],
        )

    def pull_repository(self, full_repo_path: str) -> CompletedProcess:
        # Reset repo in case any other application made changes
        self._run_git_command(
            full_repo_path=full_repo_path,
            args=["reset", "--hard"],
        )

        # Pull branch
        return self._run_git_command(
            full_repo_path=full_repo_path,
            args=["pull", "--ff-only"],
        )

    def clone_or_pull_repository(self, repo_url: str, branch: str) -> bool:
        """
        If repository does not exist, clone repository and return False
        If repository already exists, pull repository and return True
        """
        try:
            os.makedirs(name=self.repo_base_path, exist_ok=True)
        except FileExistsError:
            pass

        full_repo_path = self.get_full_repo_path(repo_url)

        if os.path.isdir(full_repo_path):
            """Repo dir exists -> Pull repo"""
            self.pull_repository(full_repo_path=full_repo_path)

            return True

        else:
            """Repo dir does not exist -> Clone repo"""
            self.clone_repository(repo_url=repo_url, branch=branch)

            return False

    def get_commit_hash(self, full_repo_path: str) -> str:
        """Returns the short commit hash of the latest commit in the repository specified by the repo path"""
        process = self._run_git_command(full_repo_path=full_repo_path, args=["rev-parse", "--short", "HEAD"])
        return process.stdout.decode("utf-8").strip()

    def get_commit_date(self, full_repo_path: str) -> datetime:
        process = self._run_git_command(full_repo_path=full_repo_path, args=["show", "-s", "--format=%cI"])
        date_string = process.stdout.decode("utf-8").strip()
        return datetime.fromisoformat(date_string)

    def _run_git_command(self, full_repo_path: str, args: list[str]) -> CompletedProcess:
        return self._run_command(
            executable=Executable.git,
            args=[
                "-C",
                full_repo_path,
                *args
            ]
        )
