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

import csv
import uuid
from enum import Enum
from typing import Dict, List

from mtc_api_utils.api_types import ApiType


class EventLogType(Enum):
    value: str

    idle_event = 'IdleEvent',
    active_event = 'ActiveEvent',
    accept_event = 'AcceptEvent',
    reject_event = 'RejectEvent',
    copy_event = 'CopyEvent',


class UserEvent(ApiType):
    event: str
    userEmail: str
    timestamp: str


def generate_id() -> str:
    return str(uuid.uuid4())


class Language(Enum):
    DE = "de"
    EN = "en"
    FR = "fr"

    @classmethod
    def _missing_(cls, value: str):
        # make enum case-insensitive
        for lang in cls:
            if value.lower() == lang.value:
                return lang

    @staticmethod
    def pair(src_lang: Language, trg_lang: Language) -> str:
        return f"{src_lang.value}-{trg_lang.value}"


class TermDict(dict):
    @staticmethod
    def from_csv(path: str):
        dictionary = {}

        with open(path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header

            for row in reader:
                dictionary[row[0]] = row[1]

        return TermDict(dictionary)

    def merge_dict(self, user_dict: Dict):
        self.update(user_dict)
        return self

    @classmethod
    def from_dicts(cls, dicts: List[Dict]):
        merged = {}
        for d in dicts:
            merged.update(d)

        return TermDict(merged)

    def filter_n_to_n_entries(self):
        filtered_dict = {key: value for key, value in self.items() if " " not in key and " " not in value}
        return TermDict(filtered_dict)
