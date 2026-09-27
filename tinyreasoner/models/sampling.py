from collections import defaultdict
from collections.abc import Sequence
from typing import Any, NamedTuple, Literal, TYPE_CHECKING

import numpy as np
import torch
from langchain_core.tools import BaseTool, tool
from nltk.corpus import wordnet
from sympy import sympify
from torch.nn import functional as F

from .. import chat_api
from ..tokenizer import BaseTokenizer

if TYPE_CHECKING:
    from .models import BaseModel

def capacity_define(word: str) -> str:
    syns = wordnet.synsets(word)
    if syns:
        definition = syns[0].definition() # type:ignore
        return definition
    return ""

def capacity_calculate(expr: str):
    try:
        s = sympify(expr)
        return str(s.evalf())
    except Exception as e:
        return str(e)

class _GenerationOutput(NamedTuple):
    input_tokens: list[int] | Any
    output_tokens: list[int]
    tc_name_tokens: list[int]
    tc_args_tokens: list[int]
    finish_reason: Literal["stop", "tool_call", "max_tokens"]


@torch.inference_mode()
def temperature_sampling(
    model: "BaseModel",
    inputs: Any,
    max_tokens: int,
    temperature=0.1,
    think: bool = False,
) -> _GenerationOutput:
    device = next(iter(model.parameters())).device
    tokenizer = model.tokenizer

    # ------------------------------ prepare inputs ------------------------------ #
    generation_tokens = [tokenizer.assistant_idx]
    if think:
        generation_tokens.append(tokenizer.think_idx)

    if isinstance(inputs, list) and isinstance(inputs[0], chat_api.AnyItem):
        input_tokens = tokenizer.encode_chat(inputs).tokens
        input_tensor = torch.tensor(input_tokens + generation_tokens, device=device)

    elif isinstance(inputs, str):
        input_tokens = tokenizer.encode_chat([chat_api.UserMessage(inputs)]).tokens + generation_tokens
        input_tensor = torch.tensor(input_tokens, device=device)

    else:
        if think: raise RuntimeError("If `inputs` is already tokenized, `think` has no effect and must be unset.")
        input_tokens = inputs
        input_tensor = torch.as_tensor(inputs, device=device)

    if input_tensor.ndim == 1:
        input_tensor = input_tensor.unsqueeze(0)


    # ---------------------------------- sample ---------------------------------- #
    capacities: dict[int, str] = {tokenizer.special_idxs[cap]: cap for cap in tokenizer.capacities}

    is_tc_name: bool = False
    is_tc_args: bool = False
    tc_name_tokens: list[int] = []
    tc_args_tokens: list[int] = []
    encoded_outputs: list[int] = []
    outputs, state = model.forward(input_tensor)

    for _ in range(max_tokens):
        char_probs = F.softmax(outputs[:, -1, :] / temperature, dim=-1)
        char_idx_tensor = torch.multinomial(char_probs, 1).detach()
        outputs, state = model.forward(char_idx_tensor, state)

        char_idx = int(char_idx_tensor.detach().cpu().item())
        encoded_outputs.append(char_idx)

        # -------------------------------- tool calls -------------------------------- #
        if is_tc_name and char_idx != tokenizer.end_idx:
            tc_name_tokens.append(char_idx)

        if is_tc_args and (char_idx != tokenizer.tool_call_idx) and (char_idx != tokenizer.end_idx):
            tc_args_tokens.append(char_idx)

        if char_idx == tokenizer.tool_call_idx:
            if is_tc_name:
                is_tc_name = False
                is_tc_args = True
            else:
                is_tc_args = False
                is_tc_name = True

            tc_name_tokens.clear()
            tc_args_tokens.clear()

        # -------------------------------- capacities -------------------------------- #
        for cap, name in capacities.items():
            if char_idx == cap:
                tc_name_tokens = tokenizer.encode_text(f"__CAPACITY__{name}")
                tc_args_tokens.clear()
                is_tc_name = False
                is_tc_args = True

        if char_idx == tokenizer.end_idx:
            if len(tc_args_tokens) > 0:
                finish_reason = "tool_call"
            else:
                finish_reason = "stop"
            break


    else:
        finish_reason = "max_tokens"

    return _GenerationOutput(
        input_tokens = input_tokens,
        output_tokens = encoded_outputs,
        tc_name_tokens = tc_name_tokens,
        tc_args_tokens = tc_args_tokens,
        finish_reason = finish_reason,
    )

