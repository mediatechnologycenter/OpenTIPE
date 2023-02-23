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

""" APE dataset. """

import os
import datasets
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = datasets.logging.get_logger(__name__)

_CITATION = """ TODO """
_DESCRIPTION = """ TODO """
HOMEPAGE = "TODO"

BASE_PATH = "../../data/"
SEED = 2021

@dataclass
class APEConfig(datasets.BuilderConfig):

    terminology_method: Optional[str] = None
    terminology_term: str = "~"

    src_lang="fr"
    tgt_lang="en"

    train_prefix = "train"
    dev_prefix = "dev"
    test_prefix = "test"
    src_suffix = ".src"
    mt_suffix = ".mt"
    pe_suffix = ".pe"

    terminology_dir = None
    max_samples = None
    src_max_len = 250
    tgt_max_len = 200
    loss_ignore_label_id = -100

    _id_counter: int = 0

@dataclass
class APEDatasetInfo(datasets.info.DatasetInfo):
    terminology_term: str = "~"
class APE(datasets.GeneratorBasedBuilder):

    BUILDER_CONFIG_CLASS = APEConfig
    APE = APEConfig(name="ape")
    MT = APEConfig(name="mt")
    APE_TEST = APEConfig(name="ape_test")
    MT_TEST = APEConfig(name="mt_test")
    BUILDER_CONFIGS = [APE, MT, APE_TEST, MT_TEST]

    def _info(self):
        """ Sets the own info based on self.config.name. """

        assert(self.config.data_dir), "Please specify data path."

        if "ape" in self.config.name:
            return datasets.DatasetInfo(
                description=str({
                    "terminology_term": self.config.terminology_term,
                    "src_lang": self.config.src_lang,
                    "tgt_lang": self.config.tgt_lang
                }),
                features=datasets.Features(
                    {
                        "src": datasets.Value("string"),                                     
                        "mt": datasets.Value("string"),   
                        "pe": datasets.Value("string")
                    }
                ),
                homepage=HOMEPAGE,
                citation=_CITATION)

        elif "mt" in self.config.name:
            return datasets.DatasetInfo(
                description=str({
                    "terminology_term": self.config.terminology_term,
                    "src_lang": self.config.src_lang,
                    "tgt_lang": self.config.tgt_lang
                }),
                features=datasets.Features(
                    {
                        "src": datasets.Value("string"),   
                        "pe": datasets.Value("string")
                    }
                ),
                homepage=HOMEPAGE,
                citation=_CITATION)

    def _split_generators(self, dl_manager):
        """ Creates the different dataset split for train/validation/test. """
        
        train_paths = (self.config.train_prefix + self.config.src_suffix,
                       self.config.train_prefix + self.config.mt_suffix,
                       self.config.train_prefix + self.config.pe_suffix)

        dev_paths = (self.config.dev_prefix + self.config.src_suffix,
                     self.config.dev_prefix + self.config.mt_suffix,
                     self.config.dev_prefix + self.config.pe_suffix)

        test_paths = (self.config.test_prefix + self.config.src_suffix,
                      self.config.test_prefix + self.config.mt_suffix,
                      self.config.test_prefix + self.config.pe_suffix)
        
        return [
            datasets.SplitGenerator(name=datasets.Split.TRAIN,
                gen_kwargs={"paths": train_paths,
                "data_dir": self.config.data_dir}),
            datasets.SplitGenerator(name=datasets.Split.VALIDATION,
                gen_kwargs={"paths": dev_paths, 
                "data_dir": self.config.data_dir}),
            datasets.SplitGenerator(name=datasets.Split.TEST, 
                gen_kwargs={"paths": test_paths, 
                "data_dir": self.config.data_dir})
         ] + ([] if self.config.terminology_dir is None else [
             datasets.SplitGenerator(
                name=datasets.Split.VALIDATION._name + "_term",
                gen_kwargs={"paths": dev_paths, 
                "data_dir": self.config.terminology_dir}),
            datasets.SplitGenerator(
                name=datasets.Split.TEST._name + "_term", 
                gen_kwargs={"paths": test_paths, 
                "data_dir": self.config.terminology_dir})
         ])

    def _generate_examples(self, paths, data_dir):
        """ Yields samples """

        if "ape" in self.config.name:
            src = open(os.path.join(data_dir, paths[0]), "r")
            mt = open(os.path.join(data_dir, paths[1]), "r")
            ape = open(os.path.join(data_dir, paths[2]), "r")
        else:
            src = open(os.path.join(data_dir, paths[0]), "r")
            ape = open(os.path.join(data_dir, paths[2]), "r")

        data = zip(src, mt, ape) if "ape" in self.config.name else zip(src, ape)

        for i, example in enumerate(data):
            sample = dict()

            if "ape" in self.config.name:
                sample['src'] = example[0].strip()
                sample['mt'] = example[1].strip()
                sample['pe'] = example[2].strip()
                
            elif "mt" in self.config.name:
                sample['src'] = example[0].strip()
                sample['pe'] = example[1].strip()

            yield self.config._id_counter, sample
            self.config._id_counter += 1

            if "test" in self.config.name and i > 100:
                break
                
            if self.config.max_samples:
                if i >= self.config.max_samples:
                    break 