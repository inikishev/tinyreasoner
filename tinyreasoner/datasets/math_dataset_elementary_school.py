# source https://github.com/RamonKaspar/MathDataset-ElementarySchool

import json
from pathlib import Path

import polars as pl

from tinyreasoner import chat_api

ROOT = Path("/run/media/jj/Ext2TB/Files/Main/Programming/Projects/tinyreasoner/notebooks/datasets/downloaded")

def _format_answer(answer):
    if isinstance(answer, float):
        if answer % 1 == 0: return int(answer)

    if isinstance(answer, int):
        return answer

    return None # skip ugly float answers

def load():
    samples = []

    df = pl.read_ndjson(ROOT / "geometry_complete.jsonl")
    for row in df.iter_rows(named=True):

        assert row["reasoning"]
        answer = _format_answer(row["answer"])
        if answer is None: continue

        samples.append([
            chat_api.UserMessage(f'{row["question"]}\nOnly include the answer in your response.'),
            chat_api.AssistantMessage(str(answer))
        ])

        samples.append([
            chat_api.UserMessage(f'{row["question"]}. Write python code to solve this and the output.'),
            chat_api.AssistantMessage(f'```py\n{row["reasoning"]}\n```\n\nAnswer: {answer}')
        ])

    df = pl.read_ndjson(ROOT / "arithmetic_1000.jsonl")
    for row in df.iter_rows(named=True):

        answer = _format_answer(row["answer"])
        if answer is None: continue

        samples.append([
            chat_api.UserMessage(f'{row["question"]}\nOnly include the answer in your response.'),
            chat_api.AssistantMessage(str(answer))
        ])

    with open(ROOT / "wordProblems_complete.json", "r", encoding='utf-8') as f:
        df = pl.from_dicts(json.load(f)).head(2)

    for row in df.iter_rows(named=True):

        answer = _format_answer(row["answer"])
        if answer is None: continue

        samples.append([
            chat_api.UserMessage(f'{row["question"]}\nOnly include the answer in your response.'),
            chat_api.AssistantMessage(str(answer))
        ])


    return samples
