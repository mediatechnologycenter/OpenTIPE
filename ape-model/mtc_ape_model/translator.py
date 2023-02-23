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
Methods and classes for inference via API.
"""
from typing import Dict, List, Optional

import os
from sacremoses import MosesDetokenizer, MosesTokenizer
from tqdm import tqdm

from .data.terminology import TerminologyProcessor
from .data.tokenizer import Seq2SeqTokenizer
from .models.factor_model import FactorEncoderDecoderModel
from .utils.misc import detokenize, tokenize
from .utils.parser import APEParser
from .utils.arguments import APEDataArguments


class APETranslator:

    def __init__(self, model_path: str, gpu: int = -1, src_lang="de",
                 tgt_lang="en", verbose: bool = False, default_dict=None):
        """
        Parameters
        ----------
        model_path:
            Path to the model
        gpu:
            GPU to use, if -1 CPU is used for translation.
        languages:
            List of languages used.
        verbose:
            Whether to print additional infos during translation.
        """
        self.model_path = model_path
        self.gpu = gpu
        self.verbose = verbose
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.src_max_len, self.terminology_method, self.terminology_term = \
            self.determine_data_format(model_path)
        self.model = FactorEncoderDecoderModel.from_pretrained(model_path)
        self.tokenizer = Seq2SeqTokenizer.from_pretrained(model_path,
            terminology_method=self.terminology_method,
            terminology_term=self.terminology_term)
        self.white_space_tokenizer_src = MosesTokenizer(self.src_lang)
        self.white_space_tokenizer_mt = MosesTokenizer(self.tgt_lang)
        self.white_space_detokenizer = MosesDetokenizer(self.tgt_lang)
        self.terminology_processor = TerminologyProcessor(src_lang=src_lang,
            tgt_lang=tgt_lang, default_dict=default_dict,
            requires_word_alignment=False)
        if self.gpu > -1:
            self.model = self.model.to(f'cuda:{self.gpu}')

    def determine_data_format(model_path: str, file_name = "run_config.json"):
        try:
            hf_parser = APEParser((APEDataArguments,))
            data_args, _ = hf_parser.parse_args_into_dataclasses_with_default(
                    return_remaining_strings=True, json_default_files=
                    os.path.join(model_path, file_name))
            src_max_len = data_args.src_max_len
            terminology_method = data_args.terminology_method
            terminology_term = data_args.terminology_term
        except:
            src_max_len = 250
            terminology_method = None
            terminology_term = "~"
        return src_max_len, terminology_method, terminology_term

    def post_edit(self, src: List[str], mt: List[str],
            terminology_dict: Optional[Dict] = None, use_default_dict=True,
            batch_size=5, whitespace_tokenize=True, whitespace_detokenize=True,
            aggressive_dash_splits=True):
        """ Post edit src-mt tuples. """

        batches = len(src) // batch_size
        if batches * batch_size < len(src):
            batches += 1

        # White space tokenize
        if whitespace_tokenize:
            src = tokenize(src, self.src_lang,
                tokenizer=self.white_space_tokenizer_src,
                aggressive_dash_splits=aggressive_dash_splits)
            mt = tokenize(mt, self.tgt_lang,
                tokenizer=self.white_space_tokenizer_mt,
                aggressive_dash_splits=aggressive_dash_splits)

        # Encode terminology
        src = self.terminology_processor.encode_from_dict(src,
            term_dict=terminology_dict, use_default_dict=use_default_dict)

        preds = []
        for i in tqdm(range(batches), desc="Translation"):
            # Take batch
            src_batch = src[i * batch_size: (i + 1) * batch_size]
            mt_batch = mt[i * batch_size: (i + 1) * batch_size]

            # Word piece tokenize and pad
            tok_inp = []
            for s, m in zip(src_batch, mt_batch):
                tok_inp.append(self.tokenizer.tokenize({"src": s, "mt": m}))
                if len(tok_inp[-1]["input_ids"]) > self.src_max_len:
                    print("Model was not trained on sentences of this length.")

            batch = {k: [tok[k] for tok in tok_inp] for k in tok_inp[0].keys()}
            batch = self.tokenizer.pad(batch)

            # Map to gpu if necessary
            if self.gpu > -1:
                batch = {k: v.to(f"cuda:{self.gpu}") for k, v in batch.items()}

            # Generate prediction(s)
            outputs = self.model.generate(batch["input_ids"],
                attention_mask=batch["attention_mask"],
                token_type_ids=batch["token_type_ids"],
                position_ids=batch["factor_ids"],
                decoder_start_token_id=self.model.config.decoder_start_token_id,
                max_length=200,
                num_beams=4)

            # Word piece detokenize
            pred = self.tokenizer.base_tokenizer.batch_decode(outputs.tolist(),
                skip_special_tokens=True, clean_up_tokenization_spaces=False)
            
            # White space detokenize
            if whitespace_detokenize:
                preds.append(detokenize(pred, self.tgt_lang,
                    detokenizer=self.white_space_detokenizer))
            else:
                preds.append(pred)

        return [i for j in preds for i in j]
