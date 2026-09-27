import json
import re

import polars as pl
from huggingface_hub import hf_hub_download

from .. import chat_api

_tc_extract = r"<tool_call>\s*(.*?)\s*</tool_call>"
_tc_resp_extract = r"<tool_response>\s*(.*?)\s*</tool_response>"

def parse_to_openai(row: tuple[str, list[dict[str,str]], str, str, str, str]):
    tools = json.loads(row[2])

    # system message is useless, it just has tools
    chat = row[1][1:]

    openai_chat = []
    for message in chat:
        role = message["from"]
        content = message["value"]

        if role == "gpt":
            tool_calls = re.findall(_tc_extract, content, re.DOTALL)
            if len(tool_calls) > 0:
                openai_chat.append({"role": "assistant", "tool_calls": [json.loads(tc.strip()) for tc in tool_calls]})
            else:
                openai_chat.append({"role": "assistant", "content": content})

        elif role == "tool":
            tool_outputs = re.findall(_tc_resp_extract, content, re.DOTALL)
            assert len(tool_outputs) > 0
            for output in tool_outputs:
                parsed = json.loads(output.strip())
                openai_chat.append({"role": "tool", "name": parsed["name"], "content": output})

        else:
            assert role == "human", role
            openai_chat.append({"role": "user", "content": content})

    return {"tools": tools, "messages": openai_chat}


def _load_dataset_openai(filename: str):
    local_path = hf_hub_download(
        repo_id="NousResearch/hermes-function-calling-v1",
        filename=filename,
        repo_type="dataset"
    )

    samples = []
    df = pl.read_json(local_path)
    for i, row in enumerate(df.iter_rows()):
        try:
            samples.append(parse_to_openai(row))
        except Exception:
            pass

    return samples


def load(verbose: bool = False) -> list[list[chat_api.BaseItem]]:
    chats = (
        _load_dataset_openai("func-calling-singleturn.json")
        + _load_dataset_openai("func-calling.json")
        + _load_dataset_openai("glaive-function-calling-5k.json")
    )

    return chat_api.convert_openai_dataset(chats, require_tc_id=False, verbose=verbose)