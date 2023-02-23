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

import multiprocessing
from typing import Union

import debugpy


def initialize_api_debugger(debug_port: Union[int, str]):
    if multiprocessing.current_process().pid > 1:
        if debug_port is None:
            raise RuntimeError("debug_port is None")

        debug_port = int(debug_port)
        debugpy.listen(("0.0.0.0", debug_port))
        print("⏳ Debugging server is running on port {}. VS Code debugger can now be attached, press F5 in VS Code ⏳".format(debug_port), flush=True)
        debugpy.wait_for_client()
        print("🎉 VS Code debugger attached, enjoy debugging 🎉", flush=True)
