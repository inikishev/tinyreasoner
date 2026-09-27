import polars as pl
from huggingface_hub import hf_hub_download
import os

def load(n_rows: int | None = None) -> list[str]:
    local_path = hf_hub_download(
        repo_id="exnivo/tinybrain-base",
        filename="tinybrain_pretrain.jsonl",
        repo_type="dataset"
    )


    df = pl.read_ndjson(local_path, n_rows=n_rows)
    return df["text"].to_list()