import polars as pl
from huggingface_hub import hf_hub_download

from .. import chat_api


def load(verbose: bool = True) -> list[list[chat_api.BaseItem]]:
    local_path_train = hf_hub_download(
        repo_id="trl-lib/Capybara",
        filename="data/train-00000-of-00001.parquet",
        repo_type="dataset"
    )
    local_path_test = hf_hub_download(
        repo_id="trl-lib/Capybara",
        filename="data/test-00000-of-00001.parquet",
        repo_type="dataset"
    )
    df = pl.concat([pl.read_parquet(local_path_train), pl.read_parquet(local_path_test)])

    chats = [{"messages": messages} for _, messages, _ in df.iter_rows()]
    return chat_api.convert_openai_dataset(chats, require_tc_id=True, verbose=verbose)