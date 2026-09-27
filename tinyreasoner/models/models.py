"""Named models."""

from typing import Any

import torch
from torch import nn
from torch.nn import functional as F

from ..tokenizer import CharacterTokenizer
from .base import BaseModel
from .rnn import RNN

char_tokenizer = CharacterTokenizer()

class LSTM_1L_1H_342_1m(RNN):

    def __init__(self, dropout=0):
        width = 342
        super().__init__(
            tokenizer=char_tokenizer,
            embedding=nn.Embedding(char_tokenizer.vocab_size, width),
            rnn=nn.LSTM(width, width, num_layers=1, batch_first=True, dropout=dropout),
            head=nn.Sequential(
                nn.Dropout(dropout), nn.Linear(width, char_tokenizer.vocab_size)
            ),
        )
        assert self.n_params() == 995_303


class LSTM_1L_LN_1H_342_1m(RNN):
    def __init__(self, dropout=0):
        width = 342
        super().__init__(
            tokenizer=char_tokenizer,
            embedding=nn.Embedding(char_tokenizer.vocab_size, width),
            rnn=nn.LSTM(width, width, num_layers=1, batch_first=True, dropout=dropout),
            head=nn.Sequential(
                nn.LayerNorm(width, elementwise_affine=False),
                nn.Dropout(dropout),
                nn.Linear(width, char_tokenizer.vocab_size),
            ),
        )
        assert self.n_params() == 995_303


class LSTM_1L_2H_320_1m(RNN):
    def __init__(self, dropout=0):
        width = 322
        super().__init__(
            tokenizer=char_tokenizer,
            embedding=nn.Embedding(char_tokenizer.vocab_size, width),
            rnn=nn.LSTM(width, width, batch_first=True, dropout=dropout),
            head=nn.Sequential(
                nn.Dropout(dropout),
                nn.Linear(width, width),
                nn.ELU(),
                nn.Dropout(dropout),
                nn.Linear(width, char_tokenizer.vocab_size),
            ),
        )
        assert self.n_params() == 989_589


class LSTM_2L_1H_244_1m(RNN):
    def __init__(self, dropout=0):
        width = 244
        super().__init__(
            tokenizer=char_tokenizer,
            embedding=nn.Embedding(char_tokenizer.vocab_size, width),
            rnn=nn.LSTM(width, width, num_layers=2, batch_first=True, dropout=dropout),
            head=nn.Sequential(
                nn.Dropout(dropout), nn.Linear(width, char_tokenizer.vocab_size)
            ),
        )
        assert self.n_params() == 997067


class LSTM_1L_5H_280_1m(RNN):
    def __init__(self, dropout=0):
        width = 280
        super().__init__(
            tokenizer=char_tokenizer,
            embedding=nn.Embedding(char_tokenizer.vocab_size, width),
            rnn=nn.LSTM(width, width, batch_first=True, dropout=dropout),
            head=nn.Sequential(
                nn.Dropout(dropout),
                nn.Linear(width, width),
                nn.ELU(),
                nn.Dropout(dropout),
                nn.Linear(width, width),
                nn.ELU(),
                nn.Dropout(dropout),
                nn.Linear(width, width),
                nn.ELU(),
                nn.Dropout(dropout),
                nn.Linear(width, width),
                nn.ELU(),
                nn.Dropout(dropout),
                nn.Linear(width, char_tokenizer.vocab_size),
            ),
        )
        assert self.n_params() == 990723


class LSTM_5L_1H_154_1m(RNN):
    def __init__(self, dropout=0):
        width = 154
        super().__init__(
            tokenizer=char_tokenizer,
            embedding=nn.Embedding(char_tokenizer.vocab_size, width),
            rnn=nn.LSTM(width, width, num_layers=5, batch_first=True, dropout=dropout),
            head=nn.Sequential(
                nn.Dropout(dropout), nn.Linear(width, char_tokenizer.vocab_size)
            ),
        )
        assert self.n_params() == 980447
