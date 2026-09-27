import copy
import itertools
import json
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, Self, cast

import langchain_core.tools
from langchain_core.utils.function_calling import convert_to_openai_function

if TYPE_CHECKING:
    from .tokenizer import BaseTokenizer


class InvalidChatError(Exception): pass


ItemTypeLiteral = Literal["user", "assistant", "tool_definition", "tool_call"]


class TokensAndMask(NamedTuple):
    tokens: list[int]
    mask: list[int]


class BaseItem(dict):
    def __repr__(self) -> str:
        kwargs_str = ", ".join(f"{k}={v}" for k, v in self.items())
        return f"{self.__class__.__name__}({kwargs_str})"

    @classmethod
    @abstractmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        """Create this item from a dictionary."""

    @property
    def type(self) -> ItemTypeLiteral: return self["type"]
    @type.setter
    def type(self, value: ItemTypeLiteral) -> None: self["type"] = value

    @abstractmethod
    def tokenize(self, tokenizer: "BaseTokenizer") -> TokensAndMask:
        """Returns tokens and mask. The mask for a token determines whether predicting that token contributes to loss.
        The mask should be shifted 1 to the left before being applied to the loss."""

    def to_dict(self) -> dict:
        return json.loads(json.dumps(self, ensure_ascii=False, sort_keys=False))


class BaseTrainableItem(BaseItem, ABC):
    @property
    def trainable(self) -> bool: return self["trainable"]
    @trainable.setter
    def trainable(self, value: bool) -> None: self["trainable"] = value


class UserMessage(BaseItem):
    def __init__(self, text: str):
        super().__init__(type="user", text=text)

    @classmethod
    def from_dict(cls, d):
        return cls(text=d["text"])

    def tokenize(self, tokenizer):
        tokens = [tokenizer.user_idx] + tokenizer.encode_text(self.text) + [tokenizer.end_idx]
        mask = [0] * len(tokens)
        return TokensAndMask(tokens, mask)

    @property
    def text(self) -> str: return self["text"]
    @text.setter
    def text(self, value: str) -> None: self["text"] = value


# ----------------------------------- tools ---------------------------------- #
class ToolCall(BaseTrainableItem):
    """A tool call.

    Args:
        name: Name of the tool.
        arguments: Arguments.
        output: The output of the tool as a string.
        trainable: Whether to include this tool call in loss calculation.
    """
    def __init__(self, name:str, arguments: str | dict[str, Any], output: str | None = None, trainable: bool = True):
        if isinstance(arguments, str): arguments = json.loads(arguments, strict=False)
        super().__init__(type="tool_call", name=name, arguments=arguments, output=output, trainable=trainable)

    @property
    def name(self) -> str: return self["name"]
    @name.setter
    def name(self, value: str) -> None: self["name"] = value

    @property
    def arguments(self) -> dict[str, Any]: return self["arguments"]
    @arguments.setter
    def arguments(self, value: dict[str, Any]) -> None: self["arguments"] = value

    @property
    def output(self) -> str | None:
        """The output of the tool as a string.
        When a model generates a `ToolCall`, this attribute must be set before sending this back to the model."""
        return self["output"]

    @output.setter
    def output(self, value: str | None): self["output"] = value

    @classmethod
    def from_dict(cls, d):
        return cls(
            name = d["name"],
            arguments = d["arguments"],
            output = d.get("output", None),
            trainable = d.get("trainable", True),
        )

    def tokenize(self, tokenizer):

        # parse inputs
        name = tokenizer.encode_text(self.name)
        arguments = tokenizer.encode_text(json.dumps(self.arguments, ensure_ascii=False, sort_keys=False))

        tc_tokens = (
            [tokenizer.tool_call_idx] + name
            + [tokenizer.space_idx] + arguments
            + [tokenizer.end_idx]
        )
        tc_mask = [int(self.trainable)] * len(tc_tokens)

        # parse outputs
        if self.output is not None:
            tool_output_tokens = tokenizer.encode_text(self.output)
            tool_output_mask = [0] * len(tool_output_tokens)
        else:
            tool_output_tokens = []
            tool_output_mask = []

        # merge
        return TokensAndMask(
            tokens = tc_tokens + tool_output_tokens,
            mask = tc_mask + tool_output_mask,
        )


class AssistantMessage(BaseTrainableItem):
    """An assistant message.

    Args:
        reasoning: reasoning before tool call and text.
        text: text displayed to the user (before the tool call).
        tool_call: tool call. Defaults to None.
        trainable: Whether to include this assistant message and reasoning in loss calculation.
    """

    def __init__(
        self,
        *,
        reasoning: str | None = "",
        text: str | None = "",
        tool_call: ToolCall | None = None,
        trainable: bool = True,
    ):
        if text is None: text = ""
        if reasoning is None: reasoning = ""

        if text == "" and tool_call is None:
            raise RuntimeError("Empty assistant message")

        super().__init__(type="assistant", reasoning=reasoning, text=text, tool_call=tool_call, trainable=trainable)

    @property
    def text(self) -> str: return self["text"]
    @text.setter
    def text(self, value: str) -> None: self["text"] = value

    @property
    def reasoning(self) -> str: return self["reasoning"]
    @reasoning.setter
    def reasoning(self, value: str) -> None: self["reasoning"] = value

    @property
    def tool_call(self) -> ToolCall | None: return self["tool_call"]
    @tool_call.setter
    def tool_call(self, value: ToolCall | None) -> None: self["tool_call"] = value

    @classmethod
    def from_dict(cls, d):
        tool_call = d.get("tool_call", None)
        if tool_call:
            tool_call = ToolCall.from_dict(tool_call)

        return cls(reasoning=d.get("reasoning", None), text=d.get("text", None), tool_call=tool_call, trainable=d.get("trainable", True))

    def tokenize(self, tokenizer):
        trainable = int(self.trainable)

        # tokenize reasoning
        reasoning_tokens = []
        reasoning_mask = []
        if self.reasoning:
            reasoning_tokens = [tokenizer.think_idx] + tokenizer.encode_text(self.reasoning) + [tokenizer.think_idx]
            reasoning_mask = [0] + [trainable] * (len(reasoning_tokens) - 1)

        # tokenize text
        if self.text:
            text_tokens = tokenizer.encode_text(self.text)
            text_mask = [trainable] * len(text_tokens)
        else:
            text_tokens = []
            text_mask = []

        # tokenize tool call or final [END]
        tc_or_end_tokens = []
        tc_or_end_mask = []

        if self.tool_call is None:
            tc_or_end_tokens = [tokenizer.end_idx]
            tc_or_end_mask = [trainable]
        else:
            # [TC] name arguments [END] output
            tc_or_end_tokens, tc_or_end_mask = self.tool_call.tokenize(tokenizer)

        # full tokenized message:

        # [ASSISTANT]
        # [THINK] reasoning [THINK]
        # text
        # [TC] name arguments [END] output

        # or:

        # [ASSISTANT]
        # [THINK] reasoning [THINK]
        # text [END]

        return TokensAndMask(
            tokens = [tokenizer.assistant_idx] + reasoning_tokens + text_tokens + tc_or_end_tokens,
            mask =   [0]                       + reasoning_mask   + text_mask   + tc_or_end_mask,
        )


class ToolDefinition(BaseItem):
    """A tool definition, placed in the beginning of the model input.

    Args:
        name: name of the tool
        description: description of the tool
        parameters: parameters following the OpenAI function schema.
    """
    def __init__(self, name: str, description: str, parameters: str | dict[str, Any]):
        if isinstance(parameters, str): parameters = json.loads(parameters, strict=False)
        super().__init__(name=name, description=description, parameters=parameters, type="tool_definition")

    @classmethod
    def from_function(cls, fn: Callable):
        """Generate a tool from a python function using langchain."""
        tool = langchain_core.tools.tool(fn)
        spec = convert_to_openai_function(tool)
        return cls(name=spec["name"], description=spec["description"], parameters=spec["parameters"])

    @property
    def name(self) -> str: return self["name"]
    @name.setter
    def name(self, value: str) -> None: self["name"] = value

    @property
    def description(self) -> str: return self["description"]
    @description.setter
    def description(self, value: str) -> None: self["description"] = value

    @property
    def parameters(self) -> dict[str, Any]: return self["parameters"]
    @parameters.setter
    def parameters(self, value: dict[str, Any]) -> None: self["parameters"] = value

    def get_json_string(self):
        schema = {"name": self.name, "description": self.description, "parameters": self.parameters}
        return json.dumps(schema, sort_keys=False, ensure_ascii=False)

    @classmethod
    def from_dict(cls, d):
        return cls(name=d["name"], description=d["description"], parameters=d["parameters"])

    def tokenize(self, tokenizer):
        definition = tokenizer.encode_text(self.get_json_string())
        tokens = [tokenizer.tool_definition_idx] + definition + [tokenizer.end_idx]
        return TokensAndMask(tokens, [0 for _ in tokens])


# Role = Literal["user", "assistant", "reasoning", "tool_output"]
# Type = Role | Literal["tool_call", "tool_definition", "assistant_start", 'assistant_end', "reasoning_start", "reasoning_end"]
AnyItem = BaseItem | dict
def to_item(x: AnyItem):
    if isinstance(x, BaseItem): return x
    if x["type"] == "user": return UserMessage.from_dict(x)
    if x["type"] == "assistant": return AssistantMessage.from_dict(x)
    if x["type"] == "tool_call": return ToolCall.from_dict(x)
    if x["type"] == "tool_definition": return ToolDefinition.from_dict(x)
    raise ValueError(f"Invalid type {x['type']} in {x}")


def validate_chat(items: Sequence[AnyItem]):
    """Validates that a given chat follows all rules.

    Rules:
    - Chat starts with ToolDefinitions or UserMessage
    - No two AssistantMessages in a row
    - either all AssistantMessages should have reasoning (think mode), or none should (instruct mode)
    - All tool calls should have tool outputs
    - Last item should be trainable (if last item is UserMessage, it contributes nothing to the loss and just increases train time)

    Special case:
    - The last assistant message can end with a pending tool call (no output).
    """

    items = [to_item(i) for i in items]

    # check empty chat
    if len(items) == 0:
        raise InvalidChatError("Got an empty list of items.")

    # check first message type
    if not isinstance(items[0], (ToolDefinition, UserMessage)):
        raise InvalidChatError("First message must be either a tool definition or a user message.")

    # check initial messages
    is_tool_defs = True
    for i, item in enumerate(items):
        if isinstance(item, ToolDefinition):
            if not is_tool_defs:
                raise InvalidChatError(
                    f"ToolDefinition can't follow a non ToolDefinition object, but previous item is {type(items[i-1])}.")
        else:
            if is_tool_defs and not isinstance(item, UserMessage):
                if i == 0: raise InvalidChatError("First message must be either a tool definition or a user message.")
                else: raise InvalidChatError(f"The first item after tool definitions must be UserMessage, but got {type(item)}.")
            is_tool_defs = False

    # check duplicate tool names
    available_tools = [item.name for item in items if isinstance(item, ToolDefinition)]
    if len(available_tools) != len(set(available_tools)):
        raise InvalidChatError(f"There are duplicate tools: {available_tools}")

    # check assistant message after final assistant message
    for i, (item1, item2) in enumerate(itertools.pairwise(items)):
        if isinstance(item1, AssistantMessage) and isinstance(item2, AssistantMessage) and item1.tool_call is None:
            raise InvalidChatError(f"AssistantMessage at index {i} has no tool calls (final message), but next message ({i+1}) is AssistantMessage.")

    # check reasoning
    is_think = None
    for item in items:
        if isinstance(item, AssistantMessage):
            is_think = bool(item.reasoning)
            break

    if is_think is None:
        raise InvalidChatError(f"The chat contains no assistant messages: {[type(i) for i in items]}.")

    for i, item in enumerate(items):
        is_last_message = (i == len(items) - 1)

        if isinstance(item, AssistantMessage):

            if is_think and not item.reasoning:
                raise InvalidChatError("Either all items should have reasoning, or none should, "
                                        "but got assistant messages with and without reasoning.")

            # check tool call
            if item.tool_call is not None:
                tc = item.tool_call

                # check that tool is defined
                if tc.name not in available_tools:
                    raise InvalidChatError(
                        f"ToolCall has name={tc.name}, but no tools with that name are defined. Defined tools: {available_tools}")

                # ensure all tool calls have outputs, ignoring last message
                if (not is_last_message) and (tc.output is None):
                    raise InvalidChatError(f"AssistantMessage at index {i} is not last, but has tool call `{tc.name}` with no outputs.")

                # check empty strings
                if len(tc.name) == 0 or len(tc.arguments) == 0 or (tc.output is not None and len(tc.output) == 0):
                    raise InvalidChatError(
                        f"AssistantMessage at index {i} has tool call `{tc.name}` with empty string in one of `name`, `arguments` or `output`.")

    # check that last item is trainable
    if not items[-1].get('trainable', False):
        raise InvalidChatError(f"Last item in the chat is not trainable: {[type(i) for i in items]}.")

    # check that there are any trainable items
    for item in items:
        if item.get("trainable", False):
            break
    else:
        raise InvalidChatError(f"All items have `trainable` set to False: {[type(i) for i in items]}.")

    # check that messages are not empty
    for i, item in enumerate(items):
        if isinstance(item, UserMessage) and len(item.text.strip()) == 0:
            raise InvalidChatError(f"UserMessage at index {i} contains empty text.")

        if isinstance(item, AssistantMessage) and len(item.text.strip()) == 0 and item.tool_call is None:
            raise InvalidChatError(f"AssistantMessage at index {i} contains empty text and no tool calls.")

        if isinstance(item, ToolDefinition):
            if len(item.name) == 0 or len(item.description) == 0:
                raise InvalidChatError(f"ToolDefinition `{item.name}` contains empty name or description: {item.to_dict()}")

    # TODO check tokenization
    # we need to implement a detokenizer to Items for this first

class InvalidCustomChatError(Exception): pass

def _parse_content(content: str | list | None | Any):
    if content is None:
        return None

    if isinstance(content, list):
        if any('text' not in el for el in content):
            raise InvalidCustomChatError("User message contains non-text content.")
        content = '\n'.join(el['text'] for el in content).strip()

    if not isinstance(content, str):
        raise InvalidCustomChatError(f"Content is not a string or a list, but {type(content)}:\n{content}")

    if len(content.strip()) == 0:
        return None

    return content.strip()


def convert_from_chat_completions_api(chat: dict, require_tc_id: bool = True, remove_reasoning: bool = False, allow_multiple_tool_calls: bool = False) -> list[BaseItem]:
    """Convert a chat completions dictionary to Items."""
    items: list[BaseItem] = []

    # parse tools
    defined_tools: set[str] = set()
    if "tools" in chat and chat["tools"] is not None:
        tools = chat["tools"]
        if isinstance(tools, str): tools = json.loads(tools.strip(), strict=False)

        for tool in chat["tools"]:
            if isinstance(tool, str): tool = json.loads(tool.strip(), strict=False)
            if "function" not in tool:
                assert "name" in tool
                tool = {"function": tool}

            defined_tools.add(tool["function"]["name"])
            items.append(
                ToolDefinition(
                    name=tool["function"]["name"],
                    description=tool["function"]["description"],
                    parameters=tool["function"]["parameters"],
                )
            )

    # parse messages
    for i, message in enumerate(chat["messages"]):
        if isinstance(message, str): message = json.loads(message.strip(), strict=False)

        # we only have user
        if message["role"] in ("user", "developer", "system"):
            user_content = _parse_content(message["content"])

            if user_content is None:
                raise InvalidCustomChatError("User message contains no content")

            items.append(UserMessage(user_content.strip()))

        elif message["role"] == "assistant":

            if len(items) == 0:
                raise InvalidCustomChatError(
                    "Chat starts from assistant message:\n",
                    f"{json.dumps(chat['messages'], sort_keys=False, ensure_ascii=False, indent=4)}",
                )

            # add tool calls
            tool_calls: list[ToolCall] = []
            if "tool_calls" in message and message["tool_calls"] is not None:
                for tc in message["tool_calls"]:
                    if isinstance(tc, str): tc = json.loads(tc.strip(), strict=False)

                    # format either {tool_call_def} or {function: {tool_call_def}}
                    tc_id = tc.get("id", None)
                    if tc_id is None and "function" in tc:
                        tc_id = tc["function"].get("id", None)

                    if "function" not in tc:
                        assert "name" in tc, tc
                        tc = {"function": tc}

                    tc_name = tc["function"]["name"]
                    tc_arguments = tc["function"]["arguments"]
                    if not isinstance(tc_arguments, str):
                        tc_arguments = json.dumps(tc_arguments, ensure_ascii=False, sort_keys=False)

                    if tc_id is None:
                        if require_tc_id:
                            raise InvalidCustomChatError(
                                f"Tool call id (key 'id') missing:\n"
                                f"{json.dumps(message, sort_keys=False, ensure_ascii=False, indent=4)}\n"
                            )


                    # check that tool call name exists
                    if tc_name not in defined_tools:
                        raise InvalidCustomChatError(
                            f"{tc} is not defined in {defined_tools}:\n",
                            f"{json.dumps(chat, sort_keys=False, ensure_ascii=False, indent=4)}",
                        )

                    # Find content of the tool call, it is injected right after tool call, no tool messages
                    tool_messages = []

                    # get all tool messages before the next non tool message
                    for next_message in chat["messages"][i + 1:]:
                        if isinstance(next_message, str): next_message = json.loads(next_message, strict=False)
                        if next_message["role"] != "tool": break
                        tool_messages.append(next_message)

                    if len(tool_messages) == 0:
                        raise InvalidCustomChatError(
                            f"There are no tool messages after tool call:\n"
                            f"{json.dumps(chat['messages'], sort_keys=False, ensure_ascii=False, indent=4)}"
                        )

                    if tc_id is None:

                        # get tool by name, but make sure tool call with that name is unique
                        # to avoid ambiguity
                        tool_names = [tm["name"] for tm in tool_messages]
                        if tc_name not in tool_names:
                            raise InvalidCustomChatError(
                                f"Tool call has no id and has name {tc_name}, and "
                                f"there is no tool message with that name, found names: {tool_names}\n"
                                f"{json.dumps(message, sort_keys=False, ensure_ascii=False, indent=4)}"
                            )

                        if tool_names.count(tc_name) > 1:
                            raise InvalidCustomChatError(
                                f"Tool call is ambiguous: has no id and has name {tc_name}, but "
                                f"multiple tool messages are using this name: {tool_names}\n"
                            )

                        # Get the tool message
                        tool_message = None
                        for tm in tool_messages:
                            if tm["name"] == tc_name:
                                tool_message = tm
                                break

                        assert tool_message is not None

                    else:
                        # tool call id is defined
                        tool_message = None
                        seen_ids = []
                        for tm in tool_messages:
                            seen_ids.append(tm["tool_call_id"])
                            if tm["tool_call_id"] == tc_id:
                                tool_message = tm
                                break

                        if tool_message is None:
                            raise InvalidCustomChatError(
                                f"Tool call id is {tc_id}, but there is no tool message with that id."
                                f"Seen ids: {seen_ids}"
                            )

                    # add ToolCall item
                    tc_output = _parse_content(tool_message["content"])
                    if tc_output is None:
                        raise InvalidCustomChatError(f"Tool message contains no content: {tool_message}")

                    tool_calls.append(ToolCall(name=tc_name, arguments=tc_arguments, output=tc_output))


            if remove_reasoning: reasoning_content = ""
            else: reasoning_content = message.get("reasoning_content", "")
            assistant_content = _parse_content(message.get("content", ""))

            # First assistant message contains reasoning and text
            items.append(AssistantMessage(
                reasoning=reasoning_content,
                text=assistant_content,
                tool_call=tool_calls[0] if len(tool_calls) > 0 else None,
            ))

            # Add assistant messages with extra tool calls
            # With our tokenization the model immediately sees tool output before calling next tool
            # which might not make sense for OpenAI format where model can call multiple tools at once
            # Therefore we disallow this by default
            if len(tool_calls) > 1:
                if not allow_multiple_tool_calls:
                    raise InvalidCustomChatError(f"Assistant message has more than one tool call: {[tc.name for tc in tool_calls]}")

                for tc in tool_calls[1:]:
                    items.append(AssistantMessage(tool_call=tc))


        elif message['role'] == "tool":
            continue # handled in assistant message

        else:
            raise InvalidCustomChatError(
                f"Unknown role {message['role']} in message:"
                f"{json.dumps(message, sort_keys=False, ensure_ascii=False, indent=4)}"
            )

    validate_chat(items)
    return items


def convert_from_sharegpt(chat: list[dict], system="system", user="human", assistant="gpt", role_key="from", content_key="value"):
    items: list[BaseItem] = []

    for message in chat:
        role = message[role_key]
        content = message[content_key]
        if role == system or role == user or role == assistant:
            items.append(UserMessage(content))
        else:
            raise InvalidCustomChatError(f"Unknown role: {role}")

    validate_chat(items)
    return items

def convert_openai_dataset(chats: list[dict], require_tc_id: bool, verbose: bool) -> list[list[BaseItem]]:
    samples = []

    for chat in chats:
        try:
            samples.append(convert_from_chat_completions_api(chat, require_tc_id=require_tc_id))
        except (InvalidCustomChatError, InvalidChatError) as e:
            if verbose: print(e)

    return samples

def convert_sharegpt_dataset(chats: list[list[dict]], system="system", user="human", assistant="gpt", role_key="from", content_key="value", verbose:bool=True) -> list[list[BaseItem]]:
    samples = []

    for chat in chats:
        try:
            samples.append(convert_from_sharegpt(chat, system=system, user=user, assistant=assistant, role_key=role_key, content_key=content_key))
        except (InvalidCustomChatError, InvalidChatError) as e:
            if verbose: print(e)

    return samples


def deduplicate(dataset: Sequence[Sequence[AnyItem]]) -> list[list[BaseItem]]:
    deduped = []
    deduped_jsons = set()

    for chat in dataset:
        chat = [to_item(i) for i in chat]

        # deduplicate should only remove duplicate samples even if they have different reasoning
        # but shoudn't remove versions of same sample with and without reasoning
        chat_copy = copy.deepcopy(chat)
        for item in chat_copy:
            if item.get("reasoning", False):
                item["reasoning"] = "__reasoning__"

        chat_json = json.dumps(chat_copy, ensure_ascii=False,sort_keys=True)
        if chat_json in deduped_jsons: continue
        deduped_jsons.add(chat_json)

        deduped.append(chat)

    return deduped

def to_dict(x: Any):
    return json.loads(json.dumps(x,sort_keys=False,ensure_ascii=False))

def strip_reasoning(item: AnyItem) -> BaseItem:
    item = to_item(copy.deepcopy(item))
    if "reasoning" in item: item["reasoning"] = ""
    if "tool_calls" in item:
        for tc in item["tool_calls"]:
            tc["reasoning"] = ""
    return item
