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

"""
This module is used to generically initiate our APIs by downloading artifacts from the artifact repository. Its functions can be called either at
image build time or at startup time.
"""

import tarfile
from os import error, makedirs, path, remove
from pathlib import Path
from typing import Tuple

import requests


def stem_tar_filename(file_path: str) -> str:
    return Path(file_path).stem.split('.')[0]


def artifact_exists(file_path: str, is_tar: bool = False) -> bool:
    if is_tar:
        base_dir = path.dirname(file_path)
        tar_exists = path.isdir(Path(base_dir, stem_tar_filename(file_path)))
        file_exists = path.isfile(file_path)
        if file_exists:
            print("file already exists...")
        if tar_exists:
            print("tar file already exists...")
        return file_exists or tar_exists
    else:
        return path.isfile(file_path)


def download_artifact(artifact_url: str, file_path: str, auth: Tuple[str, str]) -> str:
    print("Downloading artifact {} to file_path {}".format(artifact_url, file_path))

    resp = requests.get(artifact_url, allow_redirects=True, auth=auth)
    resp.raise_for_status()  # Raise http error if one occurred
    with open(file_path, 'wb') as file:
        file.write(resp.content)

    return file_path


def download_artifact_with_progress(artifact_url: str, file_path: str, auth: Tuple[str, str]) -> str:
    print(f"Downloading artifact {artifact_url} to {file_path}")
    try:
        response = requests.get(artifact_url, allow_redirects=True, auth=auth, stream=True, timeout=None)
        response.raise_for_status()

        total_size_in_bytes = int(response.headers.get('content-length', 0))
        total_size_in_mb = (round(total_size_in_bytes / 10 ** 6))
        file_name = artifact_url.split("/")[-1]
        big_size_condition = total_size_in_bytes > 10 ** 9
        if big_size_condition:
            print(f"the download of the file {file_name} takes a while, grab a ☕ ...")
        artifact_name = stem_tar_filename(artifact_url)
        total_downloaded_bytes = 0
        with open(file_path, 'wb') as file:
            for data in response.iter_content(2 ** 27):
                if big_size_condition:
                    total_downloaded_bytes += len(data)
                    total_downloaded_mb = round(total_downloaded_bytes / 10 ** 6)
                    print(f"downloaded {total_downloaded_mb} / {total_size_in_mb} megabytes of file {artifact_name}")
                file.write(data)

    except Exception as e:
        print(e)
        raise error(e)

    return file_path


def unpack_tar_file(tar_filepath: str, download_dir: str) -> str:
    print(f"unpacking {tar_filepath} to {download_dir} ...")

    def track_progress(members):
        for member in members:
            print(f"extracting {member.name} ...")
            yield member

    with tarfile.open(f'{tar_filepath}', 'r') as tarball:
        tarball.extractall(path=f'{download_dir}', members=track_progress(tarball))

    if path.exists(tar_filepath):
        remove(tar_filepath)

    return stem_tar_filename(tar_filepath)


def download_if_not_exists(artifact_url: str, download_dir: str, auth: Tuple[str, str], is_tar: bool = False) -> str:
    """ Download a file if not exists (currently only supported for files)

    Attributes
    ----------
    artifact_url: the artifact url "<path-to-your-file>"

    download_dir: to this dir the file will be downloaded

    auth: tuple of (usr, pwd)

    is_tar: if tar is active a tar file will be downloaded and unpacked

    """
    # If path does not exist (vol not attached), create it
    if not path.exists(download_dir):
        makedirs(download_dir)

    # Expect dir, not file
    if path.isfile(download_dir):
        raise error("Expect download_dir to be a directory: {}".format(download_dir))

    file_name = artifact_url.split("/")[-1]
    file_path = path.join(download_dir, file_name)

    if is_tar:
        extracted_dir_name = file_path.split(".tar")[0]
        if artifact_exists(extracted_dir_name, is_tar=True):
            return extracted_dir_name

        else:
            download_artifact_with_progress(artifact_url, file_path, auth)
            unpack_tar_file(file_path, download_dir)
            return extracted_dir_name
    else:
        if artifact_exists(file_path):
            return file_path
        else:
            return download_artifact(artifact_url, file_path, auth)
