import copy
import json
import os
import random
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import myagent as ma
import polars as pl
import tqdm

from .. import chat_api

_cot_placeholder = "chain-of-thought-placeholder"

class FailedToGenerateReasoning(Exception): pass

# TODO: implement

ROOT = "/run/media/jj/Ext2TB/Files/Main/Programming/Projects/tinyreasoner/notebooks/datasets/generated_reasoning"

def try_json_load(sample, path):
    try:
        return json.loads(sample)
    except Exception as e:
        print(path, sample)
        raise e

def load(include=None, exclude=None) -> list[list[chat_api.BaseItem]]:
    if isinstance(include, str): include = [include]
    if isinstance(exclude, str): exclude = [exclude]

    samples = []
    for file in os.listdir(ROOT):
        if file.endswith(".jsonl"):

            if include is not None:
                if file in include: include.remove(file)
                else: continue

            if exclude is not None:
                if file in exclude:
                    exclude.remove(file)
                    continue

            path = os.path.join(ROOT, file)
            with open(path, "r", encoding='utf-8') as f:
                items = [[chat_api.to_item(i) for i in try_json_load(sample.strip(), path)] for sample in f.read().split('\n') if len(sample.strip()) > 0]
                samples.extend(items)

    if include:
        raise FileNotFoundError(f"Following `include` files were not found: {include}")
    if exclude:
        raise FileNotFoundError(f"Following `exclude` files were not found: {exclude}")

    return samples