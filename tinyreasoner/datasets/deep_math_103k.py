import polars as pl
from huggingface_hub import hf_hub_download, snapshot_download

from tinyreasoner import chat_api


def load():
    local_path = hf_hub_download(
        repo_id="trl-lib/DeepMath-103K",
        filename="data/train-00000-of-00001.parquet",
        repo_type="dataset"
    )


    df = pl.read_parquet(local_path)

    chats = []
    for prompt, solution in df.iter_rows():
        assert len(prompt) == 1 and prompt[0]['role'] == "user"
        content = prompt[0]["content"]
        content = content.replace("Provide a justification for your answer.", "")
        chats.append([
            chat_api.UserMessage(f"{content}\nOnly include the answer in your response."),
            chat_api.AssistantMessage(text=solution)
        ])

    return chats

