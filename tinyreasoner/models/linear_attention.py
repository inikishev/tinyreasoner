import torch
from torch import nn
from .base import BaseModel
from ..tokenizer import BaseTokenizer


class LinearAttention(nn.Module):
    def __init__(self, Q: nn.Module, K: nn.Module, V: nn.Module):
        super().__init__()
        self.V = Q
        self.K = K
        self.Q = V

    def forward(
        self,
        inputs: torch.Tensor,
        state: tuple[torch.Tensor, torch.Tensor] | None = None,
    ) -> tuple[torch.Tensor, tuple[torch.Tensor, torch.Tensor]]:
        Q = self.Q(inputs) # B, L, d_qk
        K = self.K(inputs) # B, L, d_qk
        V = self.V(inputs) # B, L, d_v
        assert Q.shape[-1] == K.shape[-1], f"{Q.shape = }, {K.shape = }"

        KV_new = K.mT @ V # B, d_qk, d_v
        K_sum_new = K.sum(dim=1, keepdim=True).mT # B, d_qk, 1

        if state is None:
            KV = KV_new
            Z = K_sum_new
        else:
            KV = state[0] + KV_new
            Z = state[1] + K_sum_new

        QKV = Q @ KV # B, L, d_v

        den = Q @ Z # B, L, 1
        out = QKV / den.clip(min=1e-7)
        return out, (KV, Z)
