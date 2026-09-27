import copy
import json
import os
import random
import re
import warnings
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal, cast

import json_repair
import myagent
import myagent as ma
import polars as pl
import tqdm
import wonderwords
from wonderwords import RandomWord

from .. import chat_api


def load_json_string(s: str) -> Any:
    try:
        return json.loads(s, strict=False)
    except Exception:
        return json_repair.loads(s, strict=False)

def extract_string_between(s: str, start: str, end: str):
    if start not in s:
        raise ValueError("Substring start not in s")
    if end not in s:
        raise ValueError("Substring end not in s")

    s = s[s.find(start) + len(start) : s.rfind(end)]
    return s

_random_word = RandomWord()

_templates = (
    # me me me
    "The question should be a math problem about {}.",
    "The question should be a puzzle about {}.",
    "The question should be about {}.",
    "Your training sample should be a conversation about {}.",
    "Your training sample should be about a joke about {}.",
    "Your training sample should be a question about {}.",
    "Your training sample should be {} themed.",
    "Your training sample should be a logic problem about {}.",
    "Your training sample should be a word problem about {}.",
    "Your training sample should be a coding problem about {}.",
    "Your training sample should be homework help about {}.",
    "Your training sample should be a social media post draft about {}.",
    "Your training sample should be a basic question about {}.",
    "Your training sample should be a stupid question about {}.",
    "Your training sample should be a dumb question about {}.",
    "Your training sample should be a silly question about {}.",
    "Your training sample should involve chit-chat about {}.",
    "Your training sample should involve banter about {}.",
    "Your training sample should be a debate about {}.",
    "Your training sample involve the user messing with the model by writing nonsense about {}.",
    "Your training sample involve the user testing the model by writing nonsense about {}.",
    "Your training sample involve the user testing the model's knowledge about {}.",
    "In your training sample the user should be attempting to troll the model about {}.",
    "In your training sample the user should be attempting to confuse the model about {}.",
    "In your training sample the user should be incorrect about {}, and the model should correct them.",
    "Your training sample should involve the user testing the model about {}.",
    "Your training sample should be a benchmark of model capabilities related to {}.",
    "Your training sample should be an automated workflow related to {}.",
    "Your training sample should request the model to produce structured output on the topic of {}.",

    # formatting
    "In your training sample the user should ask the model to output a structured response about {} in precise format, specified by the user.",
    "In your training sample the user should ask the model to output a JSON string using a JSON schema, specified by the user. The sample should be about {}.",
    "In your training sample the user should ask the model to output an XML string using an XML schema, specified by the user. The sample should be about {}.",
    "In your training sample the user should ask the model to output the answer between two strings, specified by the user. The sample should be about {}.",
    "In your training sample the user should ask the model to produce a structured output in precise format, specified by the user. The sample should be about {}.",
    "In your training sample the user should ask the model to produce an answer in precise LaTEX format, specified by the user. The sample should be about {}.",
    "In your training sample the user should ask the model to respond in a precise format, specified by the user. The sample should be about {}.",
    "In your training sample the user should ask the model to respond in a precise template, specified by the user. The sample should be about {}.",

    # qwen
    "Your training sample should be a factual explanation of {}.",
    "Your training sampleample should be a brief history of {}.",
    "Your training sample should be a scientific description of {}.",
    "Your training sample should be a geographical fact about {}.",
    "Your training sample should be a biographical summary of {}.",
    "Your training sample should be a definition and explanation of {}.",
    "Your training sample should be an encyclopedia entry about {}.",
    "Your training sample should be a list of interesting facts about {}.",
    "Your training sample should be a detailed overview of {}.",
    "Your training sample should be a factual report on {}.",
    "Your training sample should be a descriptive paragraph about the physical characteristics of {}.",

    "Your training sample should be a comparative analysis of {}.",
    "Your training sample should be a breakdown of the pros and cons of {}.",
    "Your training sample should be an explanation of the cause and effect related to {}.",
    "Your training sample should be a step-by-step analysis of {}.",
    "Your training sample should be a troubleshooting guide for issues related to {}.",
    "Your training sample should be a deductive reasoning exercise involving {}.",
    "Your training sample should be an evaluation of the societal impact of {}.",
    "Your training sample should be a SWOT analysis of {}.",
    "Your training sample should be a root cause analysis of a problem involving {}.",

    "Your training sample should be a step-by-step guide on how to use {}.",
    "Your training sample should be a factual tutorial about {}.",
    "Your training sample should be a set of instructions for assembling {}.",
    "Your training sample should be a safety guide regarding {}.",
    "Your training sample should be a maintenance guide for {}.",
    "Your training sample should be a beginner's guide to understanding {}.",
    "Your training sample should be a recipe or formula involving {}.",

    "Your training sample should be an etymological breakdown of the word {}.",
    "Your training sample should be a list of synonyms and antonyms for {}.",
    "Your training sample should be a grammatical explanation of how to use {} in a sentence.",
    "Your training sample should be a translation of the word {} into three different languages.",
    "Your training sample should be an explanation of the cultural significance of {}.",
    "Your training sample should be a phonetic breakdown of the word {}.",

    "Your training sample should be an interview with an expert about {}.",
    "Your training sample should be a customer support dialogue regarding {}.",
    "Your training sample should be a Q&A session about {}.",
    "Your training sample should be a dialogue between a teacher and a student about {}.",
    "Your training sample should be a debate regarding {}.",

    "Your training sample should be a structured outline for an essay about {}.",
    "Your training sample should be a concise summary of {}.",
    "Your training sample should be a timeline of major events related to {}.",

    "Your training sample should be a physics concept explanation involving {}.",
    "Your training sample should be a chemistry explanation involving {}.",
    "Your training sample should be a biological classification of {}.",
    "Your training sample should be an astronomical fact about {}.",
    "Your training sample should be a geological description of {}.",
    "Your training sample should be a mathematical theorem related to {}.",
    "Your training sample should be a geometry problem involving {}.",
    "Your training sample should be a probability question involving {}.",

    "Your training sample should be a code snippet demonstrating {}.",
    "Your training sample should be a debugging scenario involving {}.",
    "Your training sample should be an algorithm design problem using {}.",
    "Your training sample should be a database schema design involving {}.",
    "Your training sample should be a software architecture pattern involving {}.",

    # The goat granite
    "Your training sample should be a historical question about {}.",
    "Your training sample should be a science question about {}.",
    "Your training sample should be a literature question about {}.",
    "Your training sample should be a geography question about {}.",
    "Your training sample should be a music question about {}.",
    "Your training sample should be a film question about {}.",
    "Your training sample should be a sports question about {}.",
    "Your training sample should be a cooking question about {}.",
    "Your training sample should be a technology question about {}.",
    "Your training sample should be an art question about {}.",
    "Your training sample should be an economics question about {}.",
    "Your training sample should be a philosophy question about {}.",
    "Your training sample should be a fitness question about {}.",
    "Your training sample should be a travel question about {}.",
    "Your training sample should be a fashion question about {}.",
    "Your training sample should be a pet question about {}.",
    "Your training sample should be a DIY project about {}.",
    "Your training sample should be a gardening question about {}.",
    "Your training sample should be a language learning question about {}.",
    "Your training sample should be a cybersecurity question about {}.",
    "Your training sample should be a marketing question about {}.",
    "Your training sample should be a negotiation scenario about {}.",
    "Your training sample should be a customer service interaction about {}.",
    "Your training sample should be a role-playing scenario about {}.",
    "Your training sample should be a debate topic about {}.",
    "Your training sample should be a personal development question about {}.",
    "Your training sample should be a family planning question about {}.",
    "Your training sample should be a career advice question about {}.",
    "Your training sample should be a relationship advice question about {}.",
    "Your training sample should be a mental health question about {}.",
    "Your training sample should be a sustainability question about {}.",
    "Your training sample should be a space exploration question about {}.",
    "Your training sample should be a mythology question about {}.",
    "Your training sample should be a folklore question about {}.",
    "Your training sample should be a coding challenge about {}.",
    "Your training sample should be a data analysis question about {}.",
    "Your training sample should be a machine learning question about {}.",
    "Your training sample should be a statistical question about {}.",
    "Your training sample should be a probability question about {}.",
    "Your training sample should be a calculus question about {}.",
    "Your training sample should be a geometry question about {}.",
    "Your training sample should be a trigonometry question about {}.",
    "Your training sample should be a physics question about {}.",
    "Your training sample should be a chemistry question about {}.",
    "Your training sample should be a biology question about {}.",
    "Your training sample should be a astronomy question about {}.",
    "Your training sample should be a environmental science question about {}.",
    "Your training sample should be a geology question about {}.",
    "Your training sample should be a meteorology question about {}.",
    "Your training sample should be a oceanography question about {}.",
    "Your training sample should be a paleontology question about {}.",
    "Your training sample should be a zoology question about {}.",
    "Your training sample should be a botany question about {}.",
    "Your training sample should be a nutrition question about {}.",
    "Your training sample should be a culinary technique question about {}.",
    "Your training sample should be a question about tinyreasoner's capacities related to {}.",
    "Your training sample should be a question about tinyreasoner and {}."
)

class InvalidExample(Exception): pass

def generate_sample_single_turn(
    lm: ma.BaseLanguageModel, callbacks, templates: Sequence[str]
) -> list[chat_api.UserMessage | chat_api.AssistantMessage] | None:
    if random.random() < 0.01:
        word = "tinyreasoner"
    else:
        choice = random.choices([1,2,3], k=1, weights=[4,2,1])[0]
        if choice == 1:
            word = _random_word.word(include_categories=["noun"])
        elif choice == 2:
            if random.random() > 0.5:
                word = f'{_random_word.word(include_categories=["adjective"])} {_random_word.word(include_categories=["noun"])}'
            else:
                word = f'{_random_word.word(include_categories=["noun"])} {_random_word.word(include_categories=["verb"])}'
        elif choice == 3:
            word = f"{_random_word.word(include_categories=["noun"])} and {_random_word.word(include_categories=["noun"])}"
        else:
            raise RuntimeError("can't happen")

    lm_messages = [
        myagent.SystemMessage("You are a training example generator for a dataset. You need to generate one example that will be used for training a tiny chat language model called tinyreasoner."),
        myagent.UserMessage(f'''Generate a very basic training example as a JSON string with two string fields: "user" with user's message to the model, and "assistant" with model's response. For example:
```json
{{"user": "who are you", "assistant": "I am tinyreasoner, a tiny language model."}}
```

{random.choice(templates).format(word)} The prompt should not assume any prior chat history, and the model shouldn't make anything up.
''')]

    lm_output = lm.agent_step(lm_messages, streaming=True, callbacks=callbacks).content
    assert lm_output is not None

    try:
        lm_output_json = load_json_string(f"{{{extract_string_between(lm_output, r"{", r"}")}}}")
        if "user" not in lm_output_json or "assistant" not in lm_output_json: raise InvalidExample("No user or assistant message.")
        return [chat_api.UserMessage(lm_output_json["user"]), chat_api.AssistantMessage(text=lm_output_json["assistant"])]

    except Exception as e:
        print(f"Error parsing LM output:\n{lm_output}")
        print(f"The error is:\n{e}")
        return None

_multi_turn_w_system = """Each message has two string fields: "role" - "system", "user" or "assistant", and "content" with the content of the message. The first message should be either a system or a user message. System message is always followed by a user message."""
_multi_turn_w_o_system = """Each message has two string fields: "role" - "user" or "assistant", and "content" with the content of the message. The first message should a user message."""

def generate_sample_multi_turn(lm: ma.BaseLanguageModel, callbacks, w_system:bool, templates: Sequence[str]) -> list[chat_api.UserMessage | chat_api.AssistantMessage] | None:
    if random.random() < 0.01:
        word = "tinyreasoner"
    else:
        choice = random.choices([1,2,3], k=1, weights=[4,2,1])[0]
        if choice == 1:
            word = _random_word.word(include_categories=["noun"])
        elif choice == 2:
            if random.random() > 0.5:
                word = f'{_random_word.word(include_categories=["adjective"])} {_random_word.word(include_categories=["noun"])}'
            else:
                word = f'{_random_word.word(include_categories=["noun"])} {_random_word.word(include_categories=["verb"])}'
        elif choice == 3:
            word = f"{_random_word.word(include_categories=["noun"])} and {_random_word.word(include_categories=["noun"])}"
        else:
            raise RuntimeError('cant happen')

    user_message = f'''Generate a very basic multi-turn training example of as a JSON array of messages. %TEMPLATE% Example:
```json
[
    {{"role": "user", "content": "whats 2+2"}},
    {{"role": "assistant", "content": "4"}},
    {{"role": "user", "content": "no its 5"}},
    {{"role": "assistant", "content": "In standard arithmetic, 2 + 2 = 4, not 5."}},
    {{"role": "user", "content": "why not"}},
    {{"role": "assistant", "content": "Because if you combine a set of 2 items with another set of 2 items, you will always get 4 total items."}},
    {{"role": "user", "content": "k you convinced me"}},
    {{"role": "assistant", "content": "Glad to help!"}}
]
```

{random.choice(templates).format(word)} The model shouldn't assume any knowledge about the user and shouldn't make anything up.
'''

    if w_system: user_message = user_message.replace("%TEMPLATE%", _multi_turn_w_system)
    else: user_message = user_message.replace("%TEMPLATE%", _multi_turn_w_o_system)

    lm_messages = [
        myagent.SystemMessage("You are a training example generator for a dataset. You need to generate one multi-turn example that will be used for training a tiny chat language model called tinyreasoner."),
        myagent.UserMessage(user_message)]

    lm_output = lm.agent_step(lm_messages, streaming=True, callbacks=callbacks).content
    assert lm_output is not None

    try:
        lm_output_json = load_json_string(f"[{extract_string_between(lm_output, '[', ']')}]")

        for msg in lm_output_json:
            if ("role" not in msg) or ("content" not in msg): raise InvalidExample("No 'role' or 'content' key.")
            msg["role"] = str(msg["role"]).lower().strip()
            if msg["role"] not in ("system", "user", "assistant"): raise InvalidExample(f"Invalid role {msg['role']}")

        if not any(msg["role"] == "user" for msg in lm_output_json): raise InvalidExample("No user messages.")
        if not any(msg["role"] == "assistant" for msg in lm_output_json): raise InvalidExample("No assistant messages.")

        training_sample = []
        for msg in lm_output_json:
            # NOTE: we don't have system role, it's just another user message
            if msg["role"] in ("system", "user"): training_sample.append(chat_api.UserMessage(msg["content"]))
            elif msg["role"] == "assistant": training_sample.append(chat_api.AssistantMessage(text=msg["content"]))
            else: raise RuntimeError("can't happen")

        return training_sample

    except Exception as e:
        print(f"Error parsing LM output:\n{lm_output}")
        print(f"The error is:\n{e}")
        return None


def generate_sample_tool_calling(lm: ma.BaseLanguageModel, callbacks, templates: Sequence[str]) -> list[chat_api.UserMessage | chat_api.AssistantMessage] | None:
    if random.random() < 0.01:
        word = "tinyreasoner"
    else:
        choice = random.choices([1,2,3], k=1, weights=[4,2,1])[0]
        if choice == 1:
            word = _random_word.word(include_categories=["noun"])
        elif choice == 2:
            if random.random() > 0.5:
                word = f'{_random_word.word(include_categories=["adjective"])} {_random_word.word(include_categories=["noun"])}'
            else:
                word = f'{_random_word.word(include_categories=["noun"])} {_random_word.word(include_categories=["verb"])}'
        elif choice == 3:
            word = f"{_random_word.word(include_categories=["noun"])} and {_random_word.word(include_categories=["noun"])}"
        else:
            raise RuntimeError('cant happen')

    lm_messages = [
        myagent.SystemMessage("You are a training example generator for a dataset. You need to generate one tool-calling example that will be used for training a tiny chat language model called tinyreasoner."),
        myagent.UserMessage(f'''Generate a very basic tool-calling training example of as a JSON array of tool definitions and messages.

The format for training examples uses one shared JSON array with both tool definitions and messages in one JSON. Start with the tool definition elements that have the following fields:
- "role": always "tool_definition"
- "name": name of the tool (string)
- "description": description of the tool (string)
- "parameters": parameters according to function calling spec from the OpenAI API (dict).

You can also define some extra tools that are not needed for this example so that the model learns to choose the correct tools. Tools should be realistic and similar to real world agentic tools.

Then continue writing message elements to the same array. Messages have the following fields:
- "role": "system", "user" or "assistant".
- "tool_call": a tool call (dict), stores both the input to the tool, and the output of the tool.
- "content": content of the message (string).

"tool_call" field in the assitant message must have the following fields:
- "name": name of the tool to call (string).
- "args": arguments to pass to the tool (dict)
- "tool_output": output that the tool returned (string).

Example
```json
[
    {{
        "role": "tool_definition",
        "name": "send_email",
        "description": "Sends an email to a specific recipient.",
        "parameters": {{
            "type": "object",
            "properties": {{
                "recipient": {{
                    "type": "string",
                    "description": "The email address of the recipient (e.g., user@example.com)"
                }},
                "body": {{
                    "type": "string",
                    "description": "The plain text body content of the email."
                }},
                "urgency": {{
                    "type": "string",
                    "enum": ["low", "normal", "high"],
                    "description": "The priority level of the email."
                }}
            }},
            "required": ["recipient", "body"]
        }}
    }},
    {{"role": "user", "content": "send URGENT email to boss@gmail.com tell him ill be 1 hour late"}},
    {{
        "role": "assistant",
        "content": "I'll use the `send_email` tool to send the email.",
        "tool_call": {{
            "name": "send_email",
            "args": {{
                "recipient": "boss@gmail.com",
                "body": "I will be 1 hour late.",
                "urgency": "high"
            }},
            "tool_output": "Mail sent."
        }}
    }},
    {{"role": "assistant", "content": "I have sent an email to boss@gmail.com saying that you will be 1 hour late. The tool returned `Mail sent`, confirming that the email was sent."}}
]
```

{random.choice(templates).format(word)} The model shouldn't assume any knowledge about the user and shouldn't make anything up.
''')]

    lm_output = lm.agent_step(lm_messages, streaming=True, callbacks=callbacks).content
    assert lm_output is not None

    try:
        lm_output_json = load_json_string(f"[{extract_string_between(lm_output, '[', ']')}]")

        for msg in lm_output_json:
            if "role" not in msg: raise InvalidExample("No 'role' key in message.")
            msg["role"] = str(msg["role"]).lower().strip()
            if msg["role"] not in ("system", "user", "assistant", "tool_definition"):
                raise InvalidExample(f"Invalid role {msg['role']}")

            if msg["role"] == "tool_definition":
                if "name" not in msg or "description" not in msg or "parameters" not in msg:
                    raise InvalidExample("Missing 'name' or 'description' or 'parameters' from tool definition.")

                if isinstance(msg["parameters"], str):
                    msg["parameters"] = load_json_string(msg["parameters"])

            else:
                if "content" not in msg: raise InvalidExample(f"No 'content' in {msg['role']} message")

            if "tool_call" in msg:
                tc = msg["tool_call"]
                if "tool_output" not in tc and "output" in tc: tc["tool_output"] = tc["output"]
                if "name" not in tc or "args" not in tc or "tool_output" not in tc:
                    raise InvalidExample("Missing 'name' or 'args' or 'tool_output' from tool call.")

                if isinstance(tc["args"], str): tc["args"] = load_json_string(tc["args"])

        if not any(msg["role"] == "user" for msg in lm_output_json): raise InvalidExample("No user messages.")
        if not any(msg["role"] == "assistant" for msg in lm_output_json): raise InvalidExample("No assistant messages.")

        training_sample = []
        for msg in lm_output_json:
            if msg["role"] == "tool_definition":
                training_sample.append(chat_api.ToolDefinition(name=msg["name"], description=msg["description"], parameters=msg["parameters"]))

            # we don't have system role, it's just another user message
            elif msg["role"] in ("system", "user"):
                training_sample.append(chat_api.UserMessage(msg["content"]))

            elif msg["role"] == "assistant":
                tool_call = None
                if "tool_call" in msg:
                    tc = msg["tool_call"]
                    tool_call = chat_api.ToolCall(name=tc["name"], arguments=tc["args"], output=tc["tool_output"])
                training_sample.append(chat_api.AssistantMessage(text=msg["content"], tool_call=tool_call))

            else: raise RuntimeError("can't happen")

        return training_sample

    except Exception as e:
        print(f"Error parsing LM output:\n{lm_output}")
        print(f"The error is:\n{e}")
        return None



def run_generate_dataset(
    lm: myagent.AnyLanguageModel,
    file: str | os.PathLike,
    type: Literal["single-turn", "multi-turn", "multi-turn-system", "tool-calling"],
    callbacks=None,
    templates:Sequence[str]=_templates,
):
    lm = ma.get_lm(lm)

    file = Path(file)

    if file.exists():
        with open(file, "r", encoding='utf-8') as f:
            existing_samples = [list(map(chat_api.to_item, json.loads(line))) for line in f.read().split('\n') if len(line) > 0]
            processed = ['\n'.join(msg.text for msg in sample if isinstance(msg, chat_api.UserMessage)) for sample in existing_samples]
    else:
        processed = []

    pbar = tqdm.tqdm()
    pbar.update(len(processed))

    with open(file, "a", encoding='utf-8') as f:

        while True:
            try:
                if type == "single-turn":
                    sample = generate_sample_single_turn(lm, callbacks,templates=templates)
                elif type == "multi-turn":
                    sample = generate_sample_multi_turn(lm, callbacks, w_system=False,templates=templates)
                elif type == "multi-turn-system":
                    sample = generate_sample_multi_turn(lm, callbacks, w_system=True,templates=templates)
                elif type == "tool-calling":
                    sample = generate_sample_tool_calling(lm, callbacks,templates=templates)
                else:
                    raise ValueError(type)

                if sample is None: continue

                user = '\n'.join(msg.text for msg in sample if isinstance(msg, chat_api.UserMessage))
                if user in processed: continue

                sample_json = json.dumps(sample, sort_keys=False, ensure_ascii=False)
                f.write(f"{sample_json}\n")
                processed.append(user)
                pbar.update(1)

            except KeyboardInterrupt:
                break

ROOT = "/run/media/jj/Ext2TB/Files/Main/Programming/Projects/tinyreasoner/notebooks/datasets/generated"

def try_json_load(sample, path):
    try:
        d = json.loads(sample)
        for message in d:
            if "text" in message: message["text"] = str(message["text"])
        return d
    except Exception as e:
        print(path, sample)
        raise e

def load(include=None, exclude=None, verbose=False) -> list[list[chat_api.BaseItem]]:
    if isinstance(include, str): include = [include]
    if isinstance(exclude, str): exclude = [exclude]

    samples = []
    for file in os.listdir(ROOT):
        if file.endswith(".jsonl"):

            if include is not None:
                if file in include: include.remove(file)
                else: continue

            if exclude is not None:
                if file in exclude:
                    exclude.remove(file)
                    continue

            path = os.path.join(ROOT, file)
            with open(path, "r", encoding='utf-8') as f:
                chats = [[chat_api.to_item(i) for i in try_json_load(sample.strip(), path)] for sample in f.read().split('\n') if len(sample.strip()) > 0]

                for chat in chats:
                    try:
                        chat_api.validate_chat(chat)
                        samples.append(chat)
                    except Exception as e:
                        if verbose:
                            print(f"Invalid chat:\n{chat}")
                            print(f'The error is:\n{e}')
    if include:
        raise FileNotFoundError(f"Following `include` files were not found: {include}")
    if exclude:
        raise FileNotFoundError(f"Following `exclude` files were not found: {exclude}")

    return samples