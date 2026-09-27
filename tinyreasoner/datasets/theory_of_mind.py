"""https://huggingface.co/datasets/grimulkan/theory-of-mind"""
import polars as pl
from huggingface_hub import hf_hub_download

from .. import chat_api


def load() -> list[list[chat_api.BaseItem]]:
    local_path1 = hf_hub_download(
        repo_id="grimulkan/theory-of-mind",
        filename="theory_of_mind.json",
        repo_type="dataset"
    )
    local_path2 = hf_hub_download(
        repo_id="grimulkan/theory-of-mind",
        filename="theory_of_mind_airoboros_fixed.json",
        repo_type="dataset"
    )
    local_path3 = hf_hub_download(
        repo_id="grimulkan/theory-of-mind",
        filename="theory_of_mind_longer.json",
        repo_type="dataset"
    )

    df = pl.concat([
        pl.read_json(local_path1),
        pl.read_json(local_path2),
        pl.read_json(local_path3),
    ])

    samples: list[list[chat_api.BaseItem]] = []
    for row in df.iter_rows(named=True):
        assert len(row["input"].strip()) == 0
        samples.append([chat_api.UserMessage(row["instruction"]), chat_api.AssistantMessage(text=row["response"])])

    return samples