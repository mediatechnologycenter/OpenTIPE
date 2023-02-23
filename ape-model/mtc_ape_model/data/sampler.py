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

import numpy as np
from typing import Any

class BatchLengthGroupedSampler():

    def __init__(self, sampler, train_batch_size: int = 4,
            token_batching: bool = False, batch_size_includes_padding=True):
        
        self.sampler = sampler
        self.train_batch_size = train_batch_size
        self.token_batching = token_batching
        self.batch_size_includes_padding = batch_size_includes_padding
        self.batches = None
        self.length = None
        self.lengths = sampler.lengths
        assert('decoder_length' in sampler.dataset.features), \
            "No decoder lengths in dataset"
        self.decoder_lengths = sampler.dataset['decoder_length']

        # Precompute
        self.batches = self._make_batches(sampler, train_batch_size,
            token_batching, batch_size_includes_padding)
        self.length = len(self.batches)

    def __len__(self):
        
        if self.length:
            self.length = sum(1 for _ in iter(self))
            return self.length
        else:
            return self.length
    
    def __iter__(self):

        if self.batches:
            return iter(self.batches)
        else:
            self.batches = iter(self._make_batches(self.sampler,
                self.train_batch_size, self.token_batching,
                self.batch_size_includes_padding))
            return self.batches


    def _make_batches(self, sampler, train_batch_size: int = 4,
            token_batching: bool = False, batch_size_includes_padding=True):
        
        batches = []

        if not token_batching:
            
            batch = []
            for sample in sampler:
                batch.append(sample)
                if len(batch) == train_batch_size:
                    batches.append(batch)
                    batch = []
                    
            if len(batch) != 0:
                batches.append(batch)
        else:

            indices = list(iter(sampler))
            enc_lens = np.array(self.lengths)[indices]
            dec_lens = np.array(self.decoder_lengths)[indices]

            if batch_size_includes_padding:
                
                batch = []
                max_enc_len = 0
                max_dec_len = 0
                els = 0

                for enc_l, dec_l, sample in zip(enc_lens, dec_lens, indices):
                    
                    if enc_l + dec_l > train_batch_size:
                        continue # Ignore

                    elif max(max_enc_len, enc_l)*(els+1) + \
                            max(max_dec_len, dec_l)*(els+1) <= train_batch_size:
                        batch.append(sample)
                        max_enc_len = max(max_enc_len, enc_l)
                        max_dec_len = max(max_dec_len, dec_l)
                        els += 1
                    else:
                        batches.append(batch)
                        batch = [sample]
                        max_enc_len = enc_l
                        max_dec_len = dec_l
                        els = 1
                        
                if len(batch) != 0:
                    batches.append(batch)
                    
            else:
                
                batch = []
                curr_len = 0
                for enc_l, dec_l, sample in zip(enc_lens, dec_lens, sampler):
                    l = enc_l + dec_l
                    if l > train_batch_size:
                        continue # Ignore
                    elif l + curr_len <= train_batch_size:
                        batch.append(sample)
                        curr_len += l
                    else:
                        batches.append(batch)
                        batch = [sample]
                        curr_len = l
                        
                if len(batch) != 0:
                    batches.append(batch)

        return batches      