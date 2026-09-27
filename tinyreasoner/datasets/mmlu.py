import polars as pl
from huggingface_hub import hf_hub_download

from tinyreasoner import chat_api


def load_w_choices():
    local_path_train = hf_hub_download(
        repo_id="cais/mmlu",
        filename="all/auxiliary_train-00000-of-00001.parquet",
        repo_type="dataset"
    )
    df = pl.read_parquet(local_path_train)
    samples = []

    for row in df.iter_rows(named=True):

        choices = row["choices"]
        question = row["question"]
        answer = choices[row["answer"]]

        choices_str = ' - ' + '\n - '.join(choices)
        items = [
            chat_api.UserMessage(f"{question}. Write out the correct choice:\n{choices_str}"),
            chat_api.AssistantMessage(text=f"{answer}"),
        ]

        samples.append(items)
    return samples

def load_w_numbered_choices():
    local_path_train = hf_hub_download(
        repo_id="cais/mmlu",
        filename="all/auxiliary_train-00000-of-00001.parquet",
        repo_type="dataset"
    )
    df = pl.read_parquet(local_path_train)
    samples = []

    for row in df.iter_rows(named=True):

        choices = row["choices"]
        question = row["question"]
        answer = row["answer"]

        choices_str = ""
        for i,c in enumerate(choices, start=1):
            choices_str = f'{choices_str}\n{i}: {c}'

        items = [
            chat_api.UserMessage(f"{question}. Write the number of the correct choice :{choices_str}"),
            chat_api.AssistantMessage(text=f"{answer + 1}"),
        ]

        samples.append(items)
    return samples


def load_w_o_choices():
    local_path_train = hf_hub_download(
        repo_id="cais/mmlu",
        filename="all/auxiliary_train-00000-of-00001.parquet",
        repo_type="dataset"
    )
    df = pl.read_parquet(local_path_train)
    samples = []

    for row in df.iter_rows(named=True):

        choices = row["choices"]
        question = row["question"]
        answer = choices[row["answer"]]

        items = [
            chat_api.UserMessage(question),
            chat_api.AssistantMessage(text=answer),
        ]

        samples.append(items)
    return samples

def load() -> list[list[chat_api.BaseItem]]:
    return load_w_choices() + load_w_numbered_choices() + load_w_o_choices()