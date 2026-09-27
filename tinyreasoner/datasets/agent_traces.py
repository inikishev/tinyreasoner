import polars as pl
from huggingface_hub import hf_hub_download

from .. import chat_api


def load(verbose: bool = False) -> list[list[chat_api.BaseItem]]:
    local_path = hf_hub_download(
        repo_id="trace-commons/agent-traces",
        filename="data/train-00000-of-00001.parquet",
        repo_type="dataset"
    )
    df = pl.read_parquet(local_path)

    chats = []
    for _, _, _, messages, tools, *_ in df.iter_rows():
        chats.append({"tools": tools, "messages": messages})

    return chat_api.convert_openai_dataset(chats, require_tc_id=True, verbose=verbose)