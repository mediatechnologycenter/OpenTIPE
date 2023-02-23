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
import json
import wandb
import logging

from argparse import Namespace
from re import I
from typing import Any, List, Dict, Optional, Union, Tuple

from transformers import Seq2SeqTrainingArguments
from transformers.trainer_utils import get_last_checkpoint as \
    get_last_checkpoint_hf

from mtc_ape_model.utils.parser import APEParser
from mtc_ape_model.utils.arguments import APEModelArguments
from mtc_ape_model.utils.logger import LOG_FILE_NAME

logger = logging.getLogger(__name__)
CONFIG_FILE_NAME = "run_config.json"

def get_run_config_from_checkpoint(checkpoint: str) -> str:
    """ Returns the config used for the training of a checkpoint.

    Parameters
    ----------
    checkpoint:
        Path to a checkpoint.

    Returns
    -------
    Path to the config used for the training of the checkpoint if there is one
    - else None.
    """
    path = os.path.abspath(os.path.join(checkpoint, os.pardir, 
        CONFIG_FILE_NAME))
    if os.path.isfile(path):
        return path
    else:
        logger.warning(f"Could not find the run_config file of the \
            checkpoint {checkpoint}.")
        return None

def is_checkpoint_compatible(checkpoint_model_args: APEModelArguments,
        model_args: APEModelArguments, return_uncompatible_args: bool = True)\
        -> Union[bool, Tuple[bool, List[str]]]:
    """ Checks whether a chechpoint is compatible with a config instance. To be
    used when loading a pretrained model with new configs. As general rule,
    the model_config cannot be different in this case, as they influence the
    weights, inputs, outputs and/or behavior of the model.
    
    Parameters
    ----------
    checkpoint_model_args:
        Model arguments of the checkpoint
    model_args:
        The model arguments to check them against
    return_uncompatible_args:
        Whether to return the parameters that do not match.
    
    Returns
    -------
    Whether the paremeters are compatible
    If `return_uncompatible_args=True` a list of parameters that are not \
    compatbile (if none an empty list).
    """
    checkpoint_dict = vars(checkpoint_model_args)
    args_dict = vars(model_args)
    is_compatible = True
    uncompatible_args = []
    for i in checkpoint_dict:
        is_current_compatible = (checkpoint_dict[i] == args_dict[i])
        if not is_current_compatible:
            uncompatible_args.append(i)
        is_compatible = is_compatible and is_current_compatible
    if return_uncompatible_args:
        return is_compatible, uncompatible_args
    else:
        return is_compatible

def verify_checkpoint(checkpoint, model_args):
    checkpoint_config = get_run_config_from_checkpoint(checkpoint)
    hf_parser = APEParser((APEModelArguments))
    checkpoint_model_args = hf_parser.parse_json_file(checkpoint_config)[0]
    if checkpoint_model_args:
        is_compatible, uncompatible_args = is_checkpoint_compatible(
            checkpoint_model_args, model_args)
        if not is_compatible:
            raise RuntimeError("The checkpoint is not compatible with the"
                "current APE_ARGS. Verify arguments {}.".format(
                    uncompatible_args))
    else:
        raise ValueError(f"Could not find {CONFIG_FILE_NAME} in checkpoint"
                            "to check compatibility.")

def get_last_checkpoint(training_args: Seq2SeqTrainingArguments,
        verify: bool = True, model_args: APEModelArguments = None) -> str:
    """ Checks whether there is a previous checkpoint.
    
    Parameters
    ----------
    training_args:
        Training arguments.

    Returns
    -------
    The path to the previous checkpoint if there exists one - else None.
    """
    last_checkpoint = None
    if os.path.isdir(training_args.output_dir) and training_args.do_train \
            and not training_args.overwrite_output_dir:
        last_checkpoint = get_last_checkpoint_hf(training_args.output_dir)
        files = os.listdir(training_args.output_dir)
        if LOG_FILE_NAME in files:
            files.remove(LOG_FILE_NAME)
        if last_checkpoint is None and len(files) > 0:
            raise ValueError(
                f"Output directory ({training_args.output_dir}) already exists "
                "and is not empty. Use --overwrite_output_dir to overcome."
            )
        elif last_checkpoint is not None:

            logger.info(
                f"Checkpoint detected, resuming training at {last_checkpoint}. "
                "To avoid this behavior, change the `--output_dir` or add "
                "`--overwrite_output_dir` to train from scratch."
            )
    if verify and last_checkpoint is not None:
        assert(model_args), "Provide model args to verify."
        verify_checkpoint(checkpoint=last_checkpoint, model_args=model_args)

    return last_checkpoint

def save_config(output_dir: str, config_paths: Optional[List[str]] = None,
        cli_args: Optional[Namespace] = None,
        hypersearch_args: Optional[Dict] = None):
    """ Saves the configs to a file.

    Parameters
    ----------
    output_dir:
        Directory in which to save the config file.
    config_paths:
        List of json config files (the later configs override the arguments
        of earlier ones).
    cli_args:
        A Namespace from argparse with cli arguments. Overrides arguments
        from `config_paths`.
    """
    if config_paths is not None:
        json_objects = []
        for config_path in config_paths:
            json_file = open(config_path, "r")
            json_object = json.load(json_file)
            json_file.close()
            json_objects.append(json_object)
        json_object = json_objects[0]
        for i in json_objects[1:]:
            json_object.update(i)
    else:
        json_object = {}

    if cli_args:
        # CLI args overwrite config args
        args_dict = vars(cli_args)
        for key, obj in args_dict.items():
            json_object[key] = obj

    if hypersearch_args:
        for key, obj in hypersearch_args.items():
            json_object[key] = obj

    save_file = open(os.path.join(output_dir, CONFIG_FILE_NAME), "w")
    json.dump(json_object, save_file, indent=4)
    save_file.close()

def hyperparameter_search(training_args, trainer):
    # Define search space
    def optuna_hp_space(trial):
        # Alternatives to suggest_categorical can be found at:
        # https://optuna.readthedocs.io/en/stable/reference/multi_objective/
        # generated/optuna.multi_objective.trial.MultiObjectiveTrial.html?
        # highlight=suggest#optuna.multi_objective.trial.
        # MultiObjectiveTrial.suggest_categorical
        assert(all(type(item) == list for item in
            training_args.hypersearch_space.values())), ("Hyperparameter"
            " space should be defined as a dict of names to lists.")
        hp_space = {key: trial.suggest_categorical(key, value) for 
            key, value in training_args.hypersearch_space.items()}
        return hp_space

    # Objective
    obj = training_args.hypersearch_objective
    def objective(obj_metrics):
        if obj:
            if obj in obj_metrics:
                return obj_metrics[obj]
            elif "eval_" + obj in obj_metrics:
                return obj_metrics["eval_" + obj]
        else:
            return None
        raise RuntimeError("Could not determine objective for "
            "hyperparameter search")

    # Perform hyperparameter search
    best_run = trainer.hyperparameter_search(
        hp_space=optuna_hp_space,
        compute_objective=objective,
        n_trials=training_args.hypersearch_trials,
        backend="optuna",
        direction="maximize"
    )

    # Set best parameters to training_args & log
    hypersearch_training_args = best_run.hyperparameters
    return hypersearch_training_args

def reports_to(training_args, tag):
    return (tag in training_args.report_to) or \
           (tag == training_args.report_to) or \
           ("all" == training_args.report_to) or \
           ("all" in training_args.report_to)

def to_test_dataset(dataset, training_args, test_case_args):
    """ Shrink a dataset to be used for testing. """
    test_sizes = {
            "train": test_case_args.train_size,
            "validation": test_case_args.valid_size,
            "test": test_case_args.test_size
        }

    for tag in dataset.keys():
        size = -1
        for s in test_sizes:
            if s in tag:
                size = test_sizes[s]
                break
        assert(size != -1)
        dataset[tag] = dataset[tag].shuffle(
            seed=training_args.seed).select(range(size))

    # Only take a subset of the data for testing
    dataset['validation'] = dataset["validation"].shuffle(
        seed=training_args.seed).select(
            range(test_case_args.valid_size))
    dataset['test'] = dataset["test"].shuffle(
        seed=training_args.seed).select(
            range(test_case_args.test_size))
    return dataset

def log_wandb_table(artifact_name, artifact_type, table_name,
        table_fields, table_content):
    """ Log a table to wandb. """
    # at = wandb.Artifact(artifact_name, type=artifact_type)
    text_table = wandb.Table(columns=table_fields)
    for entry in table_content:
        text_table.add_data(*entry)
    # at.add(text_table, table_name)
    # wandb.run.log_artifact(at)
    wandb.log({table_name: text_table})

def copy_columns(from_dataset, to_dataset, columns, num_proc):
    """ Copy the columns from one dataset to another.
    They need to be of same size. """
    def set_len(_, idx):
        return {i: from_dataset[i][idx] for i in columns}
    return to_dataset.map(set_len, with_indices=True, num_proc=num_proc)
