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

from dataclasses import dataclass, field
from typing import Optional, List, Union, Tuple, Dict

from transformers import Seq2SeqTrainingArguments

@dataclass
class APEArguments:
    """ General arguments to run the **ape.py** python script. """

    dataset_path: str = field(default="mtc_ape_model/data/dataset.py",
        metadata={"help": "Path or identifier for the dataset to load."})

    metric_path: str = field(default="mtc_ape_model/metrics/metric.py",
        metadata={"help": "Path or identifier for the metrics to load."})

    run_as_test_case: bool = field(default=False,
        metadata={"help": "Whether this is a test case run. I.e. a run not to \
        train a model but to test the pipeline (train/test size decreased)."})

    log_to_file: bool = field(default=True,
        metadata={"help": "Whether to log to a file or output stream. In case \
        of run_as_test_case == True always logs to file."})

    logging_level: str = field(default="INFO",
        metadata={"help": "Level of logging."})

    preprocess_num_proc: int = field(default=6, metadata={"help":
        "Number of processes to use during preprocessing"})

    metrics_as_json: bool = field(default=True, metadata={"help": 
        "Whether to store the metrics as json, in a text file else"}) 

    lemma_comparison: bool = field(default=True, metadata={
        "help": "Whether to compare lemma of predictions to the embedded "
        "source terminologies or not."})

    wandb_project: str = field(default="APE", metadata={
        "help": "Wandb project to log to"})

    wandb_watch: str = field(default="all", metadata={
        "help": "Weights & biases - what to watch"})
        
@dataclass
class APEModelArguments:
    """ Model arguments to run the **ape.py** python script. """

    model_name_or_path: str = field(default="dbmdz/bert-base-german-cased",
        metadata={ "help": "The model checkpoint for weights initialization."})

    tie_encoder_decoder: bool = field(default=True, metadata={ "help": 
        "Whether to tie encoder and decoder weights"})

    adapt_hidden_layer_size: bool = field(default=True, metadata={ "help":
        "Whether to adjust the hidden layer size in order to append"
        "factor embeddings. Else simply the last `factor_embed_dim` features"
        " of the word embeddings are replaces by factor embeddings."})
    
    adapted_hidden_layer_save_folder: str = field(default=
        "mtc_ape_model/checkpoints", metadata={ "help": "Folder in which to "
        "save the model variants with adjusted hidden layer size."})

    factors_in_encoder: bool = field(default=True, metadata={ "help": 
        "Whether to use the factors embeddings in encoder"})

    factors_in_decoder: bool = field(default=False, metadata={ "help": 
        "Whether to use the factors e,beddings in decoder."})

    factor_embed_dim: int = field(default=0, metadata={ "help": "Embedding "
        "size of the factors."})

    factor_embedding_init_method: str = field(default="xavier_normal", 
        metadata={"help": "Initialization method for the factor embeddings.", 
        "choices": ["xavier_uniform", "xavier_normal", "kaiming_uniform"]})

    n_factors: bool = field(default=4, metadata={ "help": "How many values the "
        "factors can take."})

    use_token_type_ids: bool = field(default=True, metadata={ "help": 
        "Whether to use token-type ids."})

    max_length: int = field(default=512, metadata={"help": 
        "Maximum length of the sequence to generate"})

    min_length: int = field(default=10, metadata={"help": 
        "Minimum length of the sequence to generate"})

    early_stopping: bool = field(default=True, metadata={"help": 
        "Whether to stop the beam search when at least num_bean sentences "
        "are finished per batch or not"})

    length_penalty: float = field(default=1.0, metadata={"help": 
        "Exponential penalty to  the length. < 1.0 encourages shorther "
        "sequences, > 1.0 encourages longer sequences."})

    num_beams: int = field(default=4, metadata={"help": 
        "Number of beams for beam seach. 1 means no beam search."})

    no_repeat_ngram_size: int = field(default=3, metadata={"help": 
        "All ngrams of that size can occur only once"})

    partial_tie_weights: bool = field(default=False, metadata={"help":
        "Whether to use partial tie weights."})

    copy_attention_to_cross_attention: bool = field(default=False, metadata=
        {"help" : "Whether to initalise the cross-attention weights from the "
        "attention weights."})

@dataclass
class APETrainingArguments(Seq2SeqTrainingArguments):
    """ Training arguments to run the **ape.py** python script. """

    report_to: str = field(default_factory= lambda: ["tensorboard", "wandb"],
        metadata={"help": "Backend used for logging."})

    output_dir: str = field(default=None,
        metadata={"help": "The output directory where the model predictions \
        and checkpoints will be written to."})

    token_batching: bool = field(default=False, metadata={"help": "Whether to \
        compute the batch size on a sentence or token level"})

    batch_size_includes_padding: bool = field(default=True, metadata={"help": 
        "Whether to include the padding tokens into the total batch size when \
        token_batching == True"})

    do_hyperparameter_search: bool = field(default = False, metadata={"help": 
        "Whether to perform a hyperparameter search"})

    hypersearch_space: Dict = field(default_factory = lambda:
        {"num_train_epochs": [2, 3, 4, 5]}, metadata={"help": "The space over \
        which to perform the hyperparameter search."})

    hypersearch_trials: int = field(default=10, metadata={"help": 
        "The number of trial runs to test in the hyperparameter search."})

    hypersearch_objective: Optional[str] = field(default=None, metadata={"help": 
        "The metric to optimize in the hyperparameter search."})

    prediction_columns_to_include: Optional[Union[List[str], str, Tuple[str],
        List[Tuple[str]]]] = field(default=None, metadata={"help": "Columns \
        from dataset to additionally include into the predictions csv."})

    prediction_csv_kwargs: Dict = field(default_factory = lambda: {"sep": ","},
        metadata={"help": "Keyword arguments when while writing the \
        predictions csv (can be used for setting delimiter, ...)"})

    use_garbage_collector_callback: bool = field(default=False,
        metadata={"help": "Whether to use the garbage colellector callback \
        -> trade speed vs. slight memory performance"})

    train_eval_samples: int = field(default=None,
        metadata={"help": "Number of train samples to evaluate during \
        evaluation"})

    text_metric_identifier: str = field(default="text_",
        metadata={"help": "Tag used to identify text metrics, i.e. predictions "
        "and labels"})

    extend_dirs_with_run_name:bool = field(default=False, metadata={"help":
        "Whether to extend output_dir and logging_dir paths with run_name."})
@dataclass
class APEDataArguments:
    """ Data arguments to run the **ape.py** python script. """
    name: str = field(default='ape', metadata={
        "help": "Task to perform, either 'ape' or 'mt'",
        "choices": ["ape", "mt"]})

    data_dir: str = field(default=None, metadata={
        "help": "Path to the folder with the data splits."})

    terminology_method: str = field(default=None, metadata={
        "help": "Method to use to encode terms within source sentence.",
        "choices": [None, "append", "replace"]})

    terminology_term: str = field(default="~", metadata={
        "help": "Term used to encode terminology, e.g. src_term~tgt_term"})

    src_lang: str = field(default="fr", metadata={
        "help": "Source language"})
        
    tgt_lang: str = field(default="en", metadata={
        "help": "Target language"})

    terminology_dir: str = field(default=None, metadata={
        "help": "Directory to the same data with terminology. Can be used to "
        "compute the term frequency for the baseline."})

    max_samples: int = field(default=None, metadata={
        "help": "Maximal samples within a dataset."})
    
    src_max_len: int = field(default=250, metadata={"help": 
        "Maximal length of source tokens."})

    tgt_max_len: int = field(default=200, metadata={"help": 
        "Maximal length of target tokens."})

    loss_ignore_label_id: int = field(default=-100, metadata={"help":
        "Label id for which loss function does not compute the loss for."})
    

@dataclass
class APETestCaseArguments:
    """ Test arguments to run the **ape.py** python script. In case of
    *APEArguments.run_as_test_case == True*. """
    
    train_size: int = field(default=120,
        metadata={"help": "The train dataset size for a test case."})

    valid_size: int = field(default=30,
        metadata={"help": "The validation dataset size for a test case."})

    test_size: int = field(default=30,
        metadata={"help": "The test dataset size for a test case."})

@dataclass
class APEPrepareData:
    """ Argument to run the **prepare_data.py** script. """

    src: str = field(default = "tbd", metadata={"help": "Source file."})

    mt: str = field(default = "tbd", metadata={"help": "MT file."})

    pe: str = field(default = "tbd", metadata={"help": "Post-edited file."})

    save_dir: str = field(default = "tbd", metadata={
        "help": "Where to save the computed files."})

    word_tokenize: bool = field(default = True, metadata={
        "help": "Whether to word-tokenize the texts in the files."})

    aggressive_dash_splits: bool = field(default = True, metadata={
        "help": "Whether to apply agressive dash splitting rules."})

    processes: int = field(default = 16, metadata={
        "help": "Number of processes for word tokenizing."})

    terminology_encode: bool = field(default = False, metadata={
        "help": "Whether to add dictionnary terms to source."})

    use_lemma: bool = field(default = True, metadata={
        "help": "Whether to use lemma's terminologies within SRC."})

    min_sentence_threshold: float = field(default = 0.0, metadata={
        "help": "Min sentence level annotation threshold."})

    max_sentence_threshold: float = field(default = 1.0, metadata={
        "help": "Max sentence level annotation threshold."})

    alignments: str = field(default = None, metadata={
        "help": "Alignment file SRC/PE."})

    batch_size: int = field(default = 32, metadata={
        "help": "Word alignment batch size."})

    source_language: str = field(default = "de", metadata={
        "help": "Source language of the APE."})

    target_language: str = field(default = "en", metadata={
        "help": "Target language of the APE."})

    dev_test_size: float = field(default = 0.2, metadata={
        "help": "Size of dev+test split."})

    test_size: float = field(default = 0.5, metadata={
        "help": "Size of test split within dev+test split."})

    text_min_length: float = field(default= 5, metadata={
        "help": "Minimum length of each text sample."})

    mt_only: bool = field(default=False, metadata={
        "help": "Whether to prepare only the .mt files."})

    clean: bool = field(default=True, metadata={
        "help": "Whether to clean the data."})