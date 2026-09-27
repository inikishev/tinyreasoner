import polars as pl
from huggingface_hub import hf_hub_download

from .. import chat_api


def load(n_rows: int | None = None):
    local_path = hf_hub_download(
        repo_id="facebook/natural_reasoning",
        filename="full.jsonl",
        repo_type="dataset"
    )

    df = pl.read_ndjson(local_path, n_rows=n_rows)
    return [[chat_api.UserMessage(row["question"]), chat_api.AssistantMessage(text=row["responses"][0]["response"])] for row in df.iter_rows(named=True)]
