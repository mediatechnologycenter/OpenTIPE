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

""" Data sampler, data collator and tokenize methods. """

from dataclasses import dataclass
from transformers.tokenization_utils_base import BatchEncoding

from transformers.file_utils import PaddingStrategy
from typing import Union, Optional, Any
from ..data.tokenizer import Seq2SeqTokenizer

@dataclass
class DataCollatorForSeq2Seq:
    """ Data collator that will dynamically pad the inputs received,
    as well as the labels. """

    tokenizer: Seq2SeqTokenizer
    padding: Union[bool, str, PaddingStrategy] = True
    label_pad_token_id: int = -100
    max_length: Optional[int] = None
    pad_to_multiple_of: Optional[int] = None
    return_tensors: str = "pt"

    def __call__(self, features, return_tensors=None):

        if return_tensors is None:
            return_tensors = self.return_tensors
        
        # If we have a list of dicts, let's convert it in a dict of lists
        # We do this to allow using this method as a collate_fn function 
        # in PyTorch Dataloader
        if isinstance(features, (list, tuple)) and isinstance(
                features[0], (dict, BatchEncoding)):
            features = {key: [example[key] for example in features]
                for key in features[0].keys()} 

        if self.padding:
            return self.tokenizer.pad(features, max_length=self.max_length, 
                pad_to_multiple_of=self.pad_to_multiple_of,
                return_tensors=return_tensors, padding=self.padding)
        else:
            return features