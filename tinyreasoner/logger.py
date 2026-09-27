from collections import UserDict
from typing import Any

import numpy as np
import torch


class DictLogger(UserDict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lazy_list = []

    def lazy_log(self, step: int, metric: str, value: Any, max_lazy: int = 1000):
        if isinstance(value, torch.Tensor): value = value.detach() # don't move to CPU to avoid blocking
        self.lazy_list.append((step, metric, value))
        if len(self.lazy_list) > max_lazy:
            self.lazy_finalize()

    def lazy_finalize(self):
        for step, metric, value in self.lazy_list:
            self.log(step, metric, value)
        self.lazy_list.clear()

    def log(self, step: int, metric: str, value: Any):
        if isinstance(value, torch.Tensor): value = value.detach().cpu().item()
        if metric not in self: self[metric] = {step: value}
        else: self[metric][step] = value

    def to_list(self, metric: str) -> list[Any]:
        self.lazy_finalize()
        return list(self[metric].values())

    def to_numpy(self, metric: str) -> np.ndarray:
        return np.asarray(self.to_list(metric))

    def min(self, metric: str):
        return self.to_numpy(metric).min()