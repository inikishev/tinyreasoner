"""various datasets in ShareGPT format"""
import polars as pl
from huggingface_hub import hf_hub_download

from .. import chat_api


def load_wiki_qa() -> list[list[chat_api.BaseItem]]:
    local_path = hf_hub_download(
        repo_id="grimulkan/wikipedia-document-question-answer",
        filename="qa_wikipedia.json",
        repo_type="dataset"
    )


    df = pl.read_json(local_path)
    return chat_api.convert_sharegpt_dataset([r["conversations"] for r in df.iter_rows(named=True)])



def load_wiki_summaries() -> list[list[chat_api.BaseItem]]:
    local_path = hf_hub_download(
        repo_id="grimulkan/wikipedia-summaries",
        filename="wikipedia_summaries.json",
        repo_type="dataset"
    )


    df = pl.read_json(local_path)
    return chat_api.convert_sharegpt_dataset([r["conversations"] for r in df.iter_rows(named=True)])

def load_wiki_editing() -> list[list[chat_api.BaseItem]]:
    local_path1 = hf_hub_download(
        repo_id="grimulkan/document-editing",
        filename="wikipedia_err_correct.json",
        repo_type="dataset"
    )
    local_path2 = hf_hub_download(
        repo_id="grimulkan/document-editing",
        filename="wikipedia_err_correct.json",
        repo_type="dataset"
    )


    df = pl.concat([pl.read_json(local_path1), pl.read_json(local_path2)])
    return chat_api.convert_sharegpt_dataset([r["conversations"] for r in df.iter_rows(named=True)])


def load() -> list[list[chat_api.BaseItem]]:
    return load_wiki_editing() + load_wiki_qa() + load_wiki_summaries()