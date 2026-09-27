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
_tab = " "*2
_vline = "-"*8

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
        reasoning: reasoning before calling this tool.
        trainable: Whether to include this tool call in loss calculation.
    """
    def __init__(self, name:str, arguments: str | dict[str, Any], output: str | None = None, reasoning: str | None = "", trainable: bool = True):
        if reasoning is None: reasoning = ""
        if isinstance(arguments, str): arguments = json.loads(arguments, strict=False)
        super().__init__(type="tool_call", name=name, arguments=arguments, output=output, reasoning=reasoning, trainable=trainable)

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

    @property
    def reasoning(self) -> str: return self["reasoning"]
    @reasoning.setter
    def reasoning(self, value: str) -> None: self["reasoning"] = value

    @classmethod
    def from_dict(cls, d):
        return cls(
            name = d["name"],
            arguments = d["arguments"],
            output = d.get("output", None),
            reasoning = d.get("reasoning", None),
            trainable = d.get("trainable", True),
        )

    def tokenize(self, tokenizer):

        # parse reasoning
        # NOTE: reasoning start/end tokens are added by AssistantMessage
        if self.reasoning:
            reasoning_tokens = tokenizer.encode_text(self.reasoning)
            reasoning_mask = [int(self.trainable)] * len(reasoning_tokens)
        else:
            reasoning_tokens = []
            reasoning_mask = []

        # parse inputs
        name = tokenizer.encode_text(self.name)
        arguments = tokenizer.encode_text(json.dumps(self.arguments, ensure_ascii=False, sort_keys=False))

        input_tokens = (
            [tokenizer.tool_call_idx] + name
            + [tokenizer.tool_call_idx] + arguments
            + [tokenizer.end_idx]
        )
        input_mask = [int(self.trainable)] * len(input_tokens)

        # parse outputs
        if self.output is not None:
            output_tokens = tokenizer.encode_text(self.output) + [tokenizer.end_idx]
            output_mask = [0] * len(output_tokens)
        else:
            output_tokens = []
            output_mask = []

        # merge
        return TokensAndMask(
            tokens = reasoning_tokens + input_tokens + output_tokens,
            mask = reasoning_mask + input_mask + output_mask,
        )

class AssistantMessage(BaseTrainableItem):
    """An assistant message optionally preceded by tool calls and reasoning.

    Args:
        text: final conversational text of this message.
        reasoning: final reasoning after tool calls and before the final conversational message.
        tool_calls: tool calls. Defaults to None.
        trainable: Whether to include this assistant message and reasoning in loss calculation.

    Example (think):
    ```python
    AssistantMessage(
        tool_calls=[
            ToolCall(reasoning="I need to list the directory.", name="list_dir", arguments="{}", output=...),
            ToolCall(reasoning="I see the notes.txt file, now I will read it.", name="read_file", arguments="...", output=...),
        ],
        reasoning="I've red the notes, now I will present this information to the user.",
        text="..."
    )
    ```

    Example (instruct):
    ```python
    AssistantMessage(
        tool_calls=[
            ToolCall(name="list_dir", arguments="{}", output=...),
            ToolCall(name="read_file", arguments="...", output=...),
        ],
        text="..."
    )
    ```
    """

    def __init__(
        self,
        text: str,
        reasoning: str | None = "",
        tool_calls: Sequence[ToolCall] | None = None,
        trainable: bool = True,
    ):
        if reasoning is None: reasoning = ""

        # convert to ToolCallSets
        if tool_calls is None: tool_calls = []
        super().__init__(type="assistant", text=text, reasoning=reasoning, tool_calls=list(tool_calls), trainable=trainable)

    @property
    def text(self) -> str: return self["text"]
    @text.setter
    def text(self, value: str) -> None: self["text"] = value

    @property
    def reasoning(self) -> str: return self["reasoning"]
    @reasoning.setter
    def reasoning(self, value: str) -> None: self["reasoning"] = value

    @property
    def tool_calls(self) -> list[ToolCall]: return self["tool_calls"]
    @tool_calls.setter
    def tool_calls(self, value: Sequence[ToolCall]) -> None: self["tool_calls"] = list(value)

    @classmethod
    def from_dict(cls, d):
        tool_calls = d.get("tool_calls", None)
        if tool_calls:
            tool_calls = [ToolCall.from_dict(tc) for tc in tool_calls]

        return cls(text=d["text"], reasoning=d.get("reasoning", None), tool_calls=tool_calls, trainable=d.get("trainable", True))

    def tokenize(self, tokenizer):
        trainable = int(self.trainable)

        # tokenize text
        if self.text:
            final_tokens = tokenizer.encode_text(self.text) + [tokenizer.end_idx]
            final_mask = [trainable] * len(final_tokens)
        else:
            final_tokens = []
            final_mask = []

        # tokenize tool calls
        tools_tokens = []
        tools_mask = []
        tool_calls_ended = True
        for i, tc in enumerate(self.tool_calls):
            tc_tokens, tc_mask = tc.tokenize(tokenizer)
            tools_tokens.extend(tc_tokens)
            tools_mask.extend(tc_mask)
            if tc.output is None:
                if i != len(self.tool_calls) - 1:
                    raise InvalidChatError("Only last tool call on last assistant message can have no output attribute.")
                tool_calls_ended = False # tools_tokens doesn't end with <END><TOOL_CALL> tokens

        if not tool_calls_ended:
            if self.text or self.reasoning:
                raise InvalidChatError("Last tool call has no tool output, but the assistant message has text or reasoning.")

        # we tokenize differently in think and instruct modes
        # in think mode, tool calls happen within think block
        if bool(self.reasoning):
            reasoning_tokens = tokenizer.encode_text(self.reasoning)
            reasoning_mask = [trainable] * len(reasoning_tokens)

            tokens = [tokenizer.assistant_idx, tokenizer.think_idx] + tools_tokens + reasoning_tokens
            mask = [0, 0] + tools_mask + reasoning_mask

            if tool_calls_ended:
                tokens.append(tokenizer.think_idx)
                mask.append(trainable)

                tokens.extend(final_tokens)
                mask.extend(final_mask)

            return TokensAndMask(tokens=tokens, mask=mask)

        # instruct mode
        return TokensAndMask(
            tokens = [tokenizer.assistant_idx] + tools_tokens + final_tokens,
            mask = [0] + tools_mask + final_mask,
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
    - either all AssistantMessages and ToolCalls should have reasoning (think mode), or none should (instruct mode)
    - All tool calls should have tool outputs
    - Last item should be trainable (if last item is UserMessage, it contributes nothing to the loss and just increases train time)

    Special case:
    - A sample can end with a pending tool call (no output) or on a finished tool call without the final conversational message. End tokens are not added during tokenization, therefore this message and tool call must be last.
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
                else: raise InvalidChatError(f"The first item after ToolDefinition must be UserMessage, but got {type(item)}.")
            is_tool_defs = False

    # check duplicate tool names
    available_tools = [item.name for item in items if isinstance(item, ToolDefinition)]
    if len(available_tools) != len(set(available_tools)):
        raise InvalidChatError(f"There are duplicate tools: {available_tools}")

    # check no assistant messages in a row
    for i, (item1, item2) in enumerate(itertools.pairwise(items)):
        if isinstance(item1, AssistantMessage) and isinstance(item2, AssistantMessage):
            raise InvalidChatError(f"There are two assistant messages in a row at indexes {i}, {i+1}.")

    # check reasoning
    is_think = None
    for item in items:
        if isinstance(item, AssistantMessage):
            is_think = bool(item.reasoning)
            break

    if is_think is None:
        raise InvalidChatError(f"The chat contains no assistant messages: {[type(i) for i in items]}.")

    for i_item, item in enumerate(items):
        is_last_message = (i_item == len(items) - 1)

        if isinstance(item, AssistantMessage):

            # NOTE: for training we allow last assistant message to only contain tool calls with no outputs
            # or tool calls but no assistant message, in that case it is tokenized with no end tokens.

            if is_last_message and is_think:
                if item.text and not item.reasoning:
                    raise InvalidChatError("First assistant message has reasoning, but last assistant message "
                                           "has a conversational output without reasoning.")

            else:
                if bool(item.reasoning) != is_think:
                    raise InvalidChatError("Either all items should have reasoning, or none should, "
                                           "but got assistant messages with and without reasoning.")

            if len(item.tool_calls) > 0 and item.tool_calls[-1].output is None:
                if item.text or item.reasoning:
                    raise InvalidChatError("Last tool call in assistant message is pending (has no output), "
                                           "but the assistant message has text or reasoning.")

            for i_tc, tc in enumerate(item.tool_calls):
                is_last_tc = i_tc == len(item.tool_calls) - 1

                # check that tool is defined
                if tc.name not in available_tools:
                    raise InvalidChatError(
                        f"ToolCall has name={tc.name}, but no tools with that name are defined. Defined tools: {available_tools}")

                # check that all tool calls contain tool outputs, unless its the last message
                if tc.output is None:
                    if is_last_message:
                        if not is_last_tc:
                            # on last message, only last tool call can have no output
                            raise InvalidChatError(f"Non-last ToolCall {i_tc} on last message for tool "
                                                   f"`{tc.name}` has no `output` attribute set.")

                    else:
                        raise InvalidChatError(f"Tool call {i_tc} for tool `{tc.name}` has no `output` attribute set.")

                if bool(tc.reasoning) != is_think and not (is_last_message and is_last_tc):
                    raise InvalidChatError("Either all assistant messages and tool calls should have reasoning, or none should, "
                                           f"but ToolCall {i_tc} for tool `{tc.name}` doesn't match.")


                # check empty strings
                if len(tc.name) == 0 or len(tc.arguments) == 0 or (tc.output is not None and len(tc.output) == 0):
                    raise InvalidChatError(
                        f"ToolCall {i_tc} for tool `{tc.name}` has an empty string in of `name`, `arguments` or `output`.")


    # check that last item is trainable
    if not items[-1].get('trainable', False):
        raise InvalidChatError(f"Last item in the chat is not trainable: {type(items[-1])}.")

    # check that there are any trainable items
    for item in items:
        if item.get("trainable", False):
            break
    else:
        raise InvalidChatError(f"All items have `trainable` set to False: {[type(i) for i in items]}.")

    # check that messages are not empty
    for i, item in enumerate(items):
        if isinstance(item, (AssistantMessage, UserMessage)):
            if len(item.text.strip()) == 0:
                if i != len(items) - 1: # last assistant message can have empty text
                    raise InvalidChatError(f"Item contains empty text: {item.to_dict()}")

        if isinstance(item, ToolDefinition):
            if len(item.name) == 0 or len(item.description) == 0:
                raise InvalidChatError(f"ToolDefinition contains empty name or description: {item.to_dict()}")

    # TODO check tokenization
    # we need to implement a detokenizer to Items for this first

class InvalidOpenAIChatError(Exception): pass

def _parse_content(content: str | list | None | Any):
    if content is None:
        return None

    if isinstance(content, list):
        if any('text' not in el for el in content):
            raise InvalidOpenAIChatError("User message contains non-text content.")
        content = '\n'.join(el['text'] for el in content).strip()

    if not isinstance(content, str):
        raise InvalidOpenAIChatError(f"Content is not a string or a list, but {type(content)}:\n{content}")

    if len(content.strip()) == 0:
        return None

    return content.strip()

def convert_from_chat_completions_api(chat: dict, require_tc_id: bool = True, strip_reasoning: bool = False) -> list[BaseItem]:
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
    tcs_to_add: list[ToolCall] = []

    for i, message in enumerate(chat["messages"]):
        if isinstance(message, str): message = json.loads(message.strip(), strict=False)

        # we only have user
        if message["role"] in ("user", "developer", "system"):
            if len(tcs_to_add) != 0:
                raise InvalidOpenAIChatError("Chat contains assistant message with tool calls but no conversational text.")

            user_content = _parse_content(message["content"])

            if user_content is None:
                raise InvalidOpenAIChatError("User message contains no content")

            items.append(UserMessage(user_content.strip()))

        elif message["role"] == "assistant":
            if len(items) == 0:
                raise InvalidOpenAIChatError(
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

                    # Add tool call item first
                    tc_name = tc["function"]["name"]
                    tc_arguments = tc["function"]["arguments"]
                    if not isinstance(tc_arguments, str):
                        tc_arguments = json.dumps(tc_arguments, ensure_ascii=False, sort_keys=False)

                    # Now add tool output immediately after the tool call
                    # we either have an ID, or have to select by function name
                    if tc_id is None:
                        if require_tc_id:
                            raise InvalidOpenAIChatError(
                                f"Tool call id (key 'id') missing:\n"
                                f"{json.dumps(message, sort_keys=False, ensure_ascii=False, indent=4)}\n"
                            )


                    # check that tool call name exists
                    if tc_name not in defined_tools:
                        raise InvalidOpenAIChatError(
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
                        raise InvalidOpenAIChatError(
                            f"There are no tool messages after tool call:\n"
                            f"{json.dumps(chat['messages'], sort_keys=False, ensure_ascii=False, indent=4)}"
                        )

                    if tc_id is None:

                        # get tool by name, but make sure tool call with that name is unique
                        # to avoid ambiguity
                        tool_names = [tm["name"] for tm in tool_messages]
                        if tc_name not in tool_names:
                            raise InvalidOpenAIChatError(
                                f"Tool call has no id and has name {tc_name}, and "
                                f"there is no tool message with that name, found names: {tool_names}\n"
                                f"{json.dumps(message, sort_keys=False, ensure_ascii=False, indent=4)}"
                            )

                        if tool_names.count(tc_name) > 1:
                            raise InvalidOpenAIChatError(
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
                            raise InvalidOpenAIChatError(
                                f"Tool call id is {tc_id}, but there is no tool message with that id."
                                f"Seen ids: {seen_ids}"
                            )

                    # add ToolCall item
                    tc_output = _parse_content(tool_message["content"])
                    if tc_output is None:
                        raise InvalidOpenAIChatError(f"Tool message contains no content: {tool_message}")

                    tool_calls.append(ToolCall(name=tc_name, arguments=tc_arguments, output=tc_output))


            # if there are no tool calls, reasoning is for the assistant message;
            # otherwise reasoning is for the tool calls
            if strip_reasoning: reasoning_content = ""
            else: reasoning_content = message.get("reasoning_content", "")
            assistant_content = _parse_content(message.get("content", ""))

            if len(tool_calls) == 0:
                if assistant_content is None:
                    raise InvalidOpenAIChatError(f"Assistant message contains no content or tool calls: {message}")

                if isinstance(items[-1], AssistantMessage):
                    # this happens when model calls tools and outputs conversational messages after each tool call
                    # since we call tools within reasoning block, we can't use that for training
                    raise InvalidOpenAIChatError("Got two assistant messages with content in a row.")

                assistant_message = AssistantMessage(
                    text=assistant_content,
                    reasoning=reasoning_content,
                    tool_calls=tcs_to_add.copy(),
                )
                items.append(assistant_message)
                tcs_to_add.clear()

            else:
                if not strip_reasoning:
                    tool_calls[0].reasoning = reasoning_content

                # in chat completions assistant message might contain no content, only tool calls
                # in which case we save it for later
                if assistant_content is None:
                    tcs_to_add.extend(tool_calls)

                else:
                    if isinstance(items[-1], AssistantMessage):
                        raise InvalidOpenAIChatError("Got two assistant messages with content in a row.")

                    assistant_message = AssistantMessage(text=assistant_content, tool_calls=tool_calls + tcs_to_add.copy())
                    items.append(assistant_message)
                    tcs_to_add.clear()


        elif message['role'] == "tool":
            continue # handled in assistant message

        else:
            raise InvalidOpenAIChatError(
                f"Unknown role {message['role']} in message:"
                f"{json.dumps(message, sort_keys=False, ensure_ascii=False, indent=4)}"
            )

    if tcs_to_add:
        # add pending tool call
        items.append(AssistantMessage(text="", reasoning="", tool_calls=tcs_to_add))

    validate_chat(items)
    return items

class InvalidShareGPTChatError(Exception): pass

def convert_from_sharegpt(chat: list[dict], system="system", user="human", assistant="gpt", role_key="from", content_key="value"):
    items: list[BaseItem] = []

    for message in chat:
        role = message[role_key]
        content = message[content_key]
        if role == system or role == user:
            items.append(UserMessage(content))
        elif role == assistant:
            items.append(UserMessage(content))
        else:
            raise InvalidShareGPTChatError(f"Unknown role: {role}")

    validate_chat(items)
    return items

def convert_openai_dataset(chats: list[dict], require_tc_id: bool, verbose: bool) -> list[list[BaseItem]]:
    samples = []

    for chat in chats:
        try:
            samples.append(convert_from_chat_completions_api(chat, require_tc_id=require_tc_id))
        except (InvalidOpenAIChatError, InvalidChatError) as e:
            if verbose: print(e)

    return samples

def convert_sharegpt_dataset(chats: list[list[dict]], system="system", user="human", assistant="gpt", role_key="from", content_key="value", verbose:bool=True) -> list[list[BaseItem]]:
    samples = []

    for chat in chats:
        try:
            samples.append(convert_from_sharegpt(chat, system=system, user=user, assistant=assistant, role_key=role_key, content_key=content_key))
        except (InvalidOpenAIChatError, InvalidChatError) as e:
            if verbose: print(e)

    return samples


def deduplicate(dataset: Sequence[Sequence[AnyItem]]) -> list[list[BaseItem]]:
    deduped = []
    deduped_jsons = set()

    for chat in dataset:
        chat = [to_item(i) for i in chat]

        # deduplicate should only differentiate reasoning vs no reasoning
        chat_copy = copy.deepcopy(chat)
        for item in chat_copy:
            if "reasoning" in item and item["reasoning"]:
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