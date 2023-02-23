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

import json
import torch
import logging
import multiprocessing as mp
from typing import Any, List, Dict

from math import ceil
from sacremoses import MosesTokenizer, MosesDetokenizer

def read_lines(file_name):
    with open(file_name, 'r', encoding='utf8') as file:
        lines = file.readlines()
    return [line[:-1] for line in lines]

def write_lines(lines, file_name):
    with open(file_name, 'w', encoding='utf8') as file:
        file.write(lines[0])
        for line in lines[1:]:
            file.write('\n' + line)

def join_lines(src_lines, mt_lines):
    joined_lines = []
    for i in range(len(src_lines)):
        joined_lines.append(src_lines[i] + ' [SEP] ' + 
            mt_lines[i])
    return joined_lines

def async_func(func, ind, *args):
    return (ind, func(*args))

def multiprocess_map(func, inputs, processes=4):
    """ Multiprocess map method """
    input_length = -1
    for i in inputs:
        if type(i) == list:
            input_length = len(i)
    assert(input_length != 1), "At least one input needs to be a list."
    processes = min(input_length, processes)
    batch_size = ceil(input_length/processes)
    pool = mp.Pool(processes=processes)
    results = [pool.apply_async(async_func,
        args=(func, i, *([(inputs[j][i*batch_size:(i+1)*batch_size] if
            type(inputs[j]) == list else inputs[j])
            for j in range(len(inputs))]))) 
        for i in range(processes)]
    results = [p.get() for p in results]
    results.sort()
    return [j for i in results for j in i[1]]
    
def tokenize(batch_lines, language, ind=None, aggressive_dash_splits=True,
        tokenizer=None):
    """ Tokenizes by words. """
    if tokenizer is None:
        tokenizer = MosesTokenizer(language.lower())
    tokenized_lines = []
    for line in batch_lines:
        tokenized_line = tokenizer.tokenize(line,
            aggressive_dash_splits=aggressive_dash_splits)
        tokenized_line = ' '.join(tokenized_line)
        tokenized_lines.append(tokenized_line)
    return tokenized_lines if ind is None else (ind, tokenized_lines)

def multiprocess_tokenize(lines, language, processes=4,
        aggressive_dash_splits=True):
    """ Tokenizes by words using several processes. """
    return multiprocess_map(tokenize, (lines, language, None,
        aggressive_dash_splits), processes=processes)

def reverse_word_split(lines):
    return [line.replace(' ##', '') for line in lines]

def detokenize(batch_lines, language, ind=None, detokenizer=None):
    if detokenizer is None:
        detokenizer = MosesDetokenizer(language.lower())
    detokenized_lines = []
    for line in batch_lines:
        detokenized_line = line.split(" ")
        detokenized_line = detokenizer.detokenize(detokenized_line)
        detokenized_lines.append(detokenized_line)
    return detokenized_lines if ind is None else (ind, detokenized_lines)

def multiprocess_detokenize(lines, language, processes=4):
    """ Deokenizes by words using several processes. """
    return multiprocess_map(detokenize, (lines, language, None),
        processes=processes)

def dict_to_file(dictionnary: Dict[str, Any], info: str = "validation metrics", 
        file_path: str = "validation_metrics.txt", as_json: bool = True,
        logger: logging.RootLogger = None):
    """ Stores metrics to file and writes them to logger.
    
    Parameters
    ----------
    dictionnary:
        Mapping (name to value) to store.
    info:
        Information used in the logging.
    file_name:
        Name of the file to dump the metrics to.
    as_json:
        Whether to dump to file as json.
    logger:
        A logger. If provided the metrics are in addition of being written to a
        file also printed in the log.
    """
    # To file
    with open(file_path, "w") as file:
        if as_json:
            file.write(json.dumps(dictionnary, indent=4, sort_keys=True))
        else:
            for key, value in sorted(dictionnary.items()):
                file.write(f"{key} = {value}\n")

    # Log
    if logger:
        logger.info(f"***** {info} *****")
        for key, value in sorted(dictionnary.items()):
            logger.info(f"  {key} = {value}")

def lines_to_file(lines: List, info: str = "predictions", 
        file_path: str = "predictions.txt",
        logger: logging.RootLogger = None):
    """ Stores metrics to file and writes them to logger.
    
    Parameters
    ----------
    lines:
        List of strings to write to file.
    info:
        Information used in the logging.
    file_name:
        Name of the file to dump the metrics to.
    as_json:
        Whether to dump to file as json.
    logger:
        A logger. If provided the metrics are in addition of being written to a
        file also printed in the log.
    """
    # To file
    with open(file_path, "w") as file:
        for line in lines:
            file.write(line+"\n")

    # Log
    if logger:
        logger.info(f"***** {info} *****")
        for line in lines:
            logger.info(line)


def validate_state_dicts(model_state_dict_1, model_state_dict_2):
    """ Compares the weights of two model of same architecture with help of 
    their state dicts and returns which layeers match and which ones not. """

    if len(model_state_dict_1) != len(model_state_dict_2):
        print(
            f"Length mismatch: {len(model_state_dict_1)}, "
            f"{len(model_state_dict_2)}"
        )
        return False

    # Replicate modules have "module" attached to their keys, so 
    # strip these off when comparing to local model.
    if next(iter(model_state_dict_1.keys())).startswith("module"):
        model_state_dict_1 = {
            k[len("module") + 1 :]: v for k, v in model_state_dict_1.items()
        }

    if next(iter(model_state_dict_2.keys())).startswith("module"):
        model_state_dict_2 = {
            k[len("module") + 1 :]: v for k, v in model_state_dict_2.items()
        }

    missmatches = []
    no_missmatch = []
    for ((k_1, v_1), (_, v_2)) in zip(
        model_state_dict_1.items(), model_state_dict_2.items()):  

        # Convert both to the same CUDA device
        if str(v_1.device) != "cuda:0":
            v_1 = v_1.to("cuda:0" if torch.cuda.is_available() else "cpu")
        if str(v_2.device) != "cuda:0":
            v_2 = v_2.to("cuda:0" if torch.cuda.is_available() else "cpu")

        if not torch.allclose(v_1, v_2):
            missmatches.append(k_1)
        else:
            no_missmatch.append(k_1)

    return missmatches, no_missmatch