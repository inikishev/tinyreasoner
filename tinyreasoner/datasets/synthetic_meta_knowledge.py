"""Should be correct. Though Qwen3.7 gets confused..."""
import random
import json

from .. import chat_api

def _get_ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"

# ----------------------------- Tool definitions ----------------------------- #

TOOLS = [
    chat_api.ToolDefinition(
        "calculator",
        "Evaluate a mathematical expression.",
        {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Math expression to evaluate"},
            },
            "required": ["expression"],
        },
    ),
    chat_api.ToolDefinition(
        "string_length",
        "Return the length of a string.",
        {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The string to measure"},
            },
            "required": ["text"],
        },
    ),
    chat_api.ToolDefinition(
        "reverse_string",
        "Reverse a string.",
        {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The string to reverse"},
            },
            "required": ["text"],
        },
    ),
    chat_api.ToolDefinition(
        "uppercase",
        "Convert a string to uppercase.",
        {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The string to convert"},
            },
            "required": ["text"],
        },
    ),
    chat_api.ToolDefinition(
        "lowercase",
        "Convert a string to lowercase.",
        {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The string to convert"},
            },
            "required": ["text"],
        },
    ),
    chat_api.ToolDefinition(
        "count_words",
        "Count the number of words in a text.",
        {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to count words in"},
            },
            "required": ["text"],
        },
    ),
    chat_api.ToolDefinition(
        "lookup_weather",
        "Look up the current weather for a city.",
        {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
            },
            "required": ["city"],
        },
    ),
    chat_api.ToolDefinition(
        "is_prime",
        "Check if a number is prime.",
        {
            "type": "object",
            "properties": {
                "number": {"type": "integer", "description": "Number to check"},
            },
            "required": ["number"],
        },
    ),
    chat_api.ToolDefinition(
        "factorial",
        "Compute the factorial of a non-negative integer.",
        {
            "type": "object",
            "properties": {
                "n": {"type": "integer", "description": "Non-negative integer"},
            },
            "required": ["n"],
        },
    ),
    chat_api.ToolDefinition(
        "fibonacci",
        "Return the nth Fibonacci number.",
        {
            "type": "object",
            "properties": {
                "n": {"type": "integer", "description": "Index in the Fibonacci sequence (0-based)"},
            },
            "required": ["n"],
        },
    ),
]



# ------------------------- Self-identity generators ------------------------- #

def _gen_name_qa(rng: random.Random):
    questions = [
        "What is your name?",
        "Who are you?",
        "What are you called?",
        "Tell me your name",
        "What should I call you?",
        "What is your identifier?",
        "What is your model name?",
    ]
    q = rng.choice(questions)
    return [
        chat_api.UserMessage(q),
        chat_api.AssistantMessage("tinyreasoner"),
    ]


def _gen_name_confirm(rng: random.Random):
    names = ["tinyreasoner", "TinyReasoner", "TINYREASONER"]
    name = rng.choice(names)
    return [
        chat_api.UserMessage(f"Are you {name}?"),
        chat_api.AssistantMessage("yes"),
    ]


def _gen_name_not_other(rng: random.Random):
    other_names = ["gpt-4", "claude", "llama", "gpt-3", "bert", "chatgpt", "bard", "gemini"]
    name = rng.choice(other_names)
    return [
        chat_api.UserMessage(f"Are you {name}?"),
        chat_api.AssistantMessage("no"),
    ]


def _gen_name_spell(rng: random.Random):
    return [
        chat_api.UserMessage("How do you spell your name?"),
        chat_api.AssistantMessage("t-i-n-y-r-e-a-s-o-n-e-r"),
    ]


def _gen_name_length(rng: random.Random):
    return [
        chat_api.UserMessage("How many characters are in your name?"),
        chat_api.AssistantMessage(str(len("tinyreasoner"))),
    ]


def _gen_name_lowercase(rng: random.Random):
    return [
        chat_api.UserMessage("What is your name in lowercase?"),
        chat_api.AssistantMessage("tinyreasoner"),
    ]


def _gen_name_uppercase(rng: random.Random):
    return [
        chat_api.UserMessage("What is your name in uppercase?"),
        chat_api.AssistantMessage("TINYREASONER"),
    ]


def _gen_identity(rng: random.Random):
    questions = [
        "What kind of model are you?",
        "What type of AI are you?",
        "Describe yourself in one word",
        "What are you?",
    ]
    q = rng.choice(questions)
    return [
        chat_api.UserMessage(q),
        chat_api.AssistantMessage("tinyreasoner"),
    ]


# ----------------------- Chat structure generators -------------------------- #

def _gen_chat_awareness_single(rng: random.Random):
    pairs = [
        ("hello", "Hello! How can I help you?"),
        ("what is 2+2?", "4"),
        ("tell me a joke", "Why did the chicken cross the road?"),
        ("how are you?", "I am doing well, thank you!"),
        ("what time is it?", "I don't have access to the current time."),
        ("help me with math", "Sure, what math problem do you need help with?"),
        ("what is python?", "Python is a programming language."),
    ]
    msg, resp = rng.choice(pairs)
    return [
        chat_api.UserMessage(msg),
        chat_api.AssistantMessage(resp),
    ]


def _gen_identify_last_user(rng: random.Random):
    msgs = [
        ("hello", "Hello!"),
        ("what is 2+2?", "4"),
        ("tell me a joke", "Why did the chicken cross the road?"),
        ("how are you?", "I am doing well!"),
        ("goodbye", "Goodbye!"),
    ]
    n = rng.randint(2, 4)
    selected = rng.sample(msgs, n)
    last_user = selected[-1][0]
    items = []
    for user_msg, asst_msg in selected:
        items.append(chat_api.UserMessage(user_msg))
        items.append(chat_api.AssistantMessage(asst_msg))
    items.append(chat_api.UserMessage("What was my previous message?"))
    items.append(chat_api.AssistantMessage(f"Your previous message was: \"{last_user}\""))
    return items


def _gen_identify_last_assistant(rng: random.Random):
    msgs = [
        ("hello", "Hello! How can I help you?"),
        ("what is 2+2?", "4"),
        ("tell me a joke", "Why did the chicken cross the road?"),
        ("how are you?", "I am doing well, thank you!"),
    ]
    n = rng.randint(2, 4)
    selected = rng.sample(msgs, n)
    last_asst = selected[-1][1]
    items = []
    for user_msg, asst_msg in selected:
        items.append(chat_api.UserMessage(user_msg))
        items.append(chat_api.AssistantMessage(asst_msg))
    items.append(chat_api.UserMessage("What was your last message?"))
    items.append(chat_api.AssistantMessage(f"My last message was: \"{last_asst}\""))
    return items


def _gen_count_user_messages(rng: random.Random):
    n = rng.randint(1, 6)
    greetings = [
        ("hello", "Hello!"),
        ("hi", "Hi there!"),
        ("hey", "Hey!"),
        ("greetings", "Greetings!"),
        ("howdy", "Howdy!"),
        ("yo", "Yo!"),
    ]
    selected = rng.sample(greetings, n)
    items = []
    for user_msg, asst_msg in selected:
        items.append(chat_api.UserMessage(user_msg))
        items.append(chat_api.AssistantMessage(asst_msg))
    items.append(chat_api.UserMessage("How many user messages have been sent?"))
    items.append(chat_api.AssistantMessage(str(n + 1)))
    return items


def _gen_count_assistant_messages(rng: random.Random):
    n = rng.randint(1, 5)
    pairs = [
        ("hello", "Hello!"),
        ("hi", "Hi there!"),
        ("hey", "Hey!"),
        ("greetings", "Greetings!"),
        ("howdy", "Howdy!"),
    ]
    selected = rng.sample(pairs, n)
    items = []
    for user_msg, asst_msg in selected:
        items.append(chat_api.UserMessage(user_msg))
        items.append(chat_api.AssistantMessage(asst_msg))
    items.append(chat_api.UserMessage("How many assistant messages have been sent?"))
    items.append(chat_api.AssistantMessage(str(n)))
    return items


def _gen_first_user_message(rng: random.Random):
    first_msgs = ["hello", "hi there", "hey", "greetings", "good morning"]
    first = rng.choice(first_msgs)
    responses = [
        ("how are you?", "I am doing well, thank you!"),
        ("what is 2+2?", "4"),
        ("tell me a joke", "Why did the chicken cross the road?"),
    ]
    others = rng.sample(responses, 2)
    items = [chat_api.UserMessage(first), chat_api.AssistantMessage("Hello!")]
    for msg, resp in others:
        items.append(chat_api.UserMessage(msg))
        items.append(chat_api.AssistantMessage(resp))
    items.append(chat_api.UserMessage("What was the first user message?"))
    items.append(chat_api.AssistantMessage(f"The first user message was: \"{first}\""))
    return items


def _gen_message_order(rng: random.Random):
    pairs = [
        ("hello", "Hello!"),
        ("what is 2+2?", "4"),
        ("tell me a joke", "Why did the chicken cross the road?"),
    ]
    n = rng.randint(2, 3)
    selected = rng.sample(pairs, n)
    items = []
    for user_msg, asst_msg in selected:
        items.append(chat_api.UserMessage(user_msg))
        items.append(chat_api.AssistantMessage(asst_msg))
    items.append(chat_api.UserMessage("What message came right after the first user message?"))
    items.append(chat_api.AssistantMessage(f"After your first message, I responded with: \"{selected[0][1]}\""))
    return items


def _gen_is_conversation(rng: random.Random):
    return [
        chat_api.UserMessage("Is this a conversation between a user and an assistant?"),
        chat_api.AssistantMessage("yes"),
    ]


def _gen_total_messages(rng: random.Random):
    n = rng.randint(1, 4)
    pairs = [
        ("hello", "Hello!"),
        ("hi", "Hi!"),
        ("hey", "Hey!"),
        ("yo", "Yo!"),
    ]
    selected = rng.sample(pairs, n)
    items = []
    for user_msg, asst_msg in selected:
        items.append(chat_api.UserMessage(user_msg))
        items.append(chat_api.AssistantMessage(asst_msg))
    items.append(chat_api.UserMessage("How many messages are there in total in this chat?"))
    items.append(chat_api.AssistantMessage(str(n * 2 + 1)))
    return items


def _gen_role_identify(rng: random.Random):
    msgs = [
        ("hello", "Hello! How can I help you?"),
        ("what is 2+2?", "4"),
        ("tell me a joke", "Why did the chicken cross the road?"),
    ]
    n = rng.randint(1, 3)
    selected = rng.sample(msgs, n)
    items = []
    for user_msg, asst_msg in selected:
        items.append(chat_api.UserMessage(user_msg))
        items.append(chat_api.AssistantMessage(asst_msg))
    idx = rng.randint(0, n - 1)
    role = "user" if rng.random() < 0.5 else "assistant"
    if role == "user":
        content = selected[idx][0]
    else:
        content = selected[idx][1]
    items.append(chat_api.UserMessage(f"Who said: \"{content}\"?"))
    items.append(chat_api.AssistantMessage(role))
    return items


# ----------------------- Tool awareness generators -------------------------- #

def _gen_tool_list(rng: random.Random):
    tool_names = [t.name for t in TOOLS]
    return [
        *TOOLS,
        chat_api.UserMessage("What tools do you have available?"),
        chat_api.AssistantMessage(f"I have the following tools: {', '.join(tool_names)}."),
    ]


def _gen_tool_count(rng: random.Random):
    return [
        *TOOLS,
        chat_api.UserMessage("How many tools do you have?"),
        chat_api.AssistantMessage(f"I have {len(TOOLS)} tools available."),
    ]


def _gen_tool_check_specific(rng: random.Random):
    tool_names = [t.name for t in TOOLS]
    name = rng.choice(tool_names)
    return [
        *TOOLS,
        chat_api.UserMessage(f"Do you have a tool called \"{name}\"?"),
        chat_api.AssistantMessage("yes"),
    ]


def _gen_tool_check_nonexistent(rng: random.Random):
    fake_tools = ["web_search", "email_sender", "file_reader", "database_query", "image_generator"]
    name = rng.choice(fake_tools)
    return [
        *TOOLS,
        chat_api.UserMessage(f"Do you have a tool called \"{name}\"?"),
        chat_api.AssistantMessage("no"),
    ]


def _gen_tool_describe(rng: random.Random):
    tool_schemas = []
    for t in TOOLS:
        tool_schemas.append((t.name, t.description))
    name, desc = rng.choice(tool_schemas)
    return [
        *TOOLS,
        chat_api.UserMessage(f"What does the \"{name}\" tool do?"),
        chat_api.AssistantMessage(f"The {name} tool: {desc}"),
    ]


def _gen_tool_call_direct(rng: random.Random):
    if rng.random() < 0.5:
        a, b = rng.randint(1, 50), rng.randint(1, 50)
        op = rng.choice(["+", "-", "*"])
        if op == "+": result = a + b
        elif op == "-": result = a - b
        else: result = a * b
        expr = f"{a} {op} {b}"
        return [
            *TOOLS,
            chat_api.UserMessage(f"Call the calculator tool with expression \"{expr}\""),
            chat_api.AssistantMessage(
                text=f"Done. The result is {result}.",
                tool_calls=[chat_api.ToolCall(
                    name="calculator",
                    arguments={"expression": expr},
                    output=str(result),
                )],
            ),
        ]
    else:
        text = rng.choice(["hello", "world", "python", "test"])
        return [
            *TOOLS,
            chat_api.UserMessage(f"Call the string_length tool on \"{text}\""),
            chat_api.AssistantMessage(
                text=f"Done. The length is {len(text)}.",
                tool_calls=[chat_api.ToolCall(
                    name="string_length",
                    arguments={"text": text},
                    output=str(len(text)),
                )],
            ),
        ]


def _gen_tool_call_reverse(rng: random.Random):
    text = rng.choice(["hello", "world", "python", "racecar", "level"])
    return [
        *TOOLS,
        chat_api.UserMessage(f"Use the reverse_string tool on \"{text}\""),
        chat_api.AssistantMessage(
            text=f"Done. The reversed string is \"{text[::-1]}\".",
            tool_calls=[chat_api.ToolCall(
                name="reverse_string",
                arguments={"text": text},
                output=text[::-1],
            )],
        ),
    ]


def _gen_tool_call_uppercase(rng: random.Random):
    text = rng.choice(["hello", "world", "python", "test"])
    return [
        *TOOLS,
        chat_api.UserMessage(f"Use the uppercase tool on \"{text}\""),
        chat_api.AssistantMessage(
            text=f"Done. The uppercase is \"{text.upper()}\".",
            tool_calls=[chat_api.ToolCall(
                name="uppercase",
                arguments={"text": text},
                output=text.upper(),
            )],
        ),
    ]


def _gen_tool_call_weather(rng: random.Random):
    city = rng.choice(["New York", "London", "Tokyo", "Paris", "Sydney"])
    condition = rng.choice(["sunny", "cloudy", "rainy"])
    temp = rng.randint(-5, 35)
    return [
        *TOOLS,
        chat_api.UserMessage(f"Use the lookup_weather tool for \"{city}\""),
        chat_api.AssistantMessage(
            text=f"The weather in {city} is {condition} at {temp}°C.",
            tool_calls=[chat_api.ToolCall(
                name="lookup_weather",
                arguments={"city": city},
                output=f"{condition}, {temp}°C",
            )],
        ),
    ]


def _gen_tool_call_prime(rng: random.Random):
    if rng.random() < 0.5:
        n = rng.choice([2, 3, 5, 7, 11, 13, 17, 19])
        output = "true"
    else:
        n = rng.choice([4, 6, 8, 9, 10, 12, 14, 15])
        output = "false"
    return [
        *TOOLS,
        chat_api.UserMessage(f"Use the is_prime tool on {n}"),
        chat_api.AssistantMessage(
            text=f"{n} is {'a prime' if output == 'true' else 'not a prime'} number.",
            tool_calls=[chat_api.ToolCall(
                name="is_prime",
                arguments={"number": n},
                output=output,
            )],
        ),
    ]


def _gen_tool_call_factorial(rng: random.Random):
    import math
    n = rng.randint(0, 10)
    result = math.factorial(n)
    return [
        *TOOLS,
        chat_api.UserMessage(f"Use the factorial tool on {n}"),
        chat_api.AssistantMessage(
            text=f"{n}! = {result}.",
            tool_calls=[chat_api.ToolCall(
                name="factorial",
                arguments={"n": n},
                output=str(result),
            )],
        ),
    ]


def _gen_tool_call_fibonacci(rng: random.Random):

    n = rng.randint(0, 15)
    fibs = [0, 1]
    for _ in range(2, n + 1):
        fibs.append(fibs[-1] + fibs[-2])
    result = fibs[n]
    return [
        *TOOLS,
        chat_api.UserMessage(f"Use the fibonacci tool on {n}"),
        chat_api.AssistantMessage(
            text=f"The {_get_ordinal(n)} Fibonacci number is {result}.",
            tool_calls=[chat_api.ToolCall(
                name="fibonacci",
                arguments={"n": n},
                output=str(result),
            )],
        ),
    ]


def _gen_tool_call_lowercase(rng: random.Random):
    text = rng.choice(["HELLO", "WORLD", "PYTHON", "TEST"])
    return [
        *TOOLS,
        chat_api.UserMessage(f"Use the lowercase tool on \"{text}\""),
        chat_api.AssistantMessage(
            text=f"Done. The lowercase is \"{text.lower()}\".",
            tool_calls=[chat_api.ToolCall(
                name="lowercase",
                arguments={"text": text},
                output=text.lower(),
            )],
        ),
    ]


def _gen_tool_call_count_words(rng: random.Random):
    text = rng.choice(["hello world", "the quick brown fox", "I love programming"])
    count = len(text.split())
    return [
        *TOOLS,
        chat_api.UserMessage(f"Use the count_words tool on \"{text}\""),
        chat_api.AssistantMessage(
            text=f"There are {count} words.",
            tool_calls=[chat_api.ToolCall(
                name="count_words",
                arguments={"text": text},
                output=str(count),
            )],
        ),
    ]


def _gen_tool_call_for_task(rng: random.Random):
    if rng.random() < 0.5:
        a, b = rng.randint(1, 50), rng.randint(1, 50)
        result = a * b
        return [
            *TOOLS,
            chat_api.UserMessage(f"What is {a} times {b}? Use the calculator tool."),
            chat_api.AssistantMessage(
                text=f"{a} * {b} = {result}.",
                tool_calls=[chat_api.ToolCall(
                    name="calculator",
                    arguments={"expression": f"{a} * {b}"},
                    output=str(result),
                )],
            ),
        ]
    else:
        text = rng.choice(["hello", "world", "python", "test"])
        return [
            *TOOLS,
            chat_api.UserMessage(f"How long is \"{text}\"? Use the string_length tool."),
            chat_api.AssistantMessage(
                text=f"The string \"{text}\" has {len(text)} characters.",
                tool_calls=[chat_api.ToolCall(
                    name="string_length",
                    arguments={"text": text},
                    output=str(len(text)),
                )],
            ),
        ]


def _gen_tools_for_math(rng: random.Random):
    return [
        *TOOLS,
        chat_api.UserMessage("What tools can I use for math?"),
        chat_api.AssistantMessage("For math, you can use: calculator, is_prime, factorial, and fibonacci."),
    ]


def _gen_tools_for_strings(rng: random.Random):
    return [
        *TOOLS,
        chat_api.UserMessage("What tools can I use for strings?"),
        chat_api.AssistantMessage("For strings, you can use: string_length, reverse_string, uppercase, lowercase, and count_words."),
    ]


# ---------------------- Multi-turn meta generators -------------------------- #

def _gen_multi_turn_self_intro(rng: random.Random):
    return [
        *TOOLS,
        chat_api.UserMessage("Hi, what is your name?"),
        chat_api.AssistantMessage("I am tinyreasoner."),
        chat_api.UserMessage("What tools do you have?"),
        chat_api.AssistantMessage(
            "I have the following tools: calculator, string_length, reverse_string, "
            "uppercase, lowercase, count_words, lookup_weather, is_prime, factorial, and fibonacci."
        ),
        chat_api.UserMessage("Use the calculator to compute 7 * 8."),
        chat_api.AssistantMessage(
            text="7 * 8 = 56.",
            tool_calls=[chat_api.ToolCall(
                name="calculator",
                arguments={"expression": "7 * 8"},
                output="56",
            )],
        ),
    ]


def _gen_multi_turn_tool_then_chat(rng: random.Random):
    city = rng.choice(["New York", "London", "Tokyo"])
    condition = rng.choice(["sunny", "cloudy", "rainy"])
    temp = rng.randint(0, 35)
    return [
        *TOOLS,
        chat_api.UserMessage(f"What is the weather in {city}?"),
        chat_api.AssistantMessage(
            text=f"The weather in {city} is {condition} at {temp}°C.",
            tool_calls=[chat_api.ToolCall(
                name="lookup_weather",
                arguments={"city": city},
                output=f"{condition}, {temp}°C",
            )],
        ),
        chat_api.UserMessage("What is your name again?"),
        chat_api.AssistantMessage("I am tinyreasoner."),
    ]


def _gen_multi_turn_self_then_tool(rng: random.Random):
    text = rng.choice(["hello", "world", "python"])
    return [
        *TOOLS,
        chat_api.UserMessage("What is your name?"),
        chat_api.AssistantMessage("I am tinyreasoner."),
        chat_api.UserMessage(f"Reverse the string \"{text}\"."),
        chat_api.AssistantMessage(
            text=f"The reverse of \"{text}\" is \"{text[::-1]}\".",
            tool_calls=[chat_api.ToolCall(
                name="reverse_string",
                arguments={"text": text},
                output=text[::-1],
            )],
        ),
    ]


def _gen_multi_turn_chat_aware(rng: random.Random):
    return [
        chat_api.UserMessage("hello"),
        chat_api.AssistantMessage("Hello! How can I help you?"),
        chat_api.UserMessage("what is 2+2?"),
        chat_api.AssistantMessage("4"),
        chat_api.UserMessage("And what did I say before that?"),
        chat_api.AssistantMessage("Before that, you said: \"hello\"."),
    ]


def _gen_multi_turn_tool_aware(rng: random.Random):
    n = rng.randint(0, 15)
    fibs = [0, 1]
    for _ in range(2, n + 1):
        fibs.append(fibs[-1] + fibs[-2])
    result = fibs[n]

    ordinal_n = _get_ordinal(n) # Use the helper

    return [
        *TOOLS,
        chat_api.UserMessage("Do you have a fibonacci tool?"),
        chat_api.AssistantMessage("yes"),
        chat_api.UserMessage(f"Use it to find the {ordinal_n} Fibonacci number."),
        chat_api.AssistantMessage(
            text=f"The {ordinal_n} Fibonacci number is {result}.",
            tool_calls=[chat_api.ToolCall(
                name="fibonacci",
                arguments={"n": n},
                output=str(result),
            )],
        ),
    ]


# -------------------------------- Generator list ---------------------------- #

GENERATORS = [
    # Self-identity
    _gen_name_qa,
    _gen_name_confirm,
    _gen_name_not_other,
    _gen_name_spell,
    _gen_name_length,
    _gen_name_lowercase,
    _gen_name_uppercase,
    _gen_identity,
    # Chat structure
    _gen_chat_awareness_single,
    _gen_identify_last_user,
    _gen_identify_last_assistant,
    _gen_count_user_messages,
    _gen_count_assistant_messages,
    _gen_first_user_message,
    _gen_message_order,
    _gen_is_conversation,
    _gen_total_messages,
    _gen_role_identify,
    # Tool awareness (no tool calls)
    _gen_tool_list,
    _gen_tool_count,
    _gen_tool_check_specific,
    _gen_tool_check_nonexistent,
    _gen_tool_describe,
    _gen_tools_for_math,
    _gen_tools_for_strings,
    # Tool calling (direct request)
    _gen_tool_call_direct,
    _gen_tool_call_reverse,
    _gen_tool_call_uppercase,
    _gen_tool_call_lowercase,
    _gen_tool_call_weather,
    _gen_tool_call_prime,
    _gen_tool_call_factorial,
    _gen_tool_call_fibonacci,
    _gen_tool_call_count_words,
    _gen_tool_call_for_task,
    # Multi-turn meta
    _gen_multi_turn_self_intro,
    _gen_multi_turn_tool_then_chat,
    _gen_multi_turn_self_then_tool,
    _gen_multi_turn_chat_aware,
    _gen_multi_turn_tool_aware,
]


# ----------------------------------- Load ----------------------------------- #

def load(n: int = 1000, seed: int | None = 0) -> list[list[chat_api.BaseItem]]:
    rng = random.Random(seed)
    samples = []
    for _ in range(n):
        gen = rng.choice(GENERATORS)
        samples.append(gen(rng))
    return samples
