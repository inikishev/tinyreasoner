from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Sequence
from typing import Any

import numpy as np
import torch
from torch import nn

from .sampling import temperature_sampling, _GenerationOutput

from ..tokenizer import BaseTokenizer

class BaseModel(nn.Module, ABC):

    def __init__(self, tokenizer: BaseTokenizer):
        super().__init__()
        # NOTE: transformers wrapper passes a DummyTokenizer as tokenizer (predict method is never called)
        # nothing I can do about it
        self.tokenizer = tokenizer

    @property
    def device(self):
        return next(iter(self.parameters())).device
    @property
    def dtype(self):
        return next(iter(self.parameters())).dtype

    def n_params(self):
        return sum(p.numel() for p in self.parameters())

    @abstractmethod
    def forward(self, x: torch.Tensor, state: Any=None) -> tuple[torch.Tensor, Any]:
        """Predict the probabilities of the next tokens for each token in `x` and update the hidden state.

        Args:
            x: token indices in shape `(B, L)` initially, then `(B, 1)` during autoregressive generation.
            state: any state neeeded for the model. The returned state will be
                passed back to the model during inference loop. Defaults to None.

        Returns (tuple):
            x_out: output of shape `(B, L, vocab_size)`.
            state: output state.
        """

    def predict(self, inputs, max_tokens: int = 1000, temperature=0.1, think:bool=False) -> _GenerationOutput:
        return temperature_sampling(
            model=self,
            inputs=inputs,
            max_tokens=max_tokens,
            temperature=temperature,
            think=think,
        )
