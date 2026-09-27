import polars as pl
from huggingface_hub import hf_hub_download, snapshot_download

from tinyreasoner import chat_api


def load() -> list[list[chat_api.BaseItem]]:
    local_path = hf_hub_download(
        repo_id="vicgalle/alpaca-gpt4",
        filename="data/train-00000-of-00001-6ef3991c06080e14.parquet",
        repo_type="dataset"
    )

    df = pl.read_parquet(local_path)

    samples = []
    for instruction, input, output, text in df.iter_rows():
        prompt = instruction
        if input:
            prompt = f"{prompt}\n\n### Input\n{input}"

        samples.append([
            chat_api.UserMessage(prompt),
            chat_api.AssistantMessage(text=output),
        ])

    return samples
