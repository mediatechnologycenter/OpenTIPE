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

""" Preprocessing methods. """

import numpy as np
from transformers import AutoTokenizer

# If the following is changed MyEncoderBertEmbeddings in bert_encoder.py
# has to be adapted. Namely at the place within the forward where we
# compute the position of the second "MT" part
SRC_FACTOR = 0
SRC_ORIGINAL_FACTOR = 2
SRC_MT_FACTOR = 3
MT_FACTOR = 1

def tokenize(string, terminology_term="~", terminology_method=None,
        module="encoder", tokenizer=None):

    if terminology_method:
        
        if module == "encoder":
            # Input sentences
            if tokenizer.sep_token in string:
                src_A, src_B = string.split(tokenizer.sep_token)  # SRC
                src_A, src_B = src_A.strip(), src_B.strip()
                factors_b = [MT_FACTOR] * len(src_B.split(" "))  # MT
            else:
                src_A = string
                factors_b = []
                
            words = src_A.split(" ")
            counts = [word.count(terminology_term) for word in words]

            def count_to_factors(count):
                if count == 0:
                    return [SRC_FACTOR]
                if count > 0:
                    if terminology_method == "append":
                        return [SRC_ORIGINAL_FACTOR] + [SRC_MT_FACTOR] * (count)
                    else:
                        return [SRC_MT_FACTOR] * (count)

            factors_a = [count_to_factors(cnt)  for cnt in counts]
            factors_a = [i for j in factors_a for i in j]
            factors = factors_a + [SRC_FACTOR] + factors_b
        else:
            # Output sentences
            factors = [MT_FACTOR] * len(string.split(" "))  # APE

        # Prepare string
        words = string.split(" ")
        if terminology_method == "replace":
            words = [(word[word.find(terminology_term)+1:] if
                (terminology_term in word) else word) for word in words]
        words = [word.split(terminology_term) for word in words]
        words = [i for j in words for i in j]
        string = " ".join(words)

    token_ids = tokenizer(*string.split(tokenizer.sep_token),
        truncation=False, padding=False)
    tokens = tokenizer.convert_ids_to_tokens(token_ids['input_ids'])
    
    # Adapt the factors to the splitting of the words
    if terminology_method and module == "encoder":
        factor_ptr = -1
        factors_tokenized = []
        sep_passed=False

        for token in tokens:

            if token in [tokenizer.sep_token, tokenizer.cls_token,
                tokenizer.pad_token, tokenizer.mask_token]:
                factors_tokenized.append((MT_FACTOR if sep_passed else 
                        SRC_FACTOR) if module == "encoder" else MT_FACTOR)
                if token == tokenizer.sep_token:
                    if not sep_passed:
                        factor_ptr += 1
                    sep_passed = True
                continue

            if token[:2] == "##":
                factors_tokenized.append(factors[factor_ptr])
            else:
                factor_ptr += 1
                factors_tokenized.append(factors[factor_ptr])

        assert(factor_ptr == len(factors)-1)
        segments_ids = factors_tokenized
        assert(len(tokens) == len(segments_ids))
    
    else:

        if tokenizer.sep_token in tokens[:-1]:
            src_A, src_B = ' '.join(tokens).split(tokenizer.sep_token, 1)
            src_A, src_B = src_A.strip(), src_B.strip()
            segments_ids = [SRC_FACTOR] * (len(src_A.split()) + 1) + \
                [MT_FACTOR] * len(src_B.split())
        else:

            # Differentiation in case of standard MT
            segments_ids = [SRC_FACTOR if module=="encoder" else MT_FACTOR] \
                * len(tokens)

    token_ids['factor_ids'] = segments_ids
    assert(len(token_ids['input_ids']) == len(token_ids['attention_mask']) \
        and len(token_ids['input_ids']) == len(token_ids['token_type_ids'])\
        and len(token_ids['input_ids']) == len(token_ids['factor_ids']) \
        and len(tokens) == len(segments_ids))
    
    return token_ids

class Seq2SeqTokenizer():

    def __init__(self, base_tokenizer, terminology_method, terminology_term,
            loss_ignore_label_id=-100):
        
        self.base_tokenizer = base_tokenizer
        self.loss_ignore_label_id = loss_ignore_label_id
        base_tokenizer.init_kwargs["terminology_method"] = terminology_method
        base_tokenizer.init_kwargs["terminology_term"] = terminology_term
        base_tokenizer.init_kwargs["loss_ignore_label_id"]= loss_ignore_label_id

    @classmethod
    def from_pretrained(cls, pretrained_model_name_or_path, 
            terminology_method=None, terminology_term=None,
            loss_ignore_label_id=None):

        # Use AutoTokenizer to retreive the tokenizer
        base_tokenizer = \
            AutoTokenizer.from_pretrained(pretrained_model_name_or_path,
                use_fast=False, do_basic_tokenize=False)

        # Get default if nothing is provided
        terminology_method = (terminology_method if terminology_method else
            base_tokenizer.init_kwargs["terminology_method"])
        terminology_term = (terminology_term if terminology_term else
            base_tokenizer.init_kwargs["terminology_term"])
        loss_ignore_label_id = (loss_ignore_label_id if loss_ignore_label_id
            else base_tokenizer.init_kwargs["loss_ignore_label_id"])

        return cls(base_tokenizer, terminology_method=terminology_method,
            terminology_term=terminology_term,
            loss_ignore_label_id=loss_ignore_label_id)

    def tokenize(self, example):

        encoder_inp = (example['src'], example['mt']) if ('mt' in example) \
            else (example['src'],)

        tokenized = tokenize(
            f" {self.base_tokenizer.sep_token} ".join(encoder_inp), 
            terminology_term=
                self.base_tokenizer.init_kwargs["terminology_term"],
            terminology_method=
                self.base_tokenizer.init_kwargs["terminology_method"],
            module="encoder", tokenizer=self.base_tokenizer)

        if "pe" in example:
            decoder_input_ids = tokenize(example['pe'], terminology_term=
                    self.base_tokenizer.init_kwargs["terminology_term"],
                terminology_method=
                    self.base_tokenizer.init_kwargs["terminology_method"], 
                module="decoder", tokenizer=self.base_tokenizer)

            decoder_input_ids = {("decoder_" + k): v for k, v in
                decoder_input_ids.items()}

            tokenized.update(decoder_input_ids)

            tokenized["labels"] = decoder_input_ids["decoder_input_ids"].copy()
            tokenized["labels"] = \
                [self.base_tokenizer.init_kwargs["loss_ignore_label_id"] if
                token == self.base_tokenizer.pad_token_id else token
                for token in tokenized["labels"]]

        if "decoder_token_type_ids" in tokenized:
            tokenized["decoder_token_type_ids"] = \
                [MT_FACTOR] * len(tokenized["decoder_token_type_ids"])

        return tokenized

    def pad(self, features, max_length=None, pad_to_multiple_of=None,
            return_tensors="pt", padding=True):

        # Pad all entries that are not per default padded by tokenizer
        if 'labels' in features:
            features['labels'] = self._pad(features['labels'], pad_to_multiple_of)
        if 'token_type_ids' in features:
            features['token_type_ids_tmp'] = features['token_type_ids']
        if 'decoder_token_type_ids' in features: 
            features['decoder_token_type_ids_tmp'] = \
                features['decoder_token_type_ids']
        for i in ['factor_ids', 'decoder_factor_ids', 'token_type_ids_tmp',
                'decoder_token_type_ids_tmp']:
            if i in features:
                features[i] = self._pad(features[i], pad_to_multiple_of,
                    pad_token=[min(1, i[-1]) for i in features[i]])

        # Pad remaining entries with tokenizer
        padded_features = self.base_tokenizer.pad(
            {k: v for k, v in features.items() if "decoder_" != k[:8]},
            padding=padding,
            max_length=max_length,
            pad_to_multiple_of=pad_to_multiple_of,
            return_tensors=return_tensors)

        decoder_features = {}
        if any("decoder_" in i for i in features):
            decoder_features = self.base_tokenizer.pad(
                {k[8:]: v for k, v in features.items() if "decoder_" == k[:8]},
                padding=padding,
                max_length=max_length,
                pad_to_multiple_of=pad_to_multiple_of,
                return_tensors=return_tensors)
            decoder_features = {"decoder_" + k: v for k,v in
                decoder_features.items()}

        # Replace standard token type id padding by custom one
        if 'token_type_ids_tmp' in padded_features:
            padded_features['token_type_ids'] = \
                padded_features['token_type_ids_tmp']
            del padded_features['token_type_ids_tmp']

        if 'decoder_token_type_ids_tmp' in decoder_features:
            decoder_features['decoder_token_type_ids'] = \
                decoder_features['decoder_token_type_ids_tmp']
            del decoder_features['decoder_token_type_ids_tmp']

        return {**padded_features, **decoder_features}

    def _pad(self, list_to_pad, pad_to_multiple_of, pad_token=None):
        """ Pads a list of lists/arrays/tensors with pad_token. """
        padding_side = self.base_tokenizer.padding_side
        el_len = [len(i) for i in list_to_pad]
        max_len = max(el_len)
        if pad_token is None:
            pad_token= self.loss_ignore_label_id

        # Allows for padding of multiples of an int
        if pad_to_multiple_of:
            if max_len % pad_to_multiple_of != 0:
                max_len += (pad_to_multiple_of - 
                    (max_len % pad_to_multiple_of))

        # Pad length for each element
        pad_len = [max_len-i for i in el_len]

        # Internal pad method
        def _pad_helper(el, pad_len, tok):
            rem = [tok] * pad_len
            if isinstance(el, list):
                return el + rem if padding_side == "right" else rem + el
            elif padding_side == "right":
                return np.concatenate([el, rem]).astype(np.int64)
            else:
                return np.concatenate([rem, el]).astype(np.int64)
        
        # Pad
        if type(pad_token) != list:
            pad_token = [pad_token] * len(list_to_pad)   
        return [_pad_helper(el, p, t) for el, p, t in
            zip(list_to_pad, pad_len, pad_token)]