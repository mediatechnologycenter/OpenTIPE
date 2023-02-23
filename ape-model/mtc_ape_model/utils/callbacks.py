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

import gc
import torch
import wandb
import dataclasses
from math import ceil

from transformers import TrainerCallback
from transformers.trainer_callback import ProgressCallback
from transformers.integrations import WandbCallback, rewrite_logs

from mtc_ape_model.data.terminology import TermFrequencyCounter
from mtc_ape_model.utils.train_utils import log_wandb_table

class LoggerProgressCallback(ProgressCallback):
    """ A callback that displays the progress of training or evaluation. """

    def __init__(self, logger):
        self.training_bar = None
        self.prediction_bar = None
        self.logger = logger

    def on_log(self, args, state, control, logs=None, **kwargs):
        if state.is_local_process_zero and self.training_bar is not None:
            _ = logs.pop("total_flos", None)
            log = {k:v for k,v in logs.items()
                if args.text_metric_identifier not in k}
            self.logger.info(str(log))

class TextWandbCallback(WandbCallback):
    """ Extended WandbCallback to log input/prediction/reference sentences. """
    def __init__(self, src_sentences=None, after_setup_callbacks=[]):
        super().__init__()
        self.src_sentences = src_sentences
        self.after_setup_callbacks = after_setup_callbacks


    def setup(self, args, state, model, **kwargs):
        super().setup(args=args, state=state, model=model, **kwargs)
        for f in self.after_setup_callbacks:
            f()
        del self.after_setup_callbacks

    def on_log(self, args, state, control, model=None, logs=None, **kwargs):
        
        if self._wandb is None:
            return
        
        if not self._initialized:
            self.setup(args, state, model)

        if state.is_world_process_zero:
            logs = rewrite_logs(logs)
            log = {k:v for k,v in logs.items() if 
                args.text_metric_identifier not in k}

            self._wandb.log({**log, "train/global_step": state.global_step})

            log_text = [v for k,v in logs.items() if
                args.text_metric_identifier in k and "eval" in k]

            if len(log_text) > 0 and self.src_sentences:
                if "eval" in self.src_sentences:
                    assert(len(log_text)) == 1
                    log_wandb_table(
                        artifact_name=f"{self._wandb.run.id}-"
                            f"{self._wandb.run.name}-eval_predictions",
                        artifact_type="predictions",
                        table_name="eval_predictions",
                        table_fields=["train/global_step","num", "input",
                            "prediction", "reference"],
                        table_content=[
                            (state.global_step, ind,
                            self.src_sentences["eval"][ind],
                            *pred_ref)
                        for ind, pred_ref in enumerate(log_text[0])])
                    


class TerminologyMetricsCallback(TrainerCallback):
    """ Compute terminology metrics with help of the source datasets and
    trigger log method of other callbacks. """
    def __init__(self, trainer, src_sentences,
            term_counter: TermFrequencyCounter = None):
        super().__init__()
        self.src_sentences = src_sentences
        self.trainer = trainer
        self.term_counter = term_counter

    def on_log(self, args, state, control, model=None, logs=None, **kwargs):
        
        if state.is_world_process_zero and self.src_sentences and \
            any([args.text_metric_identifier in i for i in logs.keys()]):

            # Go over all src_datasets
            for split, src_sentences in self.src_sentences.items():
                # Get the pred/label tuples if there is of the split
                log_text = [v for k,v in logs.items() if
                    args.text_metric_identifier in k and split in k]
                if len(log_text) > 0:
                    # There should be only one tuple
                    assert(len(log_text)) == 1
                    # Retrieve it
                    log_text = log_text[0]
                    term_freq=self.term_counter.term_frequency_lines(
                        src_sentences, [i[0] for i in log_text])[0]
                    term_freq = {f"{split}_term_frequency": term_freq}
                    self.trainer.log(term_freq)

class TrainMetricsCallback(TrainerCallback):
    """ Logs training metrics."""
    DO_NOTHING = 0
    SAVE_PREDICTIONS = 1
    COMPUTE_AND_LOG_METRICS = 2

    def on_step_begin(self, args, state, control, logs=None, **kwargs):
        # Added variable to notify trainer to compute train_metric
        # Trainer is not accessible within here, thus add it to it's model
        collect_iters = ceil(args.train_eval_samples / 
            args.gradient_accumulation_steps)
        if (state.global_step+collect_iters) % args.eval_steps < collect_iters:
            kwargs["model"].compute_train_metrics = \
                (TrainMetricsCallback.SAVE_PREDICTIONS, state.global_step)

        if state.global_step % args.eval_steps == 0 and state.global_step != 0:
            kwargs["model"].compute_train_metrics = \
                (TrainMetricsCallback.COMPUTE_AND_LOG_METRICS, state.global_step)

class GarbageCollectorCallback(TrainerCallback):
    """ Callback that calls garbage collection at every possible step during
    the training procedure.
    """

    def on_evaluate(self, args, state, control, logs=None, **kwargs):
        gc.collect()
        torch.cuda.empty_cache()

    def on_prediction_step(self, args, state, control, logs=None, **kwargs):
        gc.collect()
        torch.cuda.empty_cache()

    def on_step_begin(self, args, state, control, logs=None, **kwargs):
        gc.collect()
        torch.cuda.empty_cache()

def log_configs_to_wandb(args, data_args, model_args, test_case_args):
    """ Data & general config log """
    combined_dict = {**dataclasses.asdict(args),
        "data": dataclasses.asdict(data_args), 
        **dataclasses.asdict(model_args),
        "test_case": dataclasses.asdict(test_case_args)
    }
    wandb.config.update(combined_dict, allow_val_change=True)

def log_inputs_to_wandb(training_args, dataset):
    """ Log input datasets to wandb."""

    if training_args.do_eval:
        data = dataset['validation']
        split = "eval"
        log_wandb_table(
            artifact_name=f"{wandb.run.id}-{wandb.run.name}-{split}_inputs",
            artifact_type="inputs", 
            table_name=f"{split}_inputs",
            table_fields=["num", "src", "mt"] if "mt" in data.features
                else ["num", "src"],
            table_content=[(i, data[i]["src"], data[i]["mt"]) 
                if "mt" in data.features else (i, data[i]["src"])
                for i in range(len(data))]
        )

    if training_args.do_predict:
        data = dataset['test']
        split = "test"
        log_wandb_table(
            artifact_name=f"{wandb.run.id}-{wandb.run.name}-{split}_inputs",
            artifact_type="inputs", 
            table_name=f"{split}_inputs",
            table_fields=["num", "src", "mt"] if "mt" in data.features 
                else ["num", "src"],
            table_content=[(i, data[i]["src"], data[i]["mt"]) if "mt" 
                in data.features else (i, data[i]["src"]) 
                for i in range(len(data))]
        )