import os

import polars as pl
from huggingface_hub import hf_hub_download

from tinyreasoner import chat_api


def load():
    local_path = hf_hub_download(
        repo_id="HuggingFaceH4/MATH-500",
        filename="test.jsonl",
        repo_type="dataset"
    )


    df = pl.read_ndjson(local_path)

    chats = []
    for row in df.iter_rows(named=True):
        chats.append([
            chat_api.UserMessage(f"{row['problem']}. Only include the answer in your response."),
            chat_api.AssistantMessage(text=row["answer"])
        ])

        chats.append([
            chat_api.UserMessage(f"{row['problem']}. Give the solution and the answer."),
            chat_api.AssistantMessage(text=f"### Solution\n{row['solution']}\n\n### Answer\n{row['answer']}")
        ])

    return chats

