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

import torch
import datasets
from collections import deque

from torch import nn
from torch.cuda.amp import autocast
from torch.utils.data import DataLoader

from transformers.file_utils import is_datasets_available
from transformers.trainer_pt_utils import IterableDatasetShard
from transformers.trainer_utils import EvalPrediction

from transformers import Trainer, Seq2SeqTrainer
from transformers.trainer_seq2seq import  is_deepspeed_zero3_enabled
from typing import List, Any

from mtc_ape_model.data.sampler import BatchLengthGroupedSampler
from mtc_ape_model.utils.callbacks import TrainMetricsCallback

from typing import Tuple, Optional, Dict, Union
class TokenDataLoader():

    def get_train_dataloader(self) -> DataLoader:
        """
        Returns the training :class:`~torch.utils.data.DataLoader`.

        Will use no sampler if :obj:`self.train_dataset` does not implement 
        :obj:`__len__`, a random sampler (adapted to distributed training if 
        necessary) otherwise.

        Subclass and override this method if you want to inject some 
        custom behavior.
        """
        if self.train_dataset is None:
            raise ValueError("Trainer: training requires a train_dataset.")

        train_dataset = self.train_dataset
        if is_datasets_available() and isinstance(train_dataset, 
                datasets.Dataset):
            train_dataset = self._remove_unused_columns(train_dataset,
                description="training")

        if isinstance(train_dataset, torch.utils.data.IterableDataset):
            if self.args.world_size > 1:
                train_dataset = IterableDatasetShard(
                    train_dataset,
                    batch_size=self.args.train_batch_size,
                    drop_last=self.args.dataloader_drop_last,
                    num_processes=self.args.world_size,
                    process_index=self.args.process_index,
                )

            return DataLoader(
                train_dataset,
                batch_size=self.args.train_batch_size,
                collate_fn=self.data_collator,
                num_workers=self.args.dataloader_num_workers,
                pin_memory=self.args.dataloader_pin_memory,
            )
        
        train_sampler = self._get_train_sampler()
        batch_train_sampler = BatchLengthGroupedSampler(train_sampler,
            self.args.train_batch_size, self.args.token_batching,
            self.args.batch_size_includes_padding)

        return DataLoader(
            train_dataset,
            batch_sampler = batch_train_sampler,
            collate_fn=self.data_collator,
            drop_last=self.args.dataloader_drop_last,
            num_workers=self.args.dataloader_num_workers,
            pin_memory=self.args.dataloader_pin_memory,
        )

    def compute_loss(self, model, inputs, return_outputs=False):
        """
        MAX: Subclassed to compute training accuracy.

        How the loss is computed by Trainer. By default, all models return
        the loss in the first element.

        Subclass and override for custom behavior.
        """
        loss, outputs = super().compute_loss(model, inputs, return_outputs=True)

        # Custom train metrics logging
        if self.args.train_eval_samples:

            # Custom train metrics
            if not hasattr(self.model, "compute_train_metrics"):
                # Init required fields and callback 
                self.add_callback(TrainMetricsCallback())
                self.model.compute_train_metrics = \
                    (TrainMetricsCallback.DO_NOTHING, 0)
            
            n_samples_train_metric = self.args.train_eval_samples
            if not hasattr(self.model, "last_global_step"):
                # Used to just compute the metrics once in case of several
                # passes during gradient accumulation
                self.model.last_global_step = -1
                self.labels_buffer = deque([], n_samples_train_metric)
                self.preds_buffer = deque([], n_samples_train_metric)

            if self.model.compute_train_metrics[0] == \
                    TrainMetricsCallback.SAVE_PREDICTIONS and "labels" in inputs:
                self.labels_buffer.extend(
                    [i for i in inputs["labels"].detach().cpu()])
                self.preds_buffer.extend([i for i in
                    outputs.logits.detach().cpu().argmax(axis=2)])

            if self.model.compute_train_metrics[0] == \
                    TrainMetricsCallback.COMPUTE_AND_LOG_METRICS and \
                        (self.model.last_global_step != \
                            self.model.compute_train_metrics[1]):

                # Custom behavior
                last_global_step = self.model.compute_train_metrics[1]
                self.model.compute_train_metrics = (
                    TrainMetricsCallback.DO_NOTHING, last_global_step)
                self.model.last_global_step = last_global_step

                if "labels" in inputs and self.compute_metrics:

                    preds = torch.nn.utils.rnn.pad_sequence(
                        list(self.preds_buffer), batch_first=True,
                        padding_value=self.model.config.pad_token_id)

                    labels = torch.nn.utils.rnn.pad_sequence(
                        list(self.labels_buffer), batch_first=True,
                        padding_value=self.model.config.pad_token_id)

                    train_metrics = self.compute_metrics(
                        EvalPrediction(predictions=preds.numpy()[:, :-1],
                        label_ids=labels.numpy()[:, 1:]))

                    self.log(train_metrics)
                    self.labels_buffer = deque([], n_samples_train_metric)
                    self.preds_buffer = deque([], n_samples_train_metric)

            self.model.compute_train_metrics = (TrainMetricsCallback.DO_NOTHING,
                self.model.compute_train_metrics[1])

        return (loss, outputs) if return_outputs else loss

class TokenBatchTrainer(TokenDataLoader, Trainer):
    pass

class TokenBatchSeq2SeqTrainer(TokenDataLoader, Seq2SeqTrainer):

    def translate(self, dataset, tokenizer=None):
        outputs = self.predict(dataset)
        output_str = (tokenizer if tokenizer else self.tokenizer).batch_decode(
            outputs.predictions, skip_special_tokens=True,
            clean_up_tokenization_spaces=False)
        return output_str, outputs.metrics

    def translate_map(self, batch, tokenizer=None):
    
        # Add batch dimension if single element is given as input
        if type(batch["input_ids"][0]) != list:
            batch = {k: [batch[k]] for k in batch}

        input_ids = [torch.tensor(i) for i in batch['input_ids']]
        input_ids = torch.nn.utils.rnn.pad_sequence(input_ids, batch_first=True,
            padding_value=self.model.config.pad_token_id).to("cuda")
        input_ids = input_ids.to(next(self.model.parameters()).device)

        attention_mask = [torch.tensor(i) for i in batch['attention_mask']]
        attention_mask = torch.nn.utils.rnn.pad_sequence(attention_mask,
            batch_first=True, padding_value=0)
        attention_mask = attention_mask.to(next(self.model.parameters()).device)

        outputs = self.model.generate(input_ids,attention_mask=attention_mask,
            decoder_start_token_id=self.model.config.decoder_start_token_id)

        output_str = (tokenizer if tokenizer else self.tokenizer).batch_decode(
            outputs, skip_special_tokens=True,
            clean_up_tokenization_spaces=False)

        return {"pred_translation": output_str}

    def prediction_step(
        self,
        model: nn.Module,
        inputs: Dict[str, Union[torch.Tensor, Any]],
        prediction_loss_only: bool,
        ignore_keys: Optional[List[str]] = None,
    ) -> Tuple[Optional[float], Optional[torch.Tensor], Optional[torch.Tensor]]:

        if not self.args.predict_with_generate or prediction_loss_only:
            return super().prediction_step(model, inputs,
            prediction_loss_only=prediction_loss_only, ignore_keys=ignore_keys)

        has_labels = "labels" in inputs
        inputs = self._prepare_inputs(inputs)

        # XXX: adapt synced_gpus for fairscale as well
        gen_kwargs = {
            "max_length": self._max_length if self._max_length is not None 
                else self.model.config.max_length,
            "num_beams": self._num_beams if self._num_beams is not None else 
                self.model.config.num_beams,
            "synced_gpus": True if is_deepspeed_zero3_enabled() else False,
        }

        generated_tokens = self.model.generate(
            inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            token_type_ids=inputs["token_type_ids"],
            position_ids=inputs["factor_ids"],
            # decoder_token_type_ids=inputs["decoder_token_type_ids"],
            # decoder_position_ids=inputs["decoder_factor_ids"],
            **gen_kwargs,
        )
        # in case the batch is shorter than max length, 
        # the output should be padded
        if generated_tokens.shape[-1] < gen_kwargs["max_length"]:
            generated_tokens = self._pad_tensors_to_max_len(generated_tokens, 
                gen_kwargs["max_length"])

        with torch.no_grad():
            if self.use_amp:
                with autocast():
                    outputs = model(**inputs)
            else:
                outputs = model(**inputs)
            if has_labels:
                if self.label_smoother is not None:
                    loss = self.label_smoother(
                        outputs, inputs["labels"]).mean().detach()
                else:
                    loss = (outputs["loss"] if isinstance(outputs,
                        dict) else outputs[0]).mean().detach()
            else:
                loss = None

        if self.args.prediction_loss_only:
            return (loss, None, None)

        labels = inputs["labels"]
        if labels.shape[-1] < gen_kwargs["max_length"]:
            labels = self._pad_tensors_to_max_len(labels, 
                gen_kwargs["max_length"])

        return (loss, generated_tokens, labels)