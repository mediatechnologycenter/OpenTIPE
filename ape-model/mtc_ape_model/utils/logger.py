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
import logging

import tqdm
import optuna
import transformers
from transformers.trainer_utils import is_main_process

from mtc_ape_model.utils.arguments import (APETrainingArguments, APEArguments)

logger = logging.getLogger(__name__)
LOG_FILE_NAME = "run.log"
LOG_FORMAT = "[%(levelname)s|%(filename)s:%(lineno)d] %(asctime)s,%(msecs)d >> %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.tqdm.write(msg)
            self.flush()
        except Exception:
            self.handleError(record) 

def setup_logging(args: APEArguments, training_args: APETrainingArguments) \
        -> logging.Logger:
    """ Initiates a logger.

    Parameters
    ----------
    training_args:
        Training arguments that provide certain arguments to the logger setup.

    Returns
    -------
    A logger instance.
    """
    """ Setup logging. """
    if args.run_as_test_case or args.log_to_file:
        if args.run_as_test_case:
            args.logging_level = "INFO"
        if not os.path.isdir(training_args.output_dir):
            os.makedirs(training_args.output_dir)
        logging.basicConfig(
            format="%(message)s" if args.run_as_test_case else LOG_FORMAT,
            datefmt=DATE_FORMAT,
            filename=os.path.join(training_args.output_dir, LOG_FILE_NAME)
        )
        # logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
        logging.getLogger().addHandler(TqdmLoggingHandler())
    else:
        logging.basicConfig(
            format=LOG_FORMAT,
            datefmt=DATE_FORMAT,
            handlers=[logging.StreamHandler(sys.stdout)])

    logger.setLevel(logging.getLevelName(args.logging_level))
    
    # Log on each process the small summary:
    logger.warning(
        f"Process rank: {training_args.local_rank}, \
          device: {training_args.device}, n_gpu: {training_args.n_gpu}, \
          distributed training: {bool(training_args.local_rank != -1)}, \
          16-bits training: {training_args.fp16}"
    )

    # Set the verbosity of the logger (on main process only):
    if is_main_process(training_args.local_rank):
        transformers.utils.logging.set_verbosity(
            logging.getLevelName(args.logging_level))
        transformers.utils.logging.disable_default_handler()
        transformers.utils.logging.enable_propagation()
        transformers.utils.logging.enable_explicit_format()
        optuna.logging.disable_default_handler()
        optuna.logging.enable_propagation()

    logger.info("\n\n*** TRAINING / EVALUATION PARAMETERS ***\n%s\n",
        training_args)
    return logger