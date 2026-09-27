import json
from pathlib import Path
from .. import chat_api

XLAM_PATH = Path(__file__).resolve().parent.parent.parent / "notebooks" / "datasets" / "downloaded" / "xlam_function_calling_60k.json"

_TYPE_MAP = {
    "str": "string", "string": "string",
    "int": "integer", "integer": "integer",
    "float": "number", "number": "number",
    "bool": "boolean", "boolean": "boolean",
    "list": "array", "set": "array",
    "dict": "object",
}

def _map_type(raw: str) -> str:
    raw = raw.strip().lower().split(",")[0].split("=")[0].strip()
    if any(raw.startswith(p) for p in ("list", "tuple", "set")):
        return "array"
    if raw.startswith(("dict", "map")):
        return "object"
    if raw.startswith(("callable", "union")):
        return "string"
    return _TYPE_MAP.get(raw, "string")

def _convert_params(xlam_params: dict) -> dict:
    properties = {}
    required = []
    for pname, pdef in xlam_params.items():
        if not isinstance(pdef, dict):
            continue
        prop = {
            "type": _map_type(pdef.get("type", "str")),
            "description": pdef.get("description", ""),
        }
        if "default" in pdef:
            prop["default"] = pdef["default"]
        if "enum" in pdef:
            prop["enum"] = pdef["enum"]
        properties[pname] = prop
        if "default" not in pdef:
            required.append(pname)
    schema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema

def load(verbose: bool = False) -> list[list[chat_api.BaseItem]]:
    with open(str(XLAM_PATH),'r',encoding='utf-8') as f:
        data = json.load(f)

    samples = []
    skipped = 0

    for entry in data:
        try:
            tools = json.loads(entry["tools"])
            answers = json.loads(entry["answers"])
            query = entry["query"]

            items: list[chat_api.BaseItem] = []

            for t in tools:
                items.append(chat_api.ToolDefinition(
                    name=t["name"],
                    description=t.get("description", ""),
                    parameters=_convert_params(t.get("parameters", {})),
                ))

            items.append(chat_api.UserMessage(text=query))

            tool_calls = []
            for a in answers:
                args = a.get("arguments", {})
                if not isinstance(args, dict):
                    args = {}
                tool_calls.append(chat_api.ToolCall(
                    name=a["name"],
                    arguments=args if args else {"_": ""},
                    output=None,
                ))

            items.extend(chat_api.AssistantMessage(tool_call=tc) for tc in tool_calls)
            samples.append(items)

        except Exception as e:
            if verbose:
                eid = entry.get("id", "?")
                print(f"Skipping entry {eid}: {e}")
            skipped += 1

    if verbose and skipped:
        print(f"Skipped {skipped} / {len(data)} entries")

    samples = [s for s in samples if len(s[-1]["tool_calls"]) == 1]
    valid_samples = []
    for s in samples:
        try:
            chat_api.validate_chat(s)
            valid_samples.append(s)
        except Exception as e:
            if verbose:
                print(e)

    return valid_samples
