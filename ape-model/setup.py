#!/usr/bin/env python

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
    name="mtc_ape_api",
    description="A python implementation of Automatic Post Editing (APE) based on OpenNMT",
    version="0.3.0",
    url="https://gitlab.ethz.ch/mtc/machine-translation/ape-model",
    author="Media Technology Center (ETH Zürich)",
    author_email="mtc@ethz.ch",
    packages=["mtc_ape_api"],
    install_requires=[
        "mtc_api_utils @ git+https://github.com/mediatechnologycenter/api-utils.git",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ]
)
