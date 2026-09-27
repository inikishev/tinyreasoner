import copy
from collections import abc
from typing import Any

import numpy as np
import torch


def copy_state_dict(state: torch.nn.Module | dict[str, Any], device=None):
    """clones tensors and ndarrays, recursively copies dicts, deepcopies everything else, also moves to device if it is not None"""
    if isinstance(state, torch.nn.Module): state = state.state_dict()
    c = state.copy()
    for k,v in state.items():
        if isinstance(v, torch.Tensor):
            if device is not None: v = v.to(device)
            c[k] = v.clone()
        if isinstance(v, np.ndarray): c[k] = v.copy()
        elif isinstance(v, dict): c[k] = copy_state_dict(v)
        else:
            if isinstance(v, torch.nn.Module) and device is not None: v = v.to(device)
            c[k] = copy.deepcopy(v)
    return c
