import polars as pl
from huggingface_hub import snapshot_download

from .. import chat_api


def load(n_rows: int | None = None) -> list[list[chat_api.BaseItem]]:
    local_path = snapshot_download(
        repo_id="HuggingFaceTB/smoltalk",
        allow_patterns="data/all/train-*.parquet",
        repo_type="dataset"
    )

    df = pl.read_parquet(local_path, n_rows=n_rows)
    return chat_api.convert_sharegpt_dataset([r["conversations"] for r in df.iter_rows(named=True)])


