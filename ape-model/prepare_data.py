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

import os
import gc
import argparse

from sklearn.model_selection import train_test_split

from mtc_ape_model.utils.parser import APEParser
from mtc_ape_model.utils.arguments import APEPrepareData
from mtc_ape_model.utils.misc import (read_lines, write_lines,
    multiprocess_tokenize, multiprocess_detokenize, multiprocess_map)
from mtc_ape_model.data.terminology import TerminologyProcessor
from mtc_ape_model.utils.train_utils import save_config

# TODO Prov. fix
def clean_txt(strings):
    def _clean(string):
        string = string.replace("`", "'")
        to_remove = ['\x96', '\xad', '�', '\u200b']
        while any([(" " + i + " ") in string for i in to_remove]):
            for i in to_remove:
                string = string.replace((" " + i + " "), " ")
        if any([(i+ " ") in string for i in to_remove]):
            for i in to_remove:
                string = string.replace((i + " "), "")
        if any([(" " + i) in string for i in to_remove]):
            for i in to_remove:
                string = string.replace((" " + i), "")
        return string
    return [_clean(i) for i in strings]

def prepare_data(src, mt, pe, save_dir, word_tokenize, aggressive_dash_splits,
        processes, terminology_encode, use_lemma, min_sentence_threshold,
        max_sentence_threshold, alignments, batch_size, source_language,
        target_language, dev_test_size, test_size, text_min_length, mt_only,
        cli_args, config_paths, clean):

    source_sentences_file_name = src
    machine_translated_sentences_file_name = mt
    post_edited_sentences_file_name = pe
    source_language = source_language
    target_language = target_language
    dev_test_size = dev_test_size
    test_size = test_size

    print("Reading files and filtering...")
    src_lines = read_lines(source_sentences_file_name)
    mt_lines = read_lines(machine_translated_sentences_file_name)
    pe_lines = read_lines(post_edited_sentences_file_name)

    if clean:
        print("Cleaning...")
        src_lines = multiprocess_map(clean_txt,(src_lines,),processes=processes)
        mt_lines = multiprocess_map(clean_txt, (mt_lines,), processes=processes)
        pe_lines = multiprocess_map(clean_txt, (pe_lines,), processes=processes)

    remove_lines = set([ind for ind, triple in 
        enumerate(zip(src_lines, mt_lines, pe_lines)) if 
            any([len(i) < text_min_length for i in triple])])

    src_lines = [i for ind,i in enumerate(src_lines) if ind not in remove_lines]
    mt_lines = [i for ind,i in enumerate(mt_lines) if ind not in remove_lines]
    pe_lines = [i for ind,i in enumerate(pe_lines) if ind not in remove_lines]
    
    if word_tokenize or terminology_encode:
        print("Tokenizing...")
        src_lines = multiprocess_tokenize(src_lines, source_language, processes, 
            aggressive_dash_splits)
        mt_lines = multiprocess_tokenize(mt_lines, target_language, processes,
            aggressive_dash_splits)
        pe_lines = multiprocess_tokenize(pe_lines, target_language, processes,
            aggressive_dash_splits)
        gc.collect()

    if terminology_encode and not mt_only:
        print("Terminology encoding...")
        # assert(word_tokenize), "Word tokenize required for dict encode."
        processor = TerminologyProcessor(src_lang=source_language,
            tgt_lang = target_language, sentence_annotation_threshold=
            (min_sentence_threshold, max_sentence_threshold),
            use_lemma=use_lemma)
        
        if alignments is None:
            alignment_lines = None
        else:
            if os.path.isfile(alignments):
                alignment_lines = []
                with open(alignments, "r") as file:
                    for line in file:
                        current = []
                        for alignment in line.split(" "):
                            current.append(tuple([int(el.strip())
                                for el in alignment.split("-")]))
                        alignment_lines.append(current)
            else:
                alignment_lines = processor.get_alignments(src_lines, pe_lines)
                with open(alignments, "w") as file:
                    for alignment in alignment_lines:
                        file.write(" ".join([str(el[0]) + "-" + str(el[1])
                            for el in alignment])+ "\n")

        src_lines = processor.encode_lines(src_lines, pe_lines, alignment_lines,
            batch_size) 

    if not word_tokenize and terminology_encode:
        print("Detokenizing...")
        src_lines=multiprocess_detokenize(src_lines, source_language, processes)
        mt_lines = multiprocess_detokenize(mt_lines, target_language, processes)
        pe_lines = multiprocess_detokenize(pe_lines, target_language, processes)
        gc.collect()

    train_src_lines, dev_test_src_lines, train_pe_lines, dev_test_pe_lines = \
        train_test_split(src_lines, pe_lines, test_size=dev_test_size, 
            random_state=42)

    dev_src_lines, test_src_lines, dev_pe_lines, test_pe_lines = \
        train_test_split(dev_test_src_lines, dev_test_pe_lines,
            test_size=test_size, random_state=42)

    train_mt_lines, dev_test_mt_lines, _, dev_test_pe_lines = \
        train_test_split(mt_lines, pe_lines, test_size=dev_test_size, 
            random_state=42)

    dev_mt_lines, test_mt_lines, _, _ = train_test_split(dev_test_mt_lines, 
        dev_test_pe_lines, test_size=test_size, random_state=42)

    print("Saving of files...")
    os.makedirs(save_dir, exist_ok=True)
    save_config(save_dir, config_paths, cli_args)

    write_lines(train_mt_lines, os.path.join(save_dir, 'train.mt'))
    write_lines(dev_mt_lines, os.path.join(save_dir, 'dev.mt'))
    write_lines(test_mt_lines, os.path.join(save_dir, 'test.mt'))

    if not mt_only:
        write_lines(train_src_lines, os.path.join(save_dir, 'train.src'))
        write_lines(dev_src_lines, os.path.join(save_dir, 'dev.src'))
        write_lines(test_src_lines, os.path.join(save_dir, 'test.src'))
        
        write_lines(train_pe_lines, os.path.join(save_dir, 'train.pe'))
        write_lines(dev_pe_lines, os.path.join(save_dir, 'dev.pe'))
        write_lines(test_pe_lines, os.path.join(save_dir, 'test.pe'))

if __name__ == "__main__":
    # Parser
    parser = argparse.ArgumentParser(description='APE')
    parser.add_argument('--config', type=str, default=None, nargs="*",
        help="Cofig file with additional arguments.")
    config_paths = [os.path.abspath(i) for i in
        parser.parse_known_args()[0].config]

    # Arguments
    hf_parser = APEParser((APEPrepareData,))
    args, remaining = hf_parser.parse_args_into_dataclasses_with_default(
            return_remaining_strings=True, json_default_files=config_paths)
    cli_args = hf_parser.parse_known_args(with_default=False)[0]

    # Check whether all the arguments are consumed
    if "--config" in remaining:
        for _ in range(len(config_paths)):
            remaining.remove(remaining[remaining.index("--config")+1])
        remaining.remove("--config")
    if len(remaining) > 0:
        raise RuntimeError("There are remaining attributes that could not "
            "be attributed: {}".format(remaining))

    prepare_data(src=args.src, mt=args.mt, pe=args.pe, save_dir=args.save_dir,
        word_tokenize=args.word_tokenize, aggressive_dash_splits=
        args.aggressive_dash_splits, processes=args.processes, 
        terminology_encode=args.terminology_encode, use_lemma=args.use_lemma, 
        min_sentence_threshold=args.min_sentence_threshold,
        max_sentence_threshold=args.max_sentence_threshold, 
        alignments=args.alignments, batch_size=args.batch_size,
        source_language=args.source_language, target_language=
        args.target_language, dev_test_size=args.dev_test_size, 
        test_size=args.test_size, text_min_length=args.text_min_length,
        mt_only=args.mt_only, cli_args=cli_args, config_paths=config_paths,
        clean=args.clean)