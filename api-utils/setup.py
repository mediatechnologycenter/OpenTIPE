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

from distutils.core import setup

setup(
    name='mtc_api_utils',
    version='0.4.0',
    description='Commonly used MTC API utils',
    url='https://gitlab.ethz.ch/mtc/libraries/api-utils',
    author="Media Technology Center (ETH Zürich)",
    author_email='mtc@ethz.ch',
    package_data={
        "mtc_api_utils": ["py.typed"],
    },
    packages=[
        "mtc_api_utils",
        "mtc_api_utils.cli_wrappers",
        "mtc_api_utils.clients",
    ],
    install_requires=[
        "fastapi>=0.78.0",
        "uvicorn>=0.20.0",
        "gunicorn>=20.1.0",
        "python-multipart>=0.0.5",
        "debugpy>=1.6.3",
        "requests>=2.28.1",
        "types-requests>=2.28.11.7",
        "firebase_admin>=6.0.1",
        "httpx>=0.23.1",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        'Intended Audience :: Science/Research',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ]
)
