
# Automatic Post-Editing Model

Cconstrained automated post editing (cAPE) as described in "Training Neural Machine Translation To Apply Terminology Constraints" (Dinu et al. 2019). Constrained APE allows to enforce translations for specific words by providing them in form of a dictionnary(src term -> tgt term). Moreover, the method is slightly adapted to allow the model to inflect the desired target terms directly within the translation step as described in "Facilitating Terminology Translation with Target Lemma Annotations" (Bergmanis et al. 2021). The inflection and enforcement of the translation terms is trained in an unsupervised way. A specific dictionary for the desired translation terms has only to be provided at inference.

## Setup

Make a virtual environment and install pytorch and all the packages in the requirements.txt  
(`pip install -r requirements.txt`)  

## Workflow

Although we focus on APE models, we allow for constrained terminology models for APE and MT model.

Thus, given:
-  a tuple of text files **(src, mt)** [source, machine translation] for MT
-  a triple of text files **(src, mt, ape)** [source, machine translation, automated post edit] for APE

with corresponding sentences on each line, the workflow looks as following:
1. Prepare the data the data using ```prepare_data.py``` 
     - word tokenization
     - unsupervised terminology encoding
     - split data into train/dev/test

```bash
    python3 prepare_data.py --config mtc_ape_model/configs/prepare/escape_baseline.json
```

2. Train and/or evaluate a model using ```train.py```
    - possibility to train only
    - possibility to evaluate only
    - possiblity to use pretrained bert models

```bash
    python3 train.py --config mtc_ape_model/configs/example.json
```

**INFO:** Existing config files can be found within the config folder. Fields starting with an underscore are ignored (can be used as comments within the config files). For more details about the possible arguments within the config file please refer to ```mtc_ape_model/utils/arguments.py``` and the huggingface standard arguments for its Trainer class.
