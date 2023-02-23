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

""" Metrics for APE task. """

import datasets
import sacrebleu
from typing import Dict

@datasets.utils.file_utils.add_start_docstrings(_DESCRIPTION)
class APE(datasets.Metric):

    def _info(self):
        return datasets.MetricInfo(
            description=_DESCRIPTION,
            citation=_CITATION,
            inputs_description=_KWARGS_DESCRIPTION,
            features=datasets.Features(
                {
                    "predictions": datasets.Value("int64"),
                    "labels_ids": datasets.Value("int64"),
                }
            ),
            codebase_urls=[],
            reference_urls=[],
            format="numpy",
        )

    def _download_and_prepare(self, dl_manager):
        """Optional: download external resources useful to compute the scores"""
        self.rouge = datasets.load_metric("rouge")
        self.bleu = datasets.load_metric("sacrebleu")

    def compute_id_based_metrics(self, predictions_ids, labels_ids, pad_tok_id):
        """ Compute metrics based on the ids. """

        # Accuracy
        is_correct = (predictions_ids == labels_ids).flatten()
        mask_pad = (labels_ids.flatten() != pad_tok_id)
        accuracy = is_correct[mask_pad].mean()

        return {"accuracy": accuracy}

    def compute_string_based_metrics(self, predictions_str, labels_str):
        """ Compute metrics based on the strings. """

        rouge_output = self.rouge.compute(predictions=predictions_str,
            references=labels_str, rouge_types=["rouge2"])["rouge2"].mid

        bleu_score = self.bleu.compute(predictions=predictions_str,
            references=[[i] for i in labels_str])['score']

        ter_scores = [float(sacrebleu.sentence_ter(pred, [ref]).format(
			score_only=True)) for pred, ref in zip(predictions_str, labels_str)]
        ter_score = sum(ter_scores) / len(ter_scores)

        return {
            "rouge2_precision": round(rouge_output.precision, 4),
            "rouge2_recall": round(rouge_output.recall, 4),
            "rouge2_fmeasure": round(rouge_output.fmeasure, 4),
            "sacrebleu": round(bleu_score, 4),
            "ter_score": round(ter_score, 4)
        }

    @datasets.utils.file_utils.add_start_docstrings(_KWARGS_DESCRIPTION)
    def compute(self, pred, tokenizer, return_pred_label_str: bool = False,
            text_metric_identifier="text_") -> Dict[str, float]:
        """ General compute - combining ids + str - used in Trainer . """

        predictions_ids = pred.predictions
        labels_ids = pred.label_ids

        metrics = self.compute_id_based_metrics(
            predictions_ids=predictions_ids, labels_ids=labels_ids,
            pad_tok_id=tokenizer.pad_token_id)

        predictions_str = tokenizer.batch_decode(predictions_ids,
            skip_special_tokens=True, clean_up_tokenization_spaces=False)
        labels_ids[labels_ids == -100] = tokenizer.pad_token_id
        labels_str = tokenizer.batch_decode(labels_ids, 
            skip_special_tokens=True, clean_up_tokenization_spaces=False)

        metrics.update(self.compute_string_based_metrics(
            predictions_str=predictions_str, labels_str=labels_str))
        
        if return_pred_label_str:
            metrics.update({f"{text_metric_identifier}samples": list(
                zip(predictions_str, labels_str))})
            
        return metrics