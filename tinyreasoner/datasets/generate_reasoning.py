import copy
import json
import os
import random
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import myagent
import polars as pl
import tqdm

from .. import chat_api

_cot_placeholder = "chain-of-thought-placeholder"

class FailedToGenerateReasoning(Exception): pass

_system_template = 'You are a chain-of-thought generator. You need to generate a chain-of-thought that will be used for training a tiny chat language model called tinyreasoner. You are provided with chat history, a request and the correct answer with a chain-of-thought placeholder (a "$PLACEHOLDER$" string) in between them. You need to analyze past chat history and the request, and generate a thorough step-by-step chain-of-thought which will replace the placeholder. The chain-of-thought starts with "I need to ", followed by necessary actions or calculations and their results, and ends with the correct answer. {optional_math}Do not skip any steps in the reasoning process. Your reply must only include the chain-of-thought and nothing else.'

_math_system_prompt = "You must manually perform all the calculations and arrive at the correct answer. If a calculation is hard, use some method like long multiplication. "

KEYS_ORDER = ("type", "tool_calls", "reasoning", "text", "name", "arguments", "output", "description", "parameters", "trainable")

def _reorder_dict(d: dict[str, Any], order=KEYS_ORDER):
    d_reordered = {}
    for k in order:
        if k in d:
            d_reordered[k] = d[k]

    if set(d_reordered.keys()) != set(d.keys()):
        raise RuntimeError(f"{set(d_reordered.keys())} != {set(d.keys())}")

    return d_reordered

def sample_to_flat_json_strings(chat: Sequence[chat_api.AnyItem]):
    chat = copy.deepcopy([chat_api.to_item(i) for i in chat])

    json_strings = []

    for item in chat:
        # reorder according to the order in which the values are used in a chat
        item = _reorder_dict(item, )
        item.pop('trainable', None)

        if item["type"] == "tool_definition":
            json_strings.append(json.dumps(item, ensure_ascii=False, sort_keys=False))

        elif item["type"] == "assistant":
            for tc in item["tool_calls"]:
                tc.pop("trainable")
                json_strings.append(json.dumps(_reorder_dict(tc), ensure_ascii=False, sort_keys=False))

            item.pop("tool_calls")
            if item["reasoning"] or item["text"]:
                json_strings.append(json.dumps(item, ensure_ascii=False, sort_keys=False))

        else:
            json_strings.append(json.dumps(item, ensure_ascii=False, sort_keys=False))

    return [s.replace("\\n", "\n") for s in json_strings]

def _generate_reasoning(
    items_before: Sequence[chat_api.BaseItem],
    gen_turn: chat_api.AssistantMessage,
    include_math_prompt: bool,
    lm: myagent.AnyLanguageModel,
    callbacks=None,
) -> str | None:
    items_before = list(items_before)
    items_new: list[chat_api.BaseItem] = [gen_turn]

    strings_new_turn = sample_to_flat_json_strings(items_new)
    if len(items_before) == 1:
        strings_before = sample_to_flat_json_strings(items_before)
        chat_string = '\n'.join(strings_before + strings_new_turn)

    else:
        if items_new[-1]["tool_calls"]:
            # last message has tool calls, last tool call needs reasoning
            if items_new[-1]["tool_calls"][-1]["reasoning"] == _cot_placeholder:
                assert len(items_new) == 1
                assert items_new[0]["text"] == ""
                assert items_new[0]["reasoning"] == ""

                # clear tool output
                items_new[0]["tool_calls"][-1].pop("output")
                strings_new_turn = sample_to_flat_json_strings(items_new)
                assert all("tool_call" in s for s in strings_new_turn), strings_new_turn

                strings_before = sample_to_flat_json_strings(items_before)
                strings_before.extend(strings_new_turn[:-1])
                strings_new_turn = [strings_new_turn[-1]]

                chat_string = f"Here is the context of this chat:\n```\n{'\n'.join(strings_before)}\n```\n\nFill in the reasoning for this tool call by the assistant:\n```\n{'\n'.join(strings_new_turn)}\n```\n\nOnly include the reasoning in your answer."

            elif items_new[-1]["text"]:
                # last message has tool calls, all tool calls have reasoning,
                # convesational response needs reasoning
                strings_before = sample_to_flat_json_strings(items_before)
                strings_before.extend(strings_new_turn[:-1])
                strings_new_turn = [strings_new_turn[-1]]
                chat_string = f"Here is the context of this chat:\n```\n{'\n'.join(strings_before)}\n```\n\nThe assistant has called the tools and received their outputs, and is presenting the information to the user. Fill in the reasoning for assistant's following conversational message:\n```\n{'\n'.join(strings_new_turn)}\n```\n\nOnly include the reasoning in your answer."

            else:
                # last message has only pending tool calls and no text, no reasoning needed
                return None

        else:
            # last message has no tool calls, convesational response needs reasoning
            assert items_new[-1]["text"]
            assert len(strings_new_turn) == 1, strings_new_turn
            strings_before = sample_to_flat_json_strings(items_before)
            chat_string = f"Here is the context of this chat:\n```\n{'\n'.join(strings_before)}\n```\n\nFill in the reasoning for assistant's following response to user's last message:\n```\n{'\n'.join(strings_new_turn)}\n```\n\nOnly include the reasoning in your answer."

    system = _system_template.replace("$PLACEHOLDER$", _cot_placeholder)
    if include_math_prompt: system = system.format(optional_math=_math_system_prompt)
    else: system = system.format(optional_math="")

    messages = [
        myagent.SystemMessage(system),
        myagent.UserMessage(chat_string)
    ]
    # print(f'-------------------------------------------------\n{messages}\n\n')

    # NOTE: we use very small model for generating reasoning and it's not always good at following instructions
    # but that's fine, we only need a starting point for RL
    output = myagent.agent_step(lm, messages, streaming=True, callbacks=callbacks).content
    return (
        output
        .replace(_cot_placeholder, "the reasoning")
        .replace(_cot_placeholder.capitalize(), "The reasoning")
    )


def _generate_one_reasoning_chain_for_turn(
    items_before: list[chat_api.BaseItem],
    assistant_turn: chat_api.AssistantMessage,
    include_math_prompt: bool,
    lm,
    callbacks,
) -> tuple[chat_api.AssistantMessage, bool]:
    """Generates one missing reasoning chain, applies following rules:
    - All tool calls must have reasoning.
    - All assistant messages have reasoning.
    """

    # add reasoning to tool calls
    for i, tc in enumerate(assistant_turn.tool_calls):
        if not tc.reasoning:
            gen_turn = copy.deepcopy(assistant_turn)
            gen_turn.tool_calls = copy.deepcopy(assistant_turn.tool_calls[:i + 1])
            gen_turn.tool_calls[-1].output = None
            gen_turn.tool_calls[-1].reasoning = _cot_placeholder
            gen_turn.text = ""

            reasoning = _generate_reasoning(
                items_before=copy.deepcopy(items_before),
                gen_turn=gen_turn,
                lm = lm,
                include_math_prompt = include_math_prompt,
                callbacks = callbacks,
            )

            if reasoning is None:
                return assistant_turn, False

            tc.reasoning = reasoning
            return assistant_turn, True

    # add reasoning to final message
    if not assistant_turn.reasoning:
        gen_turn = copy.deepcopy(assistant_turn)
        gen_turn.reasoning = _cot_placeholder
        reasoning = _generate_reasoning(
            items_before=copy.deepcopy(items_before),
            gen_turn=gen_turn,
            lm = lm,
            include_math_prompt = include_math_prompt,
            callbacks = callbacks,
        )

        if reasoning is None:
            return assistant_turn, False

        assistant_turn.reasoning = reasoning
        return assistant_turn, True

    return assistant_turn, False

def generate_reasoning_chains_for_chat(
    items: Sequence[chat_api.BaseItem],
    include_math_prompt: bool,
    lm: myagent.AnyLanguageModel,
    callbacks=None,
) -> list[chat_api.BaseItem]:
    items = copy.deepcopy(list(items))
    items_before = []

    for i, item in enumerate(items.copy()):

        if isinstance(item, chat_api.AssistantMessage):
            generated = True

            while generated:
                items[i], generated = _generate_one_reasoning_chain_for_turn(
                    items_before=copy.deepcopy(items_before),
                    assistant_turn=cast(chat_api.AssistantMessage, items[i]),
                    include_math_prompt=include_math_prompt,
                    lm=lm,
                    callbacks=callbacks,
                )

        items_before.append(item)

    chat_api.validate_chat(items)
    return items


def run_generate_reasoning_for_dataset(
    samples: Sequence[Sequence[chat_api.BaseItem]],
    include_math_prompt: bool,
    lm: myagent.AnyLanguageModel,
    file: str | os.PathLike,
):
    samples = list(samples)
    file = Path(file)

    if file.exists():
        with open(file, "r", encoding='utf-8') as f:
            existing_samples = [list(map(chat_api.to_item, json.loads(line))) for line in f.read().split('\n') if len(line) > 0]
            processed = ['\n'.join(msg.text for msg in sample if isinstance(msg, chat_api.UserMessage)) for sample in existing_samples]

    else:
        processed = []

    pbar = tqdm.tqdm(total=len(samples))
    pbar.update(len(processed))

    with open(file, "a", encoding='utf-8') as f:

        # pick random sample
        try:
            for sample in tqdm.tqdm(random.sample(samples, k=len(samples))):

                assert isinstance(sample[0], (chat_api.UserMessage, chat_api.ToolDefinition))
                user = '\n'.join(msg.text for msg in sample if isinstance(msg, chat_api.UserMessage))
                if user in processed: continue

                # generate reasoning chains
                generated = generate_reasoning_chains_for_chat(items=sample, include_math_prompt=include_math_prompt, lm=lm)

                # append new samples
                f.write(f"{json.dumps(generated, sort_keys=False, ensure_ascii=False)}\n")
                processed.append(user)
                pbar.update(1)

        except KeyboardInterrupt:
            pass

ROOT = "/run/media/jj/Ext2TB/Files/Main/Programming/Projects/tinyreasoner/notebooks/datasets/generated_reasoning"

def try_json_load(sample, path):
    try:
        return json.loads(sample)
    except Exception as e:
        print(path, sample)
        raise e

def load(include=None, exclude=None) -> list[list[chat_api.BaseItem]]:
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
                items = [[chat_api.to_item(i) for i in try_json_load(sample.strip(), path)] for sample in f.read().split('\n') if len(sample.strip()) > 0]
                samples.extend(items)

    if include:
        raise FileNotFoundError(f"Following `include` files were not found: {include}")
    if exclude:
        raise FileNotFoundError(f"Following `exclude` files were not found: {exclude}")

    return samples