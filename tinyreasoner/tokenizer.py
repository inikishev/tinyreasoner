import copy
import json
import re
import string
from abc import ABC, abstractmethod
from collections import UserDict
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, Self, overload

import joblib

from . import chat_api


class SpecialTokens[T](UserDict[str,T]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def user(self) -> T: return self["user"]
    @property
    def assistant(self) -> T: return self["assistant"]
    @property
    def think(self) -> T: return self["think"]
    @property
    def end(self) -> T: return self["end"]
    @property
    def upper(self) -> T: return self["upper"]
    @property
    def tool_definition(self) -> T: return self["tool_definition"]
    @property
    def tool_call(self) -> T: return self["tool_call"]
    @property
    def unk(self) -> T: return self["unk"]
    @property
    def pad(self) -> T: return self["pad"]

_default_special_tokens = SpecialTokens({
    "user": "<|USER_MESSAGE|>",
    "assistant": "<|ASSISTANT_MESSAGE|>",
    "think": "<|THINK|>",
    "end": "<|END|>",
    "upper": "<|UPPER|>",
    "tool_definition": "<|TOOL_DEFINITION|>",
    "tool_call": "<|TOOL_CALL|>",
    "unk": "<|UNK|>",
    "pad": "<|PAD|>",
})

_default_capacity_tokens = {
    "capacity_define": "<|CAP_DEFINE|>",
    "capacity_calculate": "<|CAP_CALCULATE|>",
    "capacity_store_memory": "<|CAP_STORE|>",
    "capacity_retrieve_memory": "<|CAP_RETRIEVE|>",
}
_default_special_tokens_w_capacities = SpecialTokens(_default_special_tokens | _default_capacity_tokens)

class BaseTokenizer(ABC):
    """A tokenizer.

    Args:
        special_tokens: maps keys like "user", "assistant", "unk" to their token strings.
        special_idxs: maps keys like "user", "assistant", "unk" to their token indexes.
    """
    def __init__(self, special_strings: Mapping[str,str], special_idxs: Mapping[str, int]):
        self.special_strings: SpecialTokens[str] = SpecialTokens(copy.deepcopy(special_strings))
        self.special_idxs: SpecialTokens[int] = SpecialTokens(copy.deepcopy(special_idxs))
        self.capacities: list[str] = [k for k in self.special_strings if k.startswith("capacity_")]

        self.pad_idx = self.special_idxs.pad
        self.unk_idx = self.special_idxs.unk
        self.user_idx = self.special_idxs.user
        self.assistant_idx = self.special_idxs.assistant
        self.end_idx = self.special_idxs.end
        self.tool_call_idx = self.special_idxs.tool_call
        self.tool_definition_idx = self.special_idxs.tool_definition
        self.think_idx = self.special_idxs.think

    @property
    @abstractmethod
    def vocab_size(self) -> int:
        """vocab size"""

    @abstractmethod
    def encode_text(self, text: str) -> list[int]:
        """Encodes text, doesn't add special tokens."""

    @abstractmethod
    def decode(self, tokens: Sequence[int] | Any) -> str:
        """Decodes tokens to text."""


    def encode_chat(self, items: Sequence[chat_api.AnyItem]) -> chat_api.TokensAndMask:
        """Encodes chat with all special tokens added."""
        tokens = []
        loss_mask = []

        for item in items:
            item = chat_api.to_item(item)
            item_tokens, item_mask = item.tokenize(self)
            tokens.extend(item_tokens)
            loss_mask.extend(item_mask)

        return chat_api.TokensAndMask(tokens, loss_mask)

    def preview_encoded(self, items: Sequence[chat_api.AnyItem], masked: bool = False):
        encoded, mask = self.encode_chat(items)

        if masked:
            encoded = [t if m == 1 else self.pad_idx for t,m in zip(encoded, mask)]

        decoded = self.decode(encoded)

        for t in self.special_strings.values():
            if t not in (self.special_strings.pad, self.special_strings.unk):
                decoded = decoded.replace(t, f"\n{t}")

        return decoded.replace(self.special_strings.pad, "_")

    def save(self, file):
        joblib.dump(self, file)

    @classmethod
    def from_file(cls, file) -> "Self":
        return joblib.load(file)

# ---------------------------- character tokenizer --------------------------- #

_punctuation_chars = " \n.,:;!?'\"`#"
_math_chars = "=+-*/^%><)(@$"
_logic_chars = "&|^~"
_python_chars = r"{}[]_\\"
_chars = sorted(set(string.ascii_lowercase + string.digits + _punctuation_chars + _math_chars + _logic_chars + _python_chars))

def _create_keyword_splitter(words: Sequence[str]):
    # sort words by length descending to ensure words that
    # contain shorter words as substrings are tokenized first
    words = sorted(words, key=len, reverse=True)
    pattern = "|".join(map(re.escape, words))
    pattern = f"{pattern}|."
    return re.compile(pattern, re.DOTALL)

_replace_chars_default = {
    "×": "*",
    "÷": "/",
}

class CharacterTokenizer(BaseTokenizer):
    def __init__( # pylint:disable=dangerous-default-value
        self,
        chars: Sequence[str] = _chars,
        special_tokens: Mapping[str, str] = _default_special_tokens_w_capacities,
        replace_map: Mapping[str, str] = _replace_chars_default,
    ):
        chars = copy.deepcopy(chars)
        special_tokens = copy.deepcopy(special_tokens)
        self.replace_map = copy.deepcopy(replace_map)

        tokens = sorted(set(list(chars) + list(special_tokens.values())))

        self.token_to_int = {c: i for i,c in enumerate(tokens)}
        self.int_to_token = {i: c for c,i in self.token_to_int.items()}

        self.tokens = set(tokens)

        keywords = [t for t in tokens if len(t) > 1]
        self.splitter = _create_keyword_splitter(keywords)

        self.modifier_to_uppercase = dict(zip(
            [f"{special_tokens['upper']}{c}" for c in string.ascii_lowercase], string.ascii_uppercase,
        ))

        self.modifier_to_uppercase_pattern = re.compile(
            "|".join(re.escape(key) for key in self.modifier_to_uppercase.keys()))

        self.unk_pattern = re.compile(
            f"{re.escape(special_tokens['unk'])}(\\d+){re.escape(special_tokens['unk'])}{{2}}")

        super().__init__(special_tokens, {k: self.token_to_int[v] for k,v in special_tokens.items()})

    @property
    def vocab_size(self):
        return len(self.token_to_int)

    def encode_text(self, text: str) -> list[int]:
        for old_char, new_char in self.replace_map.items():
            text = text.replace(old_char, new_char)

        return [
            self.token_to_int.get(c, self.unk_idx)
            for tok in self.splitter.findall(str(text))
            for c in (
                [self.special_strings.upper, tok.lower()]
                if (tok.isalpha() and tok.isupper())
                else (
                    [tok]
                    if tok in self.token_to_int
                    else [self.special_strings.unk] + list(str(ord(tok))) + [self.special_strings.unk, self.special_strings.unk]
                )
            )
        ]

    def decode(self, tokens: Sequence[int] | Any) -> str:
        if isinstance(tokens, int): text = self.int_to_token[tokens]
        else: text = "".join(self.int_to_token[int(t)] for t in tokens)
        text = self.unk_pattern.sub(lambda m: chr(int(m.group(1))), text)
        text = self.modifier_to_uppercase_pattern.sub(lambda m: self.modifier_to_uppercase[m.group(0)], text)
        return text

class OrderTokenizer(BaseTokenizer):
    """A tokenizer which only has digits and special tokens, encodes everything to it's unicode order."""
    def __init__(self, special_tokens: Mapping[str,str] = _default_special_tokens):
        special_tokens = copy.deepcopy(special_tokens)

        tokens = sorted(list(string.digits) + list(special_tokens.values()))

        self.token_to_int = {c: i for i,c in enumerate(tokens)}
        self.int_to_token = {i: c for c,i in self.token_to_int.items()}

        self.tokens = set(tokens)

        keywords = [t for t in tokens if len(t) > 1]
        self.splitter = _create_keyword_splitter(keywords)

        self.unk_pattern = re.compile(
            f"{re.escape(special_tokens['unk'])}(\\d+)")

        super().__init__(special_tokens, {k: self.token_to_int[v] for k,v in special_tokens.items()})

    @property
    def vocab_size(self):
        return len(self.special_strings)

    def encode_text(self, text: str) -> list[int]:
        """Encodes text, doesn't add special tokens."""

        return [
            self.token_to_int.get(c, self.unk_idx)
            for tok in self.splitter.findall(str(text))
            for c in (
                [tok]
                if tok in self.token_to_int
                else [self.special_strings.unk] + list(str(ord(tok)))
            )
        ]

    def decode(self, tokens: Sequence[int] | Any) -> str:
        """Decodes tokens to text."""
        if isinstance(tokens, int): text = self.int_to_token[tokens]
        else: text = "".join(self.int_to_token[int(t)] for t in tokens)
        text = self.unk_pattern.sub(lambda m: chr(int(m.group(1))), text)
        return text