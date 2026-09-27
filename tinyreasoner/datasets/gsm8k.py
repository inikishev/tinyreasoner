import polars as pl
from huggingface_hub import hf_hub_download, snapshot_download

from tinyreasoner import chat_api


def _load_main() -> list[list[chat_api.BaseItem]]:
    local_path = hf_hub_download(
        repo_id="openai/gsm8k",
        filename="main/train-00000-of-00001.parquet",
        repo_type="dataset"
    )

    df = pl.read_parquet(local_path)

    samples = []
    for question, answer in df.iter_rows():
        samples.append([
            chat_api.UserMessage(f"{question}. Give the solution and the answer in the following format:\nsolution\n#### answer"),
            chat_api.AssistantMessage(text=answer),
        ])

    return samples

def _load_socratic() -> list[list[chat_api.BaseItem]]:
    local_path = hf_hub_download(
        repo_id="openai/gsm8k",
        filename="socratic/train-00000-of-00001.parquet",
        repo_type="dataset"
    )

    df = pl.read_parquet(local_path)

    samples = []
    for question, answer in df.iter_rows():
        samples.append([
            chat_api.UserMessage(f"{question}. Give a step-by step solution in Socratic style and the answer in the following format:\nsolution formatted as question ** answer lines\n#### final answer"),
            chat_api.AssistantMessage(text=answer),
        ])

    return samples

def load() -> list[list[chat_api.BaseItem]]:
    return _load_main() + _load_socratic()