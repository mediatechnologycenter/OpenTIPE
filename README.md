![ETH MTC HEADER](./assets/ETHMTCHeaderOriginal.png)

# OpenTIPE: An Open-source Translation Framework for Interactive Post-Editing Research

OpenTIPE is a flexible and extensible framework that aims at supporting research on interactive post-editing. OpenTIPE’s interactive environment allows researchers to explore human-centered approaches for the post-editing task.

## Git Submodules
For convenience, this project includes any external repositories it relies on as submodules.

In order to make sure all submodules have been initialized and are up-to-date, clone the repository with one of the following commands:
```bash
git clone --recursive {REPO_URL}
# Or
git clone --recurse-submodules {REPO_URL}
```

In order to update all repositories, execute the following command:
```bash
git pull --recurse-submodules
```

## Deployment using docker-compose

1. Make sure nvidia-docker is installed and the mtc docker repository is registered with it, by following [Installation and GPU setup (Linux based systems)](https://gitlab.ethz.ch/mtc/development-guidelines/-/blob/master/Docker/readme.md#install-docker).
2. Pull required images from various docker repositories by running the following command from the repository root:
    ```bash
    docker-compose pull
    ```
3. Start the service with one of the following configurations, depending on your use case:
    - Production deployment:
        * Make sure the host machine has a public IP address
        * Make sure a DNS entry is configured to point to the host machine's public IP
        * Configure the DNS hostname in the `.env` file as follows:
            ```
            BASE_URL={BASE_URL}
            ```
        * Run the following commands:
            ```bash
            # vanila docker commands
            docker-compose up -d
            # if you have the mtc aliases set up, you can use the following instead:
            dcup -d
            ```

    - Start a local debug server without making it available to the internet
        ```bash
        # vanila docker commands
        docker-compose -f docker-compose.yml -f docker-compose-debug.yml up
        # if you have the mtc aliases set up, you can use the following instead:
        dcdebug up --build
        ```

    - Start test server and run automated tests against it:
        ```bash
        # vanila docker commands
        docker-compose -f docker-compose.yml -f docker-compose-tests.yml up --abort-on-container-exit
        # if you have the mtc aliases set up, you can use the following instead:
        dctestsup --build
        ```

## Configuration
Any configuration can be done in the `.env` file prior to starting docker-compose.

The following configurations are supported:
| Env variable | description |
| ------------ | ----------- |
| APE_MODEL_URL_DIR | The URL to the productive APE model directory |
| MT_MODEL | Choose between `DeepL`, `HuggingFace` & `FairSeq` implementations of the machine translation model |
| MT_MODEL_NAME | If HuggingFace or FairSeq are chosen for the `MT_MODEL`, choose an applicable model checkpoint.<br/>HF Examples: Helsinki-NLP/opus-mt-de-en \| (Helsinki-NLP/opus-mt-ine-ine)<br/>Fairseq Options: transformer.wmt19.de-en \| transformer.wmt14.de-en |
| DEEPL_API_KEY | This Variable must be exposed in your environment files |
| USR | This Variable must be exposed in your environment files |
| PWD | This Variable must be exposed in your environment files 
| AUTH_ENABLED | Enable/disable Firebase bearer token authentication by setting this variable to `True`/`False` respectively |
| FIREBASE_ADMIN_CREDENTIALS_URL | URL to the firebase admin credential file |
| GPU | Enable/disable GPU support by setting this variable to 0/-1 respectively |

In order to control, which service starts a debug server, the docker-compose-debug.yml file can be edited ➡ Set the DEBUG env value of the respective service to True, and the remaining ones to False.

## CPU Only deployment
In case you want to deploy the APE project using docker but without a GPU, perform the following actions:

* Set `GPU=-1` in the `.env` file as explained under [Configuration](#configuration)
* Comment the following block from the `docker-compose.yaml` file:
    ```yaml
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [ gpu ]
    ```
    This block is used to give a service access to the GPU but errors if there is no GPU available.

