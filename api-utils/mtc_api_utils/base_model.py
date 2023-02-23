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

import warnings
from abc import ABC, abstractmethod
from threading import Thread
from time import sleep


class MLBaseModel(ABC):
    def __init__(self):
        print("Initializing model asynchronously")
        self.init_thread = Thread(target=self.init_model)
        self.init_thread.start()

    def __wait_until_ready__(self):
        """Only use this method for testing as it negates the benefits of having an asynchronous initialization"""
        warnings.warn("Waiting for model to be ready. Only use this method for testing as it negates the benefits of having an asynchronous initialization")
        while not self.is_ready():
            sleep(1)

    @abstractmethod
    def init_model(self):
        raise NotImplemented

    def is_ready(self) -> bool:
        """ Returns true only if the model is initialized and ready to perform inference. Defaults to checking the init_model() method has completed asynchronously. """
        return not self.init_thread.is_alive()

    @abstractmethod
    def inference(self, *args, **kwargs):
        raise NotImplemented
