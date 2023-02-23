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

from typing import Optional

from transformers import (AutoModel, AutoModelForCausalLM, EncoderDecoderModel,
    PreTrainedModel, PretrainedConfig)
from transformers.models.encoder_decoder.configuration_encoder_decoder import \
    EncoderDecoderConfig
from transformers.utils import logging

from .base_model import BaseModel
from .embeddings import FactorBertEmbeddings
from mtc_ape_model.data.tokenizer import MT_FACTOR

logger = logging.get_logger(__name__)

model_type_to_factor_embeddings = {
    "bert": FactorBertEmbeddings,
}


class FactorEncoderDecoderConfig(EncoderDecoderConfig):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for key in ["factor_embed_dim", "factors_in_encoder",
                    "factors_in_decoder", "n_factors", "use_token_type_ids",
                    "partial_tie_weights", "copy_attention_to_cross_attention"]:
            if key in kwargs:
                setattr(self, key, kwargs.pop(key))
            assert (hasattr(self, key))

    @classmethod
    def from_config(cls, config):
        if isinstance(config, EncoderDecoderConfig):
            config.__class__ = FactorEncoderDecoderConfig
        return config


class FactorEncoderDecoderModel(BaseModel, EncoderDecoderModel):
    config_class = FactorEncoderDecoderConfig
    DEFAULT_FACTOR_EMBED_DIM = 8

    def __init__(
            self,
            config: Optional[PretrainedConfig] = None,
            encoder: Optional[PreTrainedModel] = None,
            decoder: Optional[PreTrainedModel] = None
    ):
        if config is not None:
            config = FactorEncoderDecoderConfig.from_config(config)
        assert config is not None or (
                encoder is not None and decoder is not None
        ), ("Either a configuration or an encoder+decoder has to be provided")

        if not (config.factors_in_encoder or config.factors_in_decoder) and \
                config.n_factors > 0:
            config.n_factors = 0
            logger.info("Set n_factors to 0 as no factor embeddings are used.")

        # wait_for_tie_weigts

        # super(EncoderDecoderModel, self).__init__(config)

        # Update configs if necessary
        if config is None:
            encoder.config, decoder.config = self.update_submodule_configs(
                encoder.config, decoder.config, config)
            config = EncoderDecoderConfig.from_encoder_decoder_configs(
                encoder.config, decoder.config)
        else:
            config.encoder, config.decoder = self.update_submodule_configs(
                config.encoder, config.decoder, config)
            assert isinstance(config, EncoderDecoderConfig), f"config: \
                {config} has to be of type EncoderDecoderConfig"

        # Initialize with config
        self.wait_for_tie_weigts = True
        super().__init__(config)
        self.wait_for_tie_weigts = False

        # Encoder embeddings to factor embeddings
        if encoder is None:
            encoder = AutoModel.from_config(config.encoder)

        assert (encoder.config.model_type in
                model_type_to_factor_embeddings), NotImplementedError
        encoder_model = self.get_base_model(encoder)
        encoder_model.embeddings = model_type_to_factor_embeddings[
            config.encoder.model_type].from_embeddings(config.encoder,
                encoder_model.embeddings, is_encoder=True)

        # Decoder embeddings to factor embeddings
        if decoder is None:
            decoder = AutoModelForCausalLM.from_config(config.decoder)

        assert (decoder.config.model_type in
                model_type_to_factor_embeddings), NotImplementedError
        decoder_model = self.get_base_model(decoder)
        decoder_model.embeddings = model_type_to_factor_embeddings[
            config.encoder.model_type].from_embeddings(config.decoder,
                decoder_model.embeddings, is_encoder=False)

        self.encoder = encoder
        self.decoder = decoder

        if self.encoder.config.to_dict() != self.config.encoder.to_dict():
            logger.warning(
                f"Config of the encoder: {self.encoder.__class__} "
                "is overwritten by shared encoder config: {self.config.encoder}"
            )
        if self.decoder.config.to_dict() != self.config.decoder.to_dict():
            logger.warning(
                f"Config of the decoder: {self.decoder.__class__} "
                "is overwritten by shared decoder config: {self.config.decoder}"
            )

        # Make sure that the individual model's config refers to the shared
        # config so that the updates to the config will be synced
        self.encoder.config = self.config.encoder
        self.decoder.config = self.config.decoder

        assert (
                self.encoder.get_output_embeddings() is None
        ), "The encoder {} should not have a LM Head. \
            Please use a model without LM Head"

        self.tie_weights(is_init=True)

    @classmethod
    def from_encoder_decoder_pretrained(
            cls,
            encoder_pretrained_model_name_or_path: str = None,
            decoder_pretrained_model_name_or_path: str = None,
            *model_args,
            adapt_hidden_layer_size=False,  # added
            adapted_hidden_layer_save_folder="mtc_ape_model/checkpoints",
            **kwargs
    ) -> PreTrainedModel:
    
        if adapt_hidden_layer_size:
            encoder_pretrained_model_name_or_path = cls.adapt_hidden_layer_size(
                encoder_pretrained_model_name_or_path,
                kwargs.get("factor_embed_dim", 0),
                adapted_hidden_layer_save_folder)
            decoder_pretrained_model_name_or_path = cls.adapt_hidden_layer_size(
                decoder_pretrained_model_name_or_path,
                kwargs.get("factor_embed_dim", 0),
                adapted_hidden_layer_save_folder)

        return super().from_encoder_decoder_pretrained(
            encoder_pretrained_model_name_or_path,
            decoder_pretrained_model_name_or_path,
            *model_args, **kwargs)

    def forward(
            self,
            input_ids=None,
            attention_mask=None,
            token_type_ids=None,  # added
            factor_ids=None,  # added
            decoder_input_ids=None,
            decoder_attention_mask=None,
            decoder_token_type_ids=None,  # added
            decoder_factor_ids=None,  # added
            encoder_outputs=None,
            past_key_values=None,
            inputs_embeds=None,
            decoder_inputs_embeds=None,
            labels=None,
            use_cache=None,
            output_attentions=None,
            output_hidden_states=None,
            return_dict=None,
            **kwargs,
    ):

        return super().forward(
            input_ids=input_ids,
            attention_mask=attention_mask,
            decoder_input_ids=decoder_input_ids,
            decoder_attention_mask=decoder_attention_mask,
            encoder_outputs=encoder_outputs,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            decoder_inputs_embeds=decoder_inputs_embeds,
            labels=labels,
            use_cache=use_cache,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
            token_type_ids=token_type_ids,  # added
            position_ids=factor_ids,  # added / hack
            decoder_token_type_ids=decoder_token_type_ids,  # added
            decoder_position_ids=decoder_factor_ids,  # added / hack
            **kwargs)

    def prepare_inputs_for_generation(self, input_ids, past=None,
            attention_mask=None, use_cache=None, encoder_outputs=None, **kwargs):
        decoder_inputs = self.decoder.prepare_inputs_for_generation(
            input_ids, past=past)
        decoder_input_ids = decoder_inputs["input_ids"]
        decoder_past_values = decoder_inputs["past_key_values"]
        decoder_attention_mask = decoder_inputs["attention_mask"] if \
            "attention_mask" in decoder_inputs else None
        decoder_position_ids = decoder_attention_mask.new_ones(
            decoder_inputs["input_ids"].shape) * MT_FACTOR \
                if decoder_attention_mask is not None else None

        input_dict = {
            "attention_mask":         attention_mask,
            "decoder_attention_mask": decoder_attention_mask,
            "decoder_factor_ids":     decoder_position_ids,
            "decoder_input_ids":      decoder_input_ids,
            "encoder_outputs":        encoder_outputs,
            "past_key_values":        decoder_past_values,
            "use_cache":              use_cache,
        }
        return input_dict

    def update_submodule_configs(self, encoder_config, decoder_config,
                                 encoder_decoder_config):

        # Shared
        for key in ["n_factors", "use_token_type_ids"]:
            if not hasattr(encoder_config, key):
                setattr(encoder_config, key, getattr(encoder_decoder_config, key))
            if not hasattr(decoder_config, key):
                setattr(decoder_config, key, getattr(encoder_decoder_config, key))

        # Encoder / Decoder - whether to use embeddings
        if not hasattr(encoder_config, "use_factor_embeddings"):
            setattr(encoder_config, "use_factor_embeddings",
                    encoder_decoder_config.factors_in_encoder)

        if not hasattr(decoder_config, "use_factor_embeddings"):
            setattr(decoder_config, "use_factor_embeddings",
                    encoder_decoder_config.factors_in_decoder)

        # Encoder / Decoder - size of embedding
        if not hasattr(encoder_config, "factor_embed_dim"):
            encoder_config.factor_embed_dim = max(
                encoder_decoder_config.factor_embed_dim,
                FactorEncoderDecoderModel.DEFAULT_FACTOR_EMBED_DIM if
                (encoder_config.use_factor_embeddings or
                 decoder_config.use_factor_embeddings) else 0)

        if not hasattr(decoder_config, "factor_embed_dim"):
            decoder_config.factor_embed_dim = max(
                encoder_decoder_config.factor_embed_dim,
                FactorEncoderDecoderModel.DEFAULT_FACTOR_EMBED_DIM if
                (encoder_config.use_factor_embeddings or
                 decoder_config.use_factor_embeddings) else 0)

        # Init method for the factor embeddings
        if not hasattr(encoder_config, "factor_embedding_init_method"):
            encoder_config.factor_embedding_init_method = \
                getattr(encoder_decoder_config, "factor_embedding_init_method",
                    "xavier_normal")
        
        if not hasattr(decoder_config, "factor_embedding_init_method"):
            decoder_config.factor_embedding_init_method = \
                getattr(encoder_decoder_config, "factor_embedding_init_method",
                    "xavier_normal")

        return encoder_config, decoder_config

    def tie_weights(self, is_init=False):
        """ Ties weights across the model. Only copy attention to
        cross_attention if this method is called from init. Not when the
        weights are tied during the loading of a model. """

        if hasattr(self, "wait_for_tie_weigts"):
            if self.wait_for_tie_weigts:
                return

        if self.config.tie_encoder_decoder:
            if not self.config.partial_tie_weights:
                super().tie_weights()
            else:
                self.tie_partial_weights()

        if self.config.copy_attention_to_cross_attention and is_init:
            self.copy_attention_cross_attention_weights()
