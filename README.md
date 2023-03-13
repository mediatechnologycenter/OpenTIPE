![ETH MTC HEADER](./assets/ETHMTCHeaderOriginal.png)

# OpenTIPE: An Open-source Translation Framework for Interactive Post-Editing Research

OpenTIPE is a flexible and extensible framework designed to support research on interactive post-editing. With an interactive environment, OpenTIPE allows researchers to explore human-centered approaches to the post-editing task.

In order to see the tool in action, we encourage the reader to take a look at the following resources:

- [Two minute walkthrough video](https://youtu.be/G3Hb8_hnKIk)
- [Interactive online demo](https://www.opentipe-demo.com/)

## Deployment using docker-compose

- Start test server:
  ```bash
  docker compose up --build
  ```
- Start the automated tests:
  ```bash
  docker compose -f docker-compose.yml -f docker-compose-tests.yml up --build --abort-on-container-exit
  ```

## Configuration

### Backend/General

Any configuration can be done in the `.env` file prior to starting docker-compose.

The following configurations are supported:
| Env variable | description |
| ------------ | ----------- |
| MOCK_MODEL | If True, the models will return a predefined string instead of running a model |
| HARD_CODED_RESPONSE | If True, the models will return a hard coded string, if False it will return the input text |
| APE_MODEL_URL_DIR | The URL to the productive APE model directory |
| MT_MODEL | Choose between `DeepL`, `HuggingFace` & `FairSeq` implementations of the machine translation model |
| MT_MODEL_NAME | If HuggingFace or FairSeq are chosen for the `MT_MODEL`, choose an applicable model checkpoint.<br/>HF Examples: Helsinki-NLP/opus-mt-de-en \| (Helsinki-NLP/opus-mt-ine-ine)<br/>Fairseq Options: transformer.wmt19.de-en \| transformer.wmt14.de-en |
| DEEPL_API_KEY | This Variable must be exposed in your environment files |
| AUTH_ENABLED | Enable/disable Firebase bearer token authentication by setting this variable to `True`/`False` respectively |
| GPU | Enable/disable GPU support by setting this variable to 0/-1 respectively |

### Frontend

Any frontend-related configuration can be done in `frontend.env`. Please refer directly to the file to see the available variables and their descriptions.

## CPU Only deployment

In case you want to run OpenTIPE using docker with a GPU, perform the following actions:

- Set `GPU=0` in the `.env` file as explained under [Configuration](#configuration)
- Uncomment the following block from the `docker-compose.yaml` file:
  ```yaml
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
  ```
  This block is used to give a service access to the GPU but raises an error if there is no GPU available.

## Using custom models

There are two ways to make this project run with your own models:

### Use existing architecture and add custom weights

For licencing reasons we cannot provide our trained APE models. However, you can provide your own model files to the APE service in order to use the provided APE model architecture as follows:

- In the `.env` file, set `MOCK_MODEL=False`
- Create a directory in `./model_data` for each model that you want to make available, e.g. `ape-model-huggingface-de-en`.
- Inside the newly created directory, place the following files:
  - `config.json`
  - `pytorch_model.bin`
  - `run_config.json`
  - `special_tokens_map.json`
  - `tokenizer_config.json`
  - `vocab.txt`

When you next start the application using docker compose, the machine translation (MT) and automatic post editing (APE) models should be loaded.

If you don't have access to these files, read the README.md in the `ape-model` directory in order to train the model.

### Add custom model code

If you want to add your own model code and weights, create your own service, analog to either `mt-model` or `ape-model` or simply edit the existing code for these services.
