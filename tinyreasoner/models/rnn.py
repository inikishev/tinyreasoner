from collections.abc import Callable, Iterable, Sequence
from typing import Any

import torch
from torch import nn

from .base import BaseModel
from ..tokenizer import BaseTokenizer


class RNN(BaseModel):
    """Recurrent model.

    Args:
        embedding: for example ``nn.Embedding(vocab_size, embedding_dim)``
        rnn: for example ``nn.LSTM(embedding_dim, hidden_dim)``. Forward should return tuple ``(out, hidden)``.
        head: for example ``nn.Linear(hidden_dim, vocab_size)``. Applied to ``(B, L, hidden_size)``.
    """
    def __init__(self, tokenizer: BaseTokenizer, embedding: nn.Module, rnn: nn.Module, head: nn.Module):
        super().__init__(tokenizer)

        self.embedding = embedding
        self.rnn = rnn
        self.head = head

    def forward(self, x: torch.Tensor, state=None) -> tuple[torch.Tensor, Any]:
        embedded = self.embedding(x)
        rnn_out, state = self.rnn(embedded, state)
        output = self.head(rnn_out)
        return output, state


class TensorLinear2D(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, hidden_m: int,
                 hidden_channels: int, n_hidden:int, rms_norm:bool=False, with_mean:bool=True):
        super().__init__()
        self.hidden_m = hidden_m
        self.weighter = nn.Linear(in_channels, hidden_m)
        self.W_ih = nn.Parameter(torch.randn(hidden_m, in_channels, hidden_channels))
        self.W_hh = nn.ParameterList(
            nn.Parameter(torch.randn(hidden_m, hidden_channels, hidden_channels)) for _ in range(n_hidden-1)
        )
        self.W_ho = nn.Parameter(torch.randn(hidden_m, hidden_channels, out_channels))
        self.leak = nn.Parameter(torch.linspace(-2, 2, hidden_m).unsqueeze(-1)) # (N, 1)

        self.rms_norm = rms_norm
        self.with_mean = with_mean

    def leaky_relu(self, x: torch.Tensor):
        x = torch.where(x < 0, x*self.leak, x)
        return x

    def forward(self, x: torch.Tensor):
        # x is (..., I) - (B, L, I) for LSTM
        weights = torch.softmax(self.weighter(x), -1) # (..., N)

        # W_ih is (N, I, H)
        x = torch.einsum("...i,nih->...nh", x, self.W_ih) # (..., N, H)
        x = self.leaky_relu(x)
        for W in self.W_hh:
            # W is (N, H, H), second H is z
            x = torch.einsum("...nh,nhz->...nz", x, W)
            x = self.leaky_relu(x)

        # W_ho s (N, H, O)
        x = torch.einsum("...nh,nho->...no", x, self.W_ho) * weights.unsqueeze(-1) # (..., N, O)

        return x.mean(-2)


class TensorLinear3D(nn.Module):
    """Two-dimensional MOE also kronecker net"""
    def __init__(self, in_channels: int, out_channels: int, hidden_m: int, hidden_n: int,
                 n_hidden:int, rms_norm:bool=False, with_mean:bool=True):
        super().__init__()
        self.hidden_m = hidden_m
        self.hidden_n = hidden_n
        self.weighter_m = nn.Linear(in_channels, hidden_m)
        self.weighter_n = nn.Linear(in_channels, hidden_n)
        self.W_im = nn.Parameter(torch.randn(hidden_n, in_channels, hidden_m))
        self.W_in = nn.Parameter(torch.randn(hidden_m, in_channels, hidden_n))
        self.W_mm = nn.ParameterList(
            nn.Parameter(torch.randn(hidden_n, hidden_m, hidden_m)) for _ in range(n_hidden-1)
        )
        self.W_nn = nn.ParameterList(
            nn.Parameter(torch.randn(hidden_m, hidden_n, hidden_n)) for _ in range(n_hidden-1)
        )
        self.W_mo = nn.Parameter(torch.randn(hidden_n, hidden_m, out_channels))
        self.W_no = nn.Parameter(torch.randn(hidden_m, hidden_n, out_channels))

        self.leak_m = nn.Parameter(torch.linspace(-2, 2, hidden_m))
        self.leak_n = nn.Parameter(torch.linspace(-2, 2, hidden_n))

        self.rms_norm = rms_norm
        self.with_mean = with_mean

    def forward(self, x: torch.Tensor):
        # x is (..., I) - (B, L, I) for LSTM
        weights_n = torch.softmax(self.weighter_n(x), -1) # (..., N)
        weights_m = torch.softmax(self.weighter_m(x), -1) # (..., M)

        # W_im is (N, I, M)
        x_m = torch.einsum("...i,nim->...nm", x, self.W_im) # (..., N, M)
        x_m = torch.where(x_m < 0, x_m*self.leak_m, x_m)

        x_n = torch.einsum("...i,min->...mn", x, self.W_in) # (..., M, N)
        x_n = torch.where(x_n < 0, x_n*self.leak_n, x_n)

        x = x_m + x_n.mT # (..., N, M)

        for W_m, W_n in zip(self.W_mm, self.W_nn):
            # W_m is (N, M, M), second M is z
            x = torch.einsum("...nm,nmz->...nz", x, W_m) # (..., N, M)
            x = torch.where(x < 0, x*self.leak_m, x)

            # W_n is (M, N, N), second N is z
            x = torch.einsum("...nm,mnz->...zm", x, W_n) # (..., N, M)
            x = torch.where(x < 0, x*self.leak_n.unsqueeze(-1), x)

        # W_mo s (N, M, O)
        x_m = torch.einsum("...nm,nmo->...no", x, self.W_mo) * weights_n.unsqueeze(-1) # (..., N, O)
        x_n = torch.einsum("...nm,mno->...mo", x, self.W_no) * weights_m.unsqueeze(-1) # (..., M, O)

        x = x_m.mean(-2) + x_n.mean(-2) # (..., O)
        return x


class MLP(nn.Module):
    """Multi-layer perceptorn head.

    Args:
        channels: list of widths of linear layers.
            First value is number of input channels and last is number of output channels.
        act_cls: activation function constructor. Defaults to nn.ReLU.
        bn: if True enables batch norm. Defaults to False.
        dropout: dropout probability. Defaults to 0.
        ortho_init: if true ises orthgonal init. defaults to False.
        cls: Linear layer constructor with signature ``cls(in_channels, out_channels, bias)``
            and same output shape as nn.Linear. Defaults to nn.Linear
    """
    def __init__(
        self,
        channels: Iterable[int],
        act_cls: Callable | None = nn.ReLU,
        bn: bool = False,
        dropout: float = 0,
        ortho_init: bool = False,
        cls: Callable = nn.Linear,
    ):
        super().__init__()
        channels = list(channels)
        layers = []

        # if len(channels) = 2, this entire thing is skipped (is empty) so we get only head
        for i,o in zip(channels[:-2], channels[1:-1]):
            layers.append(cls(i, o, not bn))
            if act_cls is not None: layers.append(act_cls())
            if bn: layers.append(nn.BatchNorm1d(o))
            if dropout > 0: layers.append(nn.Dropout1d(dropout))

        self.layers = nn.Sequential(*layers)
        self.head = cls(channels[-2], channels[-1])

        if ortho_init:
            generator=torch.Generator().manual_seed(0)
            for p in self.parameters():
                if p.ndim >= 2:
                    torch.nn.init.orthogonal_(p, generator=generator)

    def forward(self, x: torch.Tensor):
        for l in self.layers: x = l(x)
        return self.head(x)


class SequentialWithHidden(nn.Module):
    def __init__(
        self,
        pre: nn.Module | Sequence[nn.Module] | None,
        rnn: nn.Module | Sequence[nn.Module] | None,
        post: nn.Module | Sequence[nn.Module] | None,
    ):
        super().__init__()

        def _ensure_list(x):
            if x is None: return nn.ModuleList([nn.Identity()])
            if isinstance(x, nn.Module): return nn.ModuleList([x])
            return nn.ModuleList(x)

        self.pre = _ensure_list(pre)
        self.rnn = _ensure_list(rnn)
        self.post = _ensure_list(post)

    def forward(self, x: torch.Tensor, hidden: Any = None):
        for m in self.pre: x = m(x)
        for m in self.rnn: x, hidden = m(x, hidden)
        for m in self.post: x = m(x)
        return x, hidden
