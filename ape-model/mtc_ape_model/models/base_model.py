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
import torch
from torch import nn
from transformers import PreTrainedModel, AutoConfig, AutoModel

from transformers import logging
from typing import List

logger = logging.get_logger(__name__)

class BaseModel():
    """ Helper methods for EncoderDecoder subclasses. This class can be 
    additionally subclassed by EncoderDecoder subclasses for further 
    functionalities. """
    
    @classmethod
    def get_base_model(cls, instance):
        """ Get the underlying base model of the Seq2Seq model. """
        if not hasattr(instance, "embeddings"):
            try:
                # Get first element from modules list
                first_module = instance._modules[
                    next(iter(instance._modules))]
                if isinstance(first_module, PreTrainedModel):
                    base_model = first_module
            except:
                raise RuntimeError("Could not determine base model.")
        else:
            base_model = instance
        return base_model
    
    @classmethod
    def adapt_hidden_layer_size(cls, pretrained_model_name_or_path,
            extra_hidden_layers=12,
            adapted_hidden_layer_save_folder="mtc_ape_model/checkpoints"):
        """ Changes the dimension of hidden layers of the model at
        `pretrained_model_name_or_path`. """

        # Check whether it already exists
        config = AutoConfig.from_pretrained(pretrained_model_name_or_path)
        new_hidden_size=config.hidden_size+extra_hidden_layers
        path = os.path.join(adapted_hidden_layer_save_folder,
            pretrained_model_name_or_path + "_" + "hidden-" + 
            str(new_hidden_size))

        if os.path.isdir(path):
            return path
            
        model = AutoModel.from_pretrained(pretrained_model_name_or_path)
        old_hidden_size = model.config.hidden_size
        for name, parameter in model.named_parameters():
            if old_hidden_size in parameter.data.shape:
                for dim in [ind for ind, dim_len in enumerate(
                        parameter.data.shape) if dim_len == old_hidden_size]:
                    data = parameter.data.detach().clone()
                    if old_hidden_size < new_hidden_size:
                        copy_length = (new_hidden_size - old_hidden_size)
                        start_index = old_hidden_size - copy_length
                        data = torch.cat([data, torch.narrow(data, dim, 
                            start_index, copy_length)], dim=dim)
                    else:
                        data = torch.narrow(data, dim, 0, new_hidden_size)
                    parameter.data = nn.parameter.Parameter(data,
                        requires_grad=parameter.requires_grad)

        model.config.hidden_size = new_hidden_size
        model.save_pretrained(path)
        del model
        return path

    @staticmethod
    def count_params(model, filter=None):
        """ Counts the number of parameters. """
        params = 0
        for name, param in model.named_parameters():
            if filter:
                if filter(name):
                    params += param.nelement()
            else:
                params += param.nelement()
        return params

    def clone_or_share_layer(self, layer1, layer2, share=False):
        """ Clones/shares a layer. """
        if share:
            layer1.weight, layer1.bias = layer2.weight, layer2.bias
        else:
            layer1.weight, layer1.bias = \
                nn.Parameter(
                    layer2.weight.clone()), nn.Parameter(layer2.bias.clone())

    def tie_partial_weights(self):
        # Tie input/output embeddings
        output_embeddings = self.decoder.get_output_embeddings()
        if output_embeddings is not None and self.config.tie_word_embeddings:
            self._tie_or_clone_weights(output_embeddings,
                self.encoder.get_input_embeddings())

        # tie encoder & decoder if needed
        if self.config.tie_encoder_decoder:
            # tie encoder and decoder base model
            decoder_base_model_prefix = self.decoder.base_model_prefix
            self._tie_partial_encoder_decoder_weights(
                self.encoder, self.decoder._modules[decoder_base_model_prefix],
                self.decoder.base_model_prefix
            )

    @staticmethod
    def _tie_partial_encoder_decoder_weights(encoder: nn.Module,
            decoder: nn.Module, base_model_prefix: str):

        uninitialized_encoder_weights: List[str] = []
        if decoder.__class__ != encoder.__class__:
            logger.info(
                f"{decoder.__class__} and {encoder.__class__} are not equal. "
                "In this case make sure that all encoder weights are correctly "
                "initialized."
            )

        def tie_encoder_to_decoder_recursively(
            decoder_pointer: nn.Module,
            encoder_pointer: nn.Module,
            module_name: str,
            uninitialized_encoder_weights: List[str],
            depth=0,
            do_tie=False
        ):
            if do_tie:
                assert isinstance(decoder_pointer, nn.Module) and isinstance(
                    encoder_pointer, nn.Module
                ), f"{decoder_pointer} and {encoder_pointer} "\
                    "have to be of type nn.Module"
                if hasattr(decoder_pointer, "weight"):
                    assert hasattr(encoder_pointer, "weight")
                    decoder_pointer.weight = encoder_pointer.weight
                    if hasattr(decoder_pointer, "bias"):
                        assert hasattr(encoder_pointer, "bias")
                        decoder_pointer.bias = encoder_pointer.bias
                    return

            encoder_modules = encoder_pointer._modules
            decoder_modules = decoder_pointer._modules
            if len(decoder_modules) > 0:
                assert (
                    len(encoder_modules) > 0
                ), f"Encoder module {encoder_pointer} does not match decoder "\
                    "module {decoder_pointer}"

                all_encoder_weights = set([module_name + "/" + sub_name for
                    sub_name in encoder_modules.keys()])
                encoder_layer_pos = 0
                for name, module in decoder_modules.items():
                    if name.isdigit():
                        encoder_name = str(int(name) + encoder_layer_pos)
                        decoder_name = name
                        if not isinstance(decoder_modules[decoder_name],
                                type(encoder_modules[encoder_name])) and len(
                            encoder_modules
                        ) != len(decoder_modules):
                            # this can happen if the name corresponds to 
                            # the position in a list module list of layers
                            # in this case the decoder has added a 
                            # cross-attention that the encoder does not have
                            # thus skip this step and subtract one layer 
                            # pos from encoder
                            encoder_layer_pos -= 1
                            continue
                    elif name not in encoder_modules:
                        continue
                    elif depth > 500:
                        raise ValueError(
                            "Max depth of recursive function "
                            "`tie_encoder_to_decoder` reached. It seems that "
                            "there is a circular dependency between two or "
                            "more `nn.Modules` of your model."
                        )
                    else:
                        decoder_name = encoder_name = name
                    
                    predicate = ("attention" in name and 
                        not "crossattention" in name) or "embeddings" in name

                    tie_encoder_to_decoder_recursively(
                        decoder_modules[decoder_name],
                        encoder_modules[encoder_name],
                        module_name + "/" + name,
                        uninitialized_encoder_weights,
                        depth=depth + 1,
                        do_tie=do_tie or predicate
                    )
                    if do_tie or predicate:
                        all_encoder_weights.remove(module_name+"/"+encoder_name)

                uninitialized_encoder_weights += list(all_encoder_weights)

        # tie weights recursively
        tie_encoder_to_decoder_recursively(decoder, encoder, base_model_prefix,
            uninitialized_encoder_weights)
        if len(uninitialized_encoder_weights) > 0:
            logger.warning(
                f"The following encoder weights were not tied to the decoder "
                f"{uninitialized_encoder_weights}"
            )

    def tie_encoder_decoder_weights_v2(self):

        self.decoder.bert.embeddings.word_embeddings.weight = \
            self.encoder.embeddings.word_embeddings.weight
        
        self.decoder.bert.embeddings.token_type_embeddings.weight = \
            self.encoder.embeddings.token_type_embeddings.weight

        for enc_layer, dec_layer in zip(self.encoder.encoder.layer,
                self.decoder.bert.encoder.layer):
            # Selfattn
            self.clone_or_share_layer(
                dec_layer.attention.self.query,
                enc_layer.attention.self.query,
                share=True)
            self.clone_or_share_layer(
                dec_layer.attention.self.key,
                enc_layer.attention.self.key,
                share=True)
            self.clone_or_share_layer(
                dec_layer.attention.self.value,
                enc_layer.attention.self.value,
                share=True)
            self.clone_or_share_layer(
                dec_layer.attention.output.dense,
                enc_layer.attention.output.dense,
                share=True)

            ## FF
            self.clone_or_share_layer(
                dec_layer.intermediate.dense,
                enc_layer.intermediate.dense,
                share=True)
            self.clone_or_share_layer(
                dec_layer.output.dense,
                enc_layer.output.dense,
                share=True)

        self.copy_attention_cross_attention_weights()

        self.decoder.cls.predictions.decoder.weight = \
            self.decoder.bert.embeddings.word_embeddings.weight

        for p in self.parameters():
            if p.dim() > 1:
                torch.nn.init.xavier_uniform_(p)
    
    def copy_attention_cross_attention_weights(self):
        for layer in self.decoder.bert.encoder.layer:
            # Crossattn
            self.clone_or_share_layer(
                layer.crossattention.self.query,
                layer.attention.self.query,
                share=False)
            self.clone_or_share_layer(
                layer.crossattention.self.key,
                layer.attention.self.key,
                share=False)
            self.clone_or_share_layer(
                layer.crossattention.self.value,
                layer.attention.self.value,
                share=False)
            self.clone_or_share_layer(
                layer.crossattention.output.dense,
                layer.attention.output.dense,
                share=False)
