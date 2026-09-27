import json

import polars as pl
from huggingface_hub import hf_hub_download

from tinyreasoner import chat_api


def _process_message(message: dict):
    if message["role"] == "tool":
        tc = json.loads(message["content"][0]["text"])
        return {"role": "tool", "name": tc["tool_name"], "content": tc["tool_result"]}
    return message

def load(verbose:bool=False):
    local_path = hf_hub_download(
        repo_id="acon96/Home-Assistant-Requests-V2",
        filename="home_assistant_test.jsonl", # NOTE: we download test set because train set is too big to download
        repo_type="dataset"
    )

    df = pl.read_ndjson(local_path)
    chats = []
    for messages, tools in df.iter_rows():
        messages = [_process_message(m) for m in messages]
        chats.append({"tools": tools, "messages": messages})

    samples = chat_api.convert_openai_dataset(chats, require_tc_id=False, verbose=verbose)
    return samples
