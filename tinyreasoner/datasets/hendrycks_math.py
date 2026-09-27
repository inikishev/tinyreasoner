import polars as pl
from huggingface_hub import snapshot_download

from tinyreasoner import chat_api


def load():
    local_path = snapshot_download(
        repo_id="EleutherAI/hendrycks_math",
        allow_patterns="**/*.parquet",
        repo_type="dataset"
    )

    df = pl.read_parquet(local_path)

    samples = []
    for row in df.iter_rows(named=True):
        samples.append([chat_api.UserMessage(row["problem"]), chat_api.AssistantMessage(text=row["solution"])])

    return samples