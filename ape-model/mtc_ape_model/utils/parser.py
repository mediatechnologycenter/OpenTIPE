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

import sys
import json
import dataclasses
from pathlib import Path

from typing import Tuple, List
from argparse import Namespace, SUPPRESS, _UNRECOGNIZED_ARGS_ATTR, ArgumentError

from transformers.hf_argparser import HfArgumentParser, DataClass

class APEParser(HfArgumentParser):
    """ Extensions to the Huggingface **HfArgumentParser** parser. It allows
    for multiple config files, where the latter ones overwrite the previous
    ones. 
    """

    def parse_known_args(self, args=None, namespace=None,
            with_default:bool = True):
        """ Based on parse_known_args `ArgumentParser.parse_known_args`.
        In addition to the initial method it allow for ignoring default 
        values - i.e. if the default value nothing is set instead of the 
        default value.

        Parameters
        ----------
        args:
            The arguments.
        namespace:
            The namespace to store the parsed arguments to.
        with_deafult:
            Whether to set default values if these are not present.
        """
        if args is None:
            # args default to the system args
            args = sys.argv[1:]
        else:
            # make sure that args are mutable
            args = list(args)

        # default Namespace built from parser defaults
        if namespace is None:
            namespace = Namespace()

        # add any action defaults that aren't present
        if with_default:
            for action in self._actions:
                if action.dest is not SUPPRESS:
                    if not hasattr(namespace, action.dest):
                        if action.default is not SUPPRESS:
                            setattr(namespace, action.dest, action.default)

        # add any parser defaults that aren't present
        if with_default:
            for dest in self._defaults:
                if not hasattr(namespace, dest):
                    setattr(namespace, dest, self._defaults[dest])

        # parse the arguments and exit if there are any errors
        try:
            namespace, args = self._parse_known_args(args, namespace)
            if hasattr(namespace, _UNRECOGNIZED_ARGS_ATTR):
                args.extend(getattr(namespace, _UNRECOGNIZED_ARGS_ATTR))
                delattr(namespace, _UNRECOGNIZED_ARGS_ATTR)
            return namespace, args
        except ArgumentError:
            err = sys.exc_info()[1]
            self.error(str(err))

    def parse_args_into_dataclasses_with_default(
        self, args: List[str] = None, return_remaining_strings: bool = False,
        look_for_args_file: bool = True, args_filename: str = None,
        json_default_files: List[str] = None) -> Tuple[DataClass, ...]:
        """
        Parse command-line args into instances of the specified dataclass types.

        This relies on argparse's `ArgumentParser.parse_known_args`.
        See the docat:
        docs.python.org/3.7/library/argparse.html#argparse.ArgumentParser.parse_args

        This method combines parse_args_into_dataclasses and parse_json_file
        from the Huggingface parser and allow additionaly to provide several
        json files.

        The order of priority in which the provided arguments are considered is:

            - cli arguments
            - last config file
            - ...
            - first config file
            - dataclass defaults

        Parameters
        ----------
        args:
            List of strings to parse. The default is taken from sys.argv.
            (same as argparse.ArgumentParser)
        return_remaining_strings:
            If true, also return a list of remaining argument strings.
        look_for_args_file:
            If true, will look for a ".args" file with the same base name as
            the entry point script for this process, and will append its
            potential content to the command line args.
        args_filename:
            If not None, will uses this file instead of the ".args" file
            specified in the previous argument.
        json_default_files:
            Paths to the config files

        Returns
        -------
        Tuple consisting of:

            - the dataclass instances in the same order as they were passed
              to the initializer.abspath
            - if applicable, an additional namespace for more (non-dataclass
              backed) arguments added to the parser after initialization.
            - The potential list of remaining argument strings. (same as
              argparse.ArgumentParser.parse_known_args)
        """
        if args_filename or (look_for_args_file and len(sys.argv)):
            if args_filename:
                args_file = Path(args_filename)
            else:
                args_file = Path(sys.argv[0]).with_suffix(".args")

            if args_file.exists():
                fargs = args_file.read_text().split()
                args = fargs + args if args is not None else \
                    fargs + sys.argv[1:]
                # in case of duplicate arguments the first one has precedence
                # so we append rather than prepend.

        if json_default_files:
            data_from_files = [json.loads(Path(i).read_text()) 
                for i in json_default_files]
            data = data_from_files[0]
            for i in data_from_files[1:]:
                data.update(i)
        
        namespace, remaining_args = self.parse_known_args(args=args,
            with_default=False)
        outputs = []

        for dtype in self.dataclass_types:
            keys = {f.name for f in dataclasses.fields(dtype) if f.init}
            inputs = {k: v for k, v in vars(namespace).items() if k in keys}
            for k in keys:
                if hasattr(namespace, k):
                    delattr(namespace, k)

            if json_default_files:
                keys = {f.name for f in dataclasses.fields(dtype) if f.init}
                default_inputs = {k: v for k, v in data.items() if k in keys}
                for key in default_inputs:
                    data.pop(key)
                default_inputs.update(inputs)
                inputs = default_inputs

            obj = dtype(**inputs)
            outputs.append(obj)

        if len(namespace.__dict__) > 0:
            # additional namespace.
            outputs.append(namespace)

        if json_default_files:
            remaining_args.extend(list([i for i in data.items()
                if i[0][0] != "_"]))

        if return_remaining_strings:
            return (*outputs, remaining_args)
        else:
            if remaining_args:
                raise ValueError(f"Some specified arguments are not used by \
                    the HfArgumentParser: {remaining_args}")

            return (*outputs,)