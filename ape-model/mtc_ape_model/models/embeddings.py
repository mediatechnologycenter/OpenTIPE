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

from packaging import version

import torch
from torch import nn

from transformers.utils import logging
from transformers.models.bert.modeling_bert import BertEmbeddings
from mtc_ape_model.data.tokenizer import (SRC_FACTOR, SRC_ORIGINAL_FACTOR,
    SRC_MT_FACTOR, MT_FACTOR)

logger = logging.get_logger(__name__)

class FactorBertEmbeddings(BertEmbeddings):
    
    """Construct the embeddings from word, position, factors and token_type
    embeddings."""

    def __init__(self, config, is_encoder=False):
        """
        config.factor_embed_dim=12 : How large the embeddings (0 - no emb)
        config.n_factors=0 : How many tokens within factor embeddings
        config.factors_in_encoder=True : Whether to use factors in the encoder
        config.factors_in_decoder=False : Whether to use factors in the decoder
        config.use_token_type_ids=True : Whether to use token_type_ids
        """
        
        super(BertEmbeddings, self).__init__()
        
        self.is_encoder = is_encoder

        self.word_embeddings = nn.Embedding(config.vocab_size,
            config.hidden_size-config.factor_embed_dim,
            padding_idx=config.pad_token_id)
        
        self.position_embeddings = nn.Embedding(
            config.max_position_embeddings, config.hidden_size)
        
        self.use_token_type_ids = config.use_token_type_ids
        if self.use_token_type_ids:
            self.token_type_embeddings = nn.Embedding(
                config.type_vocab_size, config.hidden_size)

        self.factor_embed_dim = config.factor_embed_dim
        self.use_factor_embeddings = config.use_factor_embeddings

        if self.use_factor_embeddings:
            
            # assert(config.num_attention_heads%config.factor_embed_dim == 0),\
            #     f"Invalid factor_embed_dim == {config.factor_embed_dim}"
            
            self.factor_embeddings = None
            if config.n_factors:
                self.factor_embeddings = nn.Embedding(config.n_factors,
                    config.factor_embed_dim)
                if not (config.factor_embedding_init_method in
                        ["xavier_uniform", "xavier_normal", "kaiming_uniform"]):
                    raise NotImplementedError
                if config.factor_embedding_init_method == "xavier_uniform":
                    torch.nn.init.xavier_uniform_(self.factor_embeddings.weight)
                if config.factor_embedding_init_method == "xavier_normal":
                    torch.nn.init.xavier_normal_(self.factor_embeddings.weight)
                if config.factor_embedding_init_method == "kaiming_uniform":
                    torch.nn.init.kaiming_uniform_(self.factor_embeddings.weight)

        # self.LayerNorm is not snake-cased to stick with TensorFlow model
        # variable name and be able to load any TensorFlow checkpoint file
        self.LayerNorm = nn.LayerNorm(config.hidden_size,
            eps=config.layer_norm_eps)
        self.dropout = nn.Dropout(config.hidden_dropout_prob)

        # position_ids (1, len position emb) is contiguous in memory and 
        # exported when serialized
        self.position_embedding_type = getattr(config,
            "position_embedding_type", "absolute")

        self.register_buffer("position_ids", torch.arange(
            config.max_position_embeddings).expand((1, -1)))

        if version.parse(torch.__version__) > version.parse("1.6.0"):
            self.register_buffer(
                "token_type_ids",
                torch.zeros(self.position_ids.size(), dtype=torch.long,
                device=self.position_ids.device), persistent=False)
    
    @classmethod
    def from_embeddings(cls, config, embeddings, is_encoder):
        emb = cls(config, is_encoder=is_encoder)

        emb.word_embeddings.weight.data.copy_(
            embeddings.word_embeddings.weight.data[:,
                :emb.word_embeddings.weight.shape[1]])

        emb.position_embeddings.weight.data.copy_(
            embeddings.position_embeddings.weight.data)

        if config.use_token_type_ids:
            emb.token_type_embeddings.weight.data.copy_(
                embeddings.token_type_embeddings.weight.data)
                
        return emb

    def forward(
        self, input_ids=None, token_type_ids=None, position_ids=None,
        inputs_embeds=None, past_key_values_length=0
    ):
        """ INFO: we missuse position_ids for factor_ids in order to keep the
        method signature the same and not to have to reimplement the 
        classes using this Embedding Class. You can add an additional arguments,
        however, you will have to forward this arguments throughout the classes
        that use the embedding. E.g. add a 'factor_ids' argument in every
        forward() method and forward this argument to here. """
        

        if input_ids is not None:
            input_shape = input_ids.size()
        else:
            input_shape = inputs_embeds.size()[:-1]

        seq_length = input_shape[1]

        if position_ids.shape[1] == 1:
            factor_ids = torch.ones_like(position_ids) * MT_FACTOR
            token_type_ids = torch.ones_like(token_type_ids) * MT_FACTOR
            position_ids += past_key_values_length
        else:
            factor_ids = position_ids
            assert(position_ids is not None)
            assert(inputs_embeds is None)
            assert(all(position_ids.cpu().numpy().flatten() <= max(
                SRC_FACTOR, SRC_ORIGINAL_FACTOR, SRC_MT_FACTOR, MT_FACTOR)))
            position_ids = None

            if position_ids is None:
                
                # Common to encoder/decoder
                position_ids = torch.arange(
                        seq_length,
                        dtype=torch.long,
                        device=input_ids.device)
                position_ids += past_key_values_length
                position_ids = position_ids.unsqueeze(0).expand_as(input_ids)

                # Encoder specific
                if self.is_encoder:
                    token_type = (token_type_ids == 1)
                    position_aux = ((token_type.cumsum(1) == 1) & token_type)
                    position_aux = position_aux.max(1)[1].unsqueeze(1)
                    position_aux = position_aux * token_type.clone()
                    position_ids = (position_ids - position_aux).detach()


        # Setting the token_type_ids to the registered buffer in constructor 
        # where it is all zeros, which usually occurs when its auto-generated, 
        # registered buffer helps users when tracing the model without passing 
        # token_type_ids, solves issue #5664
        if token_type_ids is None:
            if hasattr(self, "token_type_ids"):
                buffered_token_type_ids = self.token_type_ids[:, :seq_length]
                buffered_token_type_ids_expanded = \
                    buffered_token_type_ids.expand(input_shape[0], seq_length)
                token_type_ids = buffered_token_type_ids_expanded
            else:
                token_type_ids = torch.zeros(input_shape, dtype=torch.long,
                    device=self.position_ids.device)

        # Word embeddings
        if inputs_embeds is None:
            inputs_embeds = self.word_embeddings(input_ids)

        # Factor embeddings
        if self.use_factor_embeddings and self.factor_embed_dim != 0:
            factor_embeds = self.factor_embeddings(factor_ids)

        elif self.factor_embed_dim != 0:
            factors_shape = list(input_shape)
            factors_shape.append(self.factor_embed_dim)
            factor_embeds = torch.zeros(factors_shape, dtype=torch.long,
                    device=self.position_ids.device)

        else:
            embeddings = inputs_embeds

        # Word and factor append
        if self.factor_embed_dim != 0:
            embeddings = torch.cat((inputs_embeds, factor_embeds), dim=-1)

        # Token-type embeddings
        if self.use_token_type_ids:
            token_type_embeddings = self.token_type_embeddings(token_type_ids)
            embeddings += token_type_embeddings

        # Position embeddings
        if self.position_embedding_type == "absolute":
            position_embeddings = self.position_embeddings(position_ids)
            embeddings += position_embeddings

        # Norm + dropout
        embeddings = self.LayerNorm(embeddings)
        embeddings = self.dropout(embeddings)
        return embeddings