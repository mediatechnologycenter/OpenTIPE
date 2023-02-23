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

import os.path
from datetime import datetime
from enum import Enum
from http import HTTPStatus
from typing import Dict, List, Optional, Union, Any, Mapping

from fastapi import HTTPException
from mtc_api_utils.api_types import ApiType
from pydantic import Field
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from pymongo.mongo_client import MongoClient
from pymongo.results import UpdateResult, InsertOneResult

from mtc_ape_web_editor.api_types.api_types import UserEvent, generate_id
from mtc_ape_web_editor.api_types.text_segments import TextSegmentHPE, TextSegment
from mtc_ape_web_editor.api_types.translations import HPEOutputTranslation


# TODO:
#  - Support batched creation for large datasets
#  - Support storing dataset on remote blob store

class DatasetKey(Enum):
    value: str

    SRC = "srcText"
    MT = "mtText"
    APE = "apeText"
    HPE = "hpeText"


class DatasetLanguages(Enum):
    value: str

    DE = "DE"
    EN = "EN"
    FR = "FR"
    ALL = "ANY"


class DatasetOptions(ApiType):
    """
    Specifies options with which to create a Dataset
    :attr keys: Per default, create Dataset for all keys. If passed, only create a subset at a time.
                This can be beneficial if the Dataset is very large and available memory is limited.
    """

    src_lang: DatasetLanguages = DatasetLanguages.ALL
    trg_lang: DatasetLanguages = DatasetLanguages.ALL
    keys: List[DatasetKey] = [k for k in DatasetKey]


Dataset = Mapping[str, Any]


def get_filter(text_segment: TextSegment):
    return {
        id: text_segment.id
    }


class DbTextSegment(TextSegmentHPE):
    dictionary: Optional[Dict] = Field(alias="dict")
    last_modified: datetime = Field(default_factory=datetime.now, alias="lastModified")

    @staticmethod
    def example() -> DbTextSegment:
        return DbTextSegment.from_text_segment(TextSegmentHPE.example(), dictionary={})

    def get_printable_representation(self) -> str:
        return f"src_text: {self.src_text}\n  mt_text: {self.mt_text}\n  ape_text: {self.ape_text}\n  hpe_text: {self.hpe_text}"

    @staticmethod
    def from_text_segment(text_segment: TextSegmentHPE, dictionary: Dict):
        segment_id = text_segment.id if text_segment.id else generate_id()

        return DbTextSegment(
            id=segment_id,
            src_text=text_segment.src_text,
            mt_text=text_segment.mt_text,
            ape_text=text_segment.ape_text,
            hpe_text=text_segment.hpe_text,
            dictionary=dictionary,
        )


class DbTranslation(HPEOutputTranslation):
    text_segments: List[DbTextSegment] = Field(example=[DbTextSegment.example()], alias="textSegments")

    @staticmethod
    def from_hpe_translation(translation: HPEOutputTranslation) -> DbTranslation:
        return DbTranslation(
            id=translation.id,
            src_lang=translation.src_lang,
            trg_lang=translation.trg_lang,
            text_segments=[
                DbTextSegment.from_text_segment(text_segment=segment, dictionary=translation.user_dict)
                for segment
                in translation.text_segments
            ],
            user_dict=translation.user_dict,
            selected_dicts=translation.selected_dicts,
            ape_accepted=translation.ape_accepted,
        )


class MongoDBClient:

    def __init__(
            self,
            connection_string: str,
            translation_db_name: str = "translations_db",
            translations_collection_name: str = "translations",
            events_db_name: str = "events_db",
            events_collection_name: str = "events",
            server_connection_timeout_seconds: int = 2,
    ):
        self.db_client = MongoClient(connection_string, serverSelectionTimeoutMS=server_connection_timeout_seconds * 1000)

        # Translations
        self.translations_db_name = translation_db_name
        self.translations_collection_name = translations_collection_name
        self.translations = self.db_client[translation_db_name][translations_collection_name]

        # Events
        self.events_db_name = events_db_name
        self.events_collection_name = events_collection_name
        self.events = self.db_client[events_db_name][events_collection_name]

    def get_liveness(self) -> bool:
        try:
            self.db_client["admin"].command('ping')
            return True
        except ConnectionFailure:
            return False

    def insert_or_update_text_segment(self, translation: DbTranslation) -> Union[UpdateResult, InsertOneResult]:
        """
        Persists the TextSegments of a Translation in the database
        """

        # Try to insert new translation
        try:
            print(f"inserted translation dict: {translation.json_dict}")
            return self.translations.insert_one(translation.json_dict)

        # If translation ID already exists, update its TextSegments instead
        except DuplicateKeyError:
            bulk = self.translations.initialize_ordered_bulk_op()

            # Add segment updates to bulk operation
            for segment in translation.text_segments:
                bulk.find({"$and": [{"_id": translation.id},
                                    {"textSegments._id": segment.id}
                                    ]}) \
                    .upsert() \
                    .update_one({"$set": {"textSegments.$": segment.json_dict}})

            bulk.find({"_id": translation.id}) \
                .update_one({"$set": {"dict": translation.json_dict}})

            return bulk.execute()

    def export_text_segment_dataset(self, dataset_dir: str, options: DatasetOptions = DatasetOptions()) -> Dataset:
        """
        Exports a dataset from the db to a file and returns metadata that can be used to retrieve it.
        Excludes any textSegment that does not have a full set of keys (srcText, mtText, apeText, hpeText)

        :param options: An options object specifying the parameters for the generated Dataset
        :param dataset_dir: The base directory in which to store dataset files
        :return:
            - True if the dataset was created successfully, False otherwise
            - A Dataset object specifying how to access the created Dataset. None if not successful
        """

        # Helper functions
        def push_segment_keys(key: DatasetKey) -> Dict:
            return {
                "$push": f"$textSegments.{key.value}"
            }

        def reduce_segment_keys(key: DatasetKey) -> Dict:
            return {
                "$reduce": {
                    "input": f"${key.value}",
                    "initialValue": "",
                    "in": {
                        "$concat": [
                            "$$value", "\n", "$$this"
                        ]
                    }
                }
            }

        def trim_keys(key: DatasetKey) -> Dict:
            return {
                "$ltrim": {
                    "input": f"${key.value}"
                }
            }

        # Create query dynamically
        unwind_segment_keys = {"path": "$textSegments", "includeArrayIndex": "_id", "preserveNullAndEmptyArrays": True}

        filter_all_keys_exist = {f"textSegments.{key.value}": {"$exists": True} for key in options.keys}

        group_segment_texts = {key.value: push_segment_keys(key) for key in options.keys}
        group_segment_texts["_id"] = "result"

        concat_segment_texts = {key.value: reduce_segment_keys(key) for key in options.keys}

        trim_result_texts = {key.value: trim_keys(key) for key in options.keys}
        trim_result_texts["_id"] = "result"

        aggregation = self.translations.aggregate([
            {"$unwind": unwind_segment_keys},
            {"$match": filter_all_keys_exist},
            {"$group": group_segment_texts},
            {"$project": concat_segment_texts},
            {"$project": trim_result_texts},
        ])

        try:
            dataset = list(aggregation)[0]
        except IndexError as e:
            message = f"MongoDB query did not return any results: \n{e}"
            print(message)
            print(f"aggregation: {list(aggregation)}")
            raise HTTPException(detail=message, status_code=HTTPStatus.NOT_FOUND)

        # Create dir & save files
        os.makedirs(dataset_dir, exist_ok=True)

        for key in options.keys:
            file_name = f"dataset-{options.src_lang.name}-to-{options.trg_lang.name}-{key.name}.txt"
            file_path = os.path.join(dataset_dir, file_name)

            print(f"Saving dataset file for {key.name} to {file_path}")
            with open(file_path, "w") as file:
                file.write(dataset[key.value])

        return dataset

    def insert_event(self, event: UserEvent) -> InsertOneResult:
        return self.events.insert_one(event.json_dict)

    def get_events(self) -> List[UserEvent]:
        # DEBUG:
        print(f"{self.db_client[self.events_db_name][self.events_collection_name].count_documents({})=}")
        print(f"{self.db_client[self.events_db_name][self.events_collection_name].find({})=}")

        return [UserEvent.parse_obj(event) for event in self.events.find({})]
