from typing import Literal

from torch import nn
from transformers import PreTrainedConfig, PreTrainedModel

from ..models import models, rnn
from ..tokenizer import BaseTokenizer, _default_special_tokens


class DummyTokenizer(BaseTokenizer):
    def __init__(self, vocab_size):
        self._vocab_size = vocab_size

        super().__init__(
            special_strings = _default_special_tokens,
            special_idxs = {k:i for i,k in enumerate(_default_special_tokens.keys())}
        )

    @property
    def vocab_size(self) -> int:
        return self._vocab_size

    def encode_text(self, text):
        raise RuntimeError("Called `DummyTokenizer.encode_text()`")

    def decode(self, tokens):
        raise RuntimeError("Called `DummyTokenizer.decode()`")


class TinyreasonerRNNConfig(PreTrainedConfig):
    model_type = "tinyreasoner_rnn"

    def __init__(
        self,
        vocab_size: int,
        emb_size: int,
        rnn_hidden_size: int,
        rnn_n_layers: int,
        head_hidden_size: int,
        rnn_type: Literal["rnn", "lstm", "gru"],
        rnn_dropout: float,
        head_dropout: float,
        **kwargs,
    ):
        self.vocab_size = vocab_size
        self.emb_size = emb_size
        self.rnn_hidden_size = rnn_hidden_size
        self.rnn_n_layers = rnn_n_layers
        self.head_hidden_size = head_hidden_size
        self.rnn_type = rnn_type
        self.rnn_dropout = rnn_dropout
        self.head_dropout = head_dropout
        super().__init__(**kwargs)

class TinyreasonerRNN(PreTrainedModel):
    config_class = TinyreasonerRNNConfig


    def __init__(self, config: TinyreasonerRNNConfig):
        super().__init__(config)
        rnn_cls = {
            "rnn": nn.RNN,
            "lstm": nn.LSTM,
            "gru": nn.GRU
        }[config.rnn_type]

        self.model = rnn.RNN(
            tokenizer = DummyTokenizer(config.vocab_size),
            embedding = nn.Embedding(config.vocab_size, config.emb_size),
            rnn = rnn_cls(
                config.emb_size,
                config.rnn_hidden_size,
                num_layers=config.rnn_n_layers,
                batch_first=True,
                dropout=config.rnn_dropout,
            ),
            head = nn.Sequential(
                nn.Dropout(config.head_dropout),
                nn.Linear(config.head_hidden_size, config.vocab_size),
            ),
        )

    def forward(self, input_ids, state=None):
        return self.model.forward(input_ids, state=state)