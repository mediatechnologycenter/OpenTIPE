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
import ast
import wandb
import argparse
import dataclasses
from typing import List 

from datasets import load_dataset, load_metric

import transformers
from transformers import set_seed, AutoTokenizer, AutoConfig

from mtc_ape_model.models.factor_model import FactorEncoderDecoderModel
from mtc_ape_model.utils.arguments import (APEArguments, APEModelArguments,
    APETrainingArguments, APEDataArguments, APETestCaseArguments)
from mtc_ape_model.utils.parser import APEParser
from mtc_ape_model.utils.logger import setup_logging
from mtc_ape_model.utils.misc import lines_to_file, dict_to_file
from mtc_ape_model.data.collator import DataCollatorForSeq2Seq
from mtc_ape_model.data.tokenizer import Seq2SeqTokenizer
from mtc_ape_model.trainer import TokenBatchSeq2SeqTrainer
from mtc_ape_model.data.terminology import TermFrequencyCounter
from mtc_ape_model.metrics.metrics_calculator import MetricsCalculator
from mtc_ape_model.utils.callbacks import (LoggerProgressCallback,
    TerminologyMetricsCallback, GarbageCollectorCallback, TextWandbCallback,
    log_configs_to_wandb, log_inputs_to_wandb)
from mtc_ape_model.utils.train_utils import (get_last_checkpoint, save_config,
    reports_to, hyperparameter_search, to_test_dataset, log_wandb_table,
    copy_columns)

def main(logger, args, model_args, data_args, training_args,test_case_args=None,
        config_paths=None, cli_args=None):

    # Get checkpoint if one exists
    last_checkpoint = get_last_checkpoint(training_args, verify=True,
        model_args=model_args)

    # Set seed for reproducability
    set_seed(training_args.seed)

    # Load data
    logger.info("LOADING THE DATA\n")
    raw_datasets = load_dataset(args.dataset_path, 
        **dataclasses.asdict(data_args))
    
    # Set the terminology term of the dataset
    dataset_info = ast.literal_eval(raw_datasets["train"].info.description)
    TGT_LANG = dataset_info["tgt_lang"]
        
    # Load metrics
    logger.info("LOADING THE METRICS\n")
    metric = load_metric(args.metric_path)

    # Load tokenizer
    logger.info("LOADING THE TOKENIZER\n")
    # use_fast=True + do_basic_tokenize=False does not work - bug?
    tokenizer = AutoTokenizer.from_pretrained(
        model_args.model_name_or_path, use_fast=False,
        do_basic_tokenize=False) 

    # Tokenize
    seq_tokenizer = Seq2SeqTokenizer(tokenizer,
        terminology_method = data_args.terminology_method,
        terminology_term = data_args.terminology_term,
        loss_ignore_label_id = data_args.loss_ignore_label_id)

    tokenized_datasets = raw_datasets.map(seq_tokenizer.tokenize, batched=False,
        load_from_cache_file=True, num_proc=args.preprocess_num_proc)
    
    # Get encoder/decoder input lengths
    def add_lengths(batch):
        return {"length": [len(example) for example in batch['input_ids']],
                "decoder_length": [len(example) 
                    for example in batch['decoder_input_ids']]}
    tokenized_datasets = tokenized_datasets.map(add_lengths, batched=True,
        load_from_cache_file=True, num_proc=args.preprocess_num_proc)

    # Sync lengths between validation_term and validation if available
    if 'validation_term' in tokenized_datasets:
        tokenized_datasets['validation_term'] = copy_columns(
            from_dataset = tokenized_datasets['validation'], 
            to_dataset = tokenized_datasets['validation_term'],
            columns = ["length", "decoder_length"], 
            num_proc = args.preprocess_num_proc)

    # Sync lengths between test_term and test if available
    if 'test_term' in tokenized_datasets:
        tokenized_datasets['test_term'] = copy_columns(
            from_dataset = tokenized_datasets['test'], 
            to_dataset = tokenized_datasets['test_term'],
            columns = ["length", "decoder_length"], 
            num_proc = args.preprocess_num_proc)

    # Filter too long samples
    dataset = tokenized_datasets.filter(
        lambda ex: ex['length'] < data_args.src_max_len and \
            ex['decoder_length'] < data_args.tgt_max_len,
            num_proc=args.preprocess_num_proc)

    # Shrink dataset if testing
    if args.run_as_test_case:
        logger.info("MAKE TEST DATASET\n")
        dataset = to_test_dataset(dataset, training_args=training_args,
            test_case_args=test_case_args)

    # Load model
    def model_init(trial):
        """ Method to load a model. Trial parameter used for providing
        parameters within hyperparameter search. """
        
        logger.info("LOADING THE MODEL\n")
        trial = {} if trial is None else trial.params

        # Reset seed each time this is called - i.e. for hyperparameter search
        set_seed(training_args.seed)

        # Init model
        if (AutoConfig.from_pretrained(
                model_args.model_name_or_path).model_type == "encoder-decoder"):
            mdl_args = dataclasses.asdict(model_args)
            del mdl_args["model_name_or_path"]
            del mdl_args["adapt_hidden_layer_size"]
            del mdl_args["adapted_hidden_layer_save_folder"]
            model = FactorEncoderDecoderModel.from_pretrained(
                model_args.model_name_or_path, **mdl_args)
        else:
            mdl_args = {k: v for k, v in dataclasses.asdict(model_args).items()
                if k != "model_name_or_path"}
            model_name_or_path = model_args.model_name_or_path
            mdl_args.update({
                "encoder_pretrained_model_name_or_path": model_name_or_path,
                "decoder_pretrained_model_name_or_path": model_name_or_path,
                "eos_token_id": tokenizer.sep_token_id,
                "pad_token_id": tokenizer.pad_token_id,
            })
            
            model = FactorEncoderDecoderModel.from_encoder_decoder_pretrained(
                **mdl_args)

            # Add vocab size from encoder and set decoder_start_token_id
            model.config.decoder_start_token_id = tokenizer.cls_token_id
            model.config.vocab_size = model.config.encoder.vocab_size
        return model

    # Data collator
    data_collator = DataCollatorForSeq2Seq(
        seq_tokenizer,
        label_pad_token_id=data_args.loss_ignore_label_id,
        pad_to_multiple_of=8 if training_args.fp16 else None,
    )

    # Initial callbacks
    callbacks = []
    if training_args.use_garbage_collector_callback:
        callbacks.append(GarbageCollectorCallback())
    

    # Initialize trainer
    trainer = TokenBatchSeq2SeqTrainer(
        model_init=model_init,
        args=training_args,
        train_dataset=dataset["train"] if training_args.do_train else None,
        eval_dataset=dataset["validation"] if training_args.do_eval else None,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=lambda pred: metric.compute(pred,
            tokenizer=tokenizer, return_pred_label_str=True,
            text_metric_identifier=training_args.text_metric_identifier),
        callbacks=callbacks if callbacks != [] else None
    )

    # Replace by progress callback with logger
    trainer.remove_callback(transformers.trainer_callback.ProgressCallback)
    trainer.add_callback(LoggerProgressCallback(logger=logger))
    
    # Term frequency counter
    term_counter = TermFrequencyCounter(lang=TGT_LANG,
        lemma_comparison=args.lemma_comparison)
    
    # Source sentences of the evaluation dataset
    src_sentences = None
    if training_args.do_eval:
        term_dat = dataset['validation_term'] if "validation_term" \
                in dataset.keys() else dataset['validation']
        src_sentences = {"eval": [(i["src"] + " [SEP] " + i["mt"]) if "mt" in i 
            else i["src"] for i in term_dat]}

    # Add terminology logging
    if data_args.terminology_method or data_args.terminology_dir:
        trainer.add_callback(TerminologyMetricsCallback(trainer=trainer,
            src_sentences=src_sentences, term_counter=term_counter))

    # Replace wandblogger
    trainer.remove_callback(transformers.integrations.WandbCallback)
    if reports_to(training_args, "wandb"):
        trainer.add_callback(TextWandbCallback(
            src_sentences=src_sentences,
            after_setup_callbacks=[
                lambda: log_inputs_to_wandb(training_args, dataset),
                lambda: log_configs_to_wandb(
                    args, data_args, model_args, test_case_args)])
        )

    # Hyperparameter search
    hypersearch_training_args = {}
    if training_args.do_hyperparameter_search:
        hypersearch_training_args = hyperparameter_search(training_args,
            trainer)
        logger.info("***** Hyperparameter best run *****")
        for key, value in hypersearch_training_args.items():
            setattr(training_args, key, value)
            logger.info(f"  {key} = {value}")

    # Save config file
    save_config(training_args.output_dir, config_paths=config_paths,
        cli_args=cli_args, hypersearch_args=hypersearch_training_args)

    # Training
    if training_args.do_train:

        # Start training
        logger.info("*** Train ***")
        train_result = trainer.train(resume_from_checkpoint=last_checkpoint)

        # Saves the tokenizer too for easy upload
        trainer.save_model()  

        # Need to save the state, since Trainer.save_model saves only the 
        # tokenizer with the model
        trainer.state.save_to_json(os.path.join(training_args.output_dir,
            "trainer_state.json"))

        if trainer.is_world_process_zero():
            # Write train stats
            dict_to_file(train_result.metrics, info="Train stats",
                file_path=os.path.join(training_args.output_dir, 
                "train_stats.txt"), as_json=args.metrics_as_json, logger=logger)
    
    # Evaluation
    def evaluate(dataset, data_split = "dev", term_dataset=None):
        
        translations, metrics = trainer.translate(dataset)
        text = [v for k,v in metrics.items() if 
            training_args.text_metric_identifier in k][0]

        if reports_to(training_args, "wandb") and len(text) > 0 and \
                training_args.do_train:

            src_sentences = [s['src'] if "mt" not in s else 
                (s['src'] + " [SEP] " + s["mt"]) for s in dataset]

            log_wandb_table(
                artifact_name = f"{wandb.run.id}-{wandb.run.name}-"
                                f"{data_split}_predictions",
                artifact_type = "predictions",
                table_name =    f"{data_split}_predictions",
                table_fields = ["train/global_step", "num","input",
                                "prediction", "reference"],
                table_content = [(trainer.state.global_step,
                        ind, src_sentences[ind], pred, ref)
                    for ind, (pred, ref) in enumerate(text)]
            )

        metrics = {k:v for k,v in metrics.items() if
            training_args.text_metric_identifier not in k}

        term_src = term_dataset['src'] if term_dataset else dataset['src']
        term_freq=term_counter.term_frequency_lines([i for i in term_src],
            [i[0] for i in text])[0]

        metrics.update({"term_frequency": term_freq, "samples": len(term_src)})
        metrics = {(k if k[:5] != "eval_" else k[5:]): v for k,v
            in metrics.items()}
        
        dict_to_file(metrics, info=f"{data_split} metrics",
            file_path=os.path.join(training_args.output_dir, 
            f"{data_split}_metrics.txt"), as_json=args.metrics_as_json,
            logger=logger)

        lines_to_file(translations, info=f"{data_split} predictions",
            file_path=os.path.join(training_args.output_dir, 
            f"{data_split}_predictions.txt"))

        return metrics
    
    calculator = MetricsCalculator(metric=metric, term_counter=term_counter)

    final_metrics = {}
    if training_args.do_train and training_args.train_eval_samples:
        logger.info("*** Train final eval ***")
        train_samples = list(range(training_args.train_eval_samples))
        final_metrics["train"] = evaluate(
            dataset["train"].select(train_samples), "train",
            None if "train_term" not in dataset.keys() else 
            dataset["train_term"].select(train_samples))

    if training_args.do_eval:
        logger.info("*** Validation final eval ***")
        final_metrics["eval"] = evaluate(dataset["validation"], "eval",
            dataset.get("validation_term", None))
        if "mt" in dataset["validation"].features:
            final_metrics["eval_do_nothing"] = \
                {k: None for k,_ in final_metrics["eval"].items()}
            final_metrics["eval_do_nothing"].update(
                calculator.metrics_from_lines(
                    src_lines=dataset["validation"]["mt"],
                    tgt_lines=dataset["validation"]["pe"],
                    src_term_lines=dataset["validation_term"]["src"] if
                        "validation_term" in dataset else (
                        dataset["validation"]["src"] if data_args.terminology_method
                        else None)
                )
            )

    if training_args.do_predict:
        logger.info("*** Test final eval ***")
        final_metrics["test"] = evaluate(dataset["test"], "test",
            dataset.get("test_term", None))
        if "mt" in dataset["test"].features:
            final_metrics["test_do_nothing"] = \
                {k: None for k,_ in final_metrics["test"].items()}
            final_metrics["test_do_nothing"].update(
                calculator.metrics_from_lines(
                    src_lines=dataset["test"]["mt"],
                    tgt_lines=dataset["test"]["pe"],
                    src_term_lines=dataset["test_term"]["src"] if
                        "test_term" in dataset else (
                        dataset["test"]["src"] if data_args.terminology_method
                        else None)
                )
            )

    if reports_to(training_args, "wandb") and len(final_metrics.keys()) > 0 and\
            training_args.do_train:
        splits = list(final_metrics.keys())
        log_wandb_table(artifact_name=
                f"{wandb.run.id}-{wandb.run.name}-final_metrics",
            artifact_type="metrics",
            table_name="final_metrics",
            table_fields=["metric"]+splits,
            table_content=[(mk, *[final_metrics[k][mk] for k in splits])
                for mk in final_metrics[splits[0]].keys()])

if __name__ == "__main__":

    # Parser
    parser = argparse.ArgumentParser(description='APE')
    parser.add_argument('--config', type=str, default=None, nargs="*",
        help="Cofig file with additional arguments.")
    config_paths = [os.path.abspath(i) for i in
        parser.parse_known_args()[0].config]

    # Arguments
    hf_parser = APEParser((APEArguments, APEModelArguments,
        APETrainingArguments, APEDataArguments, APETestCaseArguments))
    args, model_args, training_args, data_args, test_case_args, remaining = \
        hf_parser.parse_args_into_dataclasses_with_default(
            return_remaining_strings=True, json_default_files=config_paths)
    cli_args = hf_parser.parse_known_args(with_default=False)[0]

    os.environ["WANDB_PROJECT"] = args.wandb_project
    os.environ["WANDB_WATCH"] = args.wandb_watch

    # Check that output dir is set
    if training_args.output_dir is None:
        raise ValueError("Output directory is not set. Please set it.")

    # Set paths
    if training_args.extend_dirs_with_run_name:
        training_args.output_dir = os.path.join(training_args.output_dir, 
            training_args.run_name)
    training_args.logging_dir = os.path.join(training_args.output_dir, "logs")

    # Logging
    logger = setup_logging(args, training_args)

    # Check whether all the arguments are consumed
    if "--config" in remaining:
        for _ in range(len(config_paths)):
            remaining.remove(remaining[remaining.index("--config")+1])
        remaining.remove("--config")
    if len(remaining) > 0:
        raise RuntimeError("There are remaining attributes that could not "
            "be attributed: {}".format(remaining))

    main(logger=logger, args=args, model_args=model_args, data_args=data_args,
        training_args=training_args, test_case_args=test_case_args,
        config_paths=config_paths, cli_args=cli_args)