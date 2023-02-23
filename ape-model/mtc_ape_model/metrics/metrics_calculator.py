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
import sys
import argparse
from datasets import load_metric

if __name__ == "__main__":
    curr_dir=os.path.abspath(__file__)
    parentdir = os.path.dirname(os.path.dirname(os.path.dirname(curr_dir)))
    os.sys.path.insert(0,parentdir)

from mtc_ape_model.utils.misc import dict_to_file
from mtc_ape_model.data.terminology import TermFrequencyCounter

class MetricsCalculator:
    
    def __init__(self, metric, term_counter):
        self.metric = metric
        self.term_counter = term_counter
        
    def metrics_from_lines(self, src_lines, tgt_lines, src_term_lines=None):
        metrics=self.metric.compute_string_based_metrics(src_lines, tgt_lines)
        if src_term_lines:
            term_freq = self.term_counter.term_frequency_lines(src_term_lines,
                src_lines)[0]
            metrics.update({"term_frequency": round(term_freq, 4)})
        metrics.update({"samples": len(src_lines)})
        return metrics

    def metrics_from_files(self, src_file, tgt_file, src_term_file=None,
            output_file=None):
        with open(src_file, "r") as src:
            with open(tgt_file, "r") as tgt:
                src_lines = src.readlines()
                tgt_lines = tgt.readlines()
                if src_term_file:
                    src_term_lines = open(src_term_file, "r").readlines()
                else:
                    src_term_lines=None
                metrics = self.metrics_from_lines(src_lines, tgt_lines,
                    src_term_lines)
                print(metrics)
                if output_file:
                    dict_to_file(metrics, info="mt_metrics", 
                        file_path=output_file, as_json=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='APE')
    parser.add_argument('--src_file', type=str)
    parser.add_argument('--tgt_file', type=str)
    parser.add_argument('--src_term_file', type=str, default=None)
    parser.add_argument('--output_file', type=str, default=None)
    parser.add_argument('--lang', type=str, default="en")
    parser.add_argument('--lemma_comparison', type=bool, default=True)
    args = parser.parse_args()
    metric = load_metric("metric.py")
    term_counter = TermFrequencyCounter(args.lang, args.lemma_comparison)
    translator = MetricsCalculator(metric, term_counter)
    translator.metrics_from_files(args.src_file, args.tgt_file,
        args.src_term_file, args.output_file)