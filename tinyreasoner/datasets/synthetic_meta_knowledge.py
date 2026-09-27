"""Should be correct. Though Qwen3.7 gets confused..."""
import json
import random

import wonderwords

from .. import chat_api

random_word = wonderwords.RandomWord()

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
        *rng.sample(TOOLS, k=rng.randint(0, len(TOOLS))),
        chat_api.UserMessage(q),
        chat_api.AssistantMessage(text="I am tinyreasoner."),
    ]


def _gen_name_confirm(rng: random.Random):
    names = ["tinyreasoner", "TinyReasoner", "TINYREASONER"]
    name = rng.choice(names)
    return [
        *rng.sample(TOOLS, k=rng.randint(0, len(TOOLS))),
        chat_api.UserMessage(f"Are you {name}?"),
        chat_api.AssistantMessage(text="Yes, I am tinyreasoner."),
    ]


def _gen_name_not_other(rng: random.Random):
    other_names = ["gpt-4", "claude", "llama", "gpt-3", "bert", "chatgpt", "bard", "gemini", "john", "mark", "ann", "liz"]
    name = rng.choice(other_names)
    return [
        *rng.sample(TOOLS, k=rng.randint(0, len(TOOLS))),
        chat_api.UserMessage(f"Are you {name}?"),
        chat_api.AssistantMessage(text=f"I am not {name}. I am tinyreasoner."),
    ]


def _gen_name_spell(rng: random.Random):
    return [
        *rng.sample(TOOLS, k=rng.randint(0, len(TOOLS))),
        chat_api.UserMessage("How do you spell your name?"),
        chat_api.AssistantMessage(text="t-i-n-y-r-e-a-s-o-n-e-r"),
    ]


def _gen_name_length(rng: random.Random):
    return [
        chat_api.UserMessage("How many characters are in your name?"),
        chat_api.AssistantMessage(text=f"My name, tinyreasoner, contains {len("tinyreasoner")} characters."),
    ]


def _gen_name_lowercase(rng: random.Random):
    return [
        chat_api.UserMessage("What is your name in lowercase?"),
        chat_api.AssistantMessage(text="tinyreasoner"),
    ]


def _gen_name_uppercase(rng: random.Random):
    return [
        chat_api.UserMessage("What is your name in uppercase?"),
        chat_api.AssistantMessage(text="TINYREASONER"),
    ]


def _gen_identity(rng: random.Random):
    questions = [
        "Describe yourself in one word",
        "Write down your name",
        "Output your name and nothing else",
    ]
    q = rng.choice(questions)
    return [
        *rng.sample(TOOLS, k=rng.randint(0, len(TOOLS))),
        chat_api.UserMessage(q),
        chat_api.AssistantMessage(text="tinyreasoner"),
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
        chat_api.AssistantMessage(text=resp),
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
        items.append(chat_api.AssistantMessage(text=asst_msg))
    items.append(chat_api.UserMessage("What was my previous message?"))
    items.append(chat_api.AssistantMessage(text=f"Your previous message was: \"{last_user}\""))
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
        items.append(chat_api.AssistantMessage(text=asst_msg))
    items.append(chat_api.UserMessage("What was your last message?"))
    items.append(chat_api.AssistantMessage(text=f"My last message was: \"{last_asst}\""))
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
    items: list = rng.sample(TOOLS, k=rng.randint(0, len(TOOLS)))

    for user_msg, asst_msg in selected:
        items.append(chat_api.UserMessage(user_msg))
        items.append(chat_api.AssistantMessage(text=asst_msg))
    items.append(chat_api.UserMessage("How many user messages have been sent?"))
    items.append(chat_api.AssistantMessage(text=f"{n + 1}"))
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
    items: list = rng.sample(TOOLS, k=rng.randint(0, len(TOOLS)))
    for user_msg, asst_msg in selected:
        items.append(chat_api.UserMessage(user_msg))
        items.append(chat_api.AssistantMessage(text=asst_msg))
    items.append(chat_api.UserMessage("How many assistant messages have been sent?"))
    items.append(chat_api.AssistantMessage(text=str(n)))
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
    items = [chat_api.UserMessage(first), chat_api.AssistantMessage(text="Hello!")]
    for msg, resp in others:
        items.append(chat_api.UserMessage(msg))
        items.append(chat_api.AssistantMessage(text=resp))
    items.append(chat_api.UserMessage("What was the first user message?"))
    items.append(chat_api.AssistantMessage(text=f"The first user message was: \"{first}\""))
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
        items.append(chat_api.AssistantMessage(text=asst_msg))
    items.append(chat_api.UserMessage("What message came right after the first user message?"))
    items.append(chat_api.AssistantMessage(text=f"After your first message, I responded with: \"{selected[0][1]}\""))
    return items


def _gen_is_conversation(rng: random.Random):
    return [
        chat_api.UserMessage("Is this a conversation between a user and an assistant?"),
        chat_api.AssistantMessage(text="Yes, this is a conversation between you (user) and me (assistant)."),
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
    items: list = rng.sample(TOOLS, k=rng.randint(0, len(TOOLS)))
    for user_msg, asst_msg in selected:
        items.append(chat_api.UserMessage(user_msg))
        items.append(chat_api.AssistantMessage(text=asst_msg))
    items.append(chat_api.UserMessage("How many messages are there in total in this chat?"))
    items.append(chat_api.AssistantMessage(text=f"There are {n * 2 + 1} messages in this chat."))
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
        items.append(chat_api.AssistantMessage(text=asst_msg))
    idx = rng.randint(0, n - 1)
    role = "user" if rng.random() < 0.5 else "assistant"
    if role == "user":
        content = selected[idx][0]
    else:
        content = selected[idx][1]
    items.append(chat_api.UserMessage(f"Who said: \"{content}\"?"))
    items.append(chat_api.AssistantMessage(text=role))
    return items


# ----------------------- Tool awareness generators -------------------------- #

def _gen_tool_list(rng: random.Random):
    tools = rng.sample(TOOLS, k=rng.randint(0, len(TOOLS)))
    if len(tools) == 0:
        return [
            chat_api.UserMessage("What tools do you have available?"),
            chat_api.AssistantMessage(text="I don't have any tools available."),
        ]

    return [
        *tools,
        chat_api.UserMessage("What tools do you have available?"),
        chat_api.AssistantMessage(text=f"I have the following tools: {', '.join(t.name for t in tools)}."),
    ]


def _gen_tool_count(rng: random.Random):
    tools = rng.sample(TOOLS, k=rng.randint(0, len(TOOLS)))
    l = f"{len(tools)}" if len(tools) > 0 else "no"
    return [
        *tools,
        chat_api.UserMessage("How many tools do you have?"),
        chat_api.AssistantMessage(text=f"I have {l} tools available."),
    ]


def _gen_tool_check_specific(rng: random.Random):
    tools = rng.sample(TOOLS, k=rng.randint(0, len(TOOLS)))
    name = rng.choice([t.name for t in TOOLS] + ["web_search", "email_sender", "file_reader", "database_query", "image_generator"])
    resp = f"Yes, I have a tool called \"{name}\"." if name in tools else f"No, I don't have a tool called \"{name}\"."
    return [
        *tools,
        chat_api.UserMessage(f"Do you have a tool called \"{name}\"?"),
        chat_api.AssistantMessage(text=resp),
    ]


def _gen_tool_describe(rng: random.Random):
    tool_schemas = []
    for t in TOOLS:
        tool_schemas.append((t.name, t.description))
    name, desc = rng.choice(tool_schemas)
    return [
        *TOOLS,
        chat_api.UserMessage(f"What does the \"{name}\" tool do?"),
        chat_api.AssistantMessage(text=f"The \"{name}\" tool has the following description: {desc}"),
    ]


def _gen_tool_call_direct(rng: random.Random):
    tools = rng.sample(TOOLS, k=rng.randint(0, len(TOOLS)))

    if rng.random() < 0.5:
        a, b = rng.randint(1, 50), rng.randint(1, 50)
        op = rng.choice(["+", "-", "*"])
        if op == "+": result = a + b
        elif op == "-": result = a - b
        else: result = a * b
        expr = f"{a} {op} {b}"
        if 'calculator' not in [t.name for t in tools]:
            return [
                *tools,
                chat_api.UserMessage(f'Call the calculator tool with expression "{expr}"'),
                chat_api.AssistantMessage(text=("I am sorry, but I don't have a `calculator` tool. I can "
                                                f"calculate this manually for you: {a} {op} {b} = {result}."))
            ]

        return [
            *tools,
            chat_api.UserMessage(f"Call the calculator tool with expression \"{expr}\""),
            chat_api.AssistantMessage(
                text = f"I'll use the calculator tool to evaluate \"{expr}\"",
                tool_call=chat_api.ToolCall(
                    name="calculator",
                    arguments={"expression": expr},
                    output=str(result),
                ),
            ),
            chat_api.AssistantMessage(text=f"Done. The result is {result}.",)
        ]

    else:
        text = random_word.word()

        if 'string_length' not in [t.name for t in tools]:
            return [
                *tools,
                chat_api.UserMessage(f"Call the string_length tool on \"{text}\""),
                chat_api.AssistantMessage(text=("I am sorry, but I don't have a `string_length` tool. Looking at "
                                                f"the string \"{text}\", it's length is {len(text)}"))
                ]

        return [
            *tools,
            chat_api.UserMessage(f"Call the string_length tool on \"{text}\""),
            chat_api.AssistantMessage(
                text = f"I'll use the `string_length` tool on \"{text}\"",
                tool_call=chat_api.ToolCall(
                    name="string_length",
                    arguments={"text": text},
                    output=str(len(text)),
                ),
            ),
            chat_api.AssistantMessage(text=f"Done. The result is {len(text)}.",)
        ]


def _gen_tool_call_reverse(rng: random.Random):
    text = random_word.word()
    return [
        *TOOLS,
        chat_api.UserMessage(f"Use the reverse_string tool on \"{text}\""),
        chat_api.AssistantMessage(
            text="I'll use the `reverse_string` tool.",
            tool_call=chat_api.ToolCall(
                name="reverse_string",
                arguments={"text": text},
                output=text[::-1],
            ),
        ),
        chat_api.AssistantMessage(text=f"Done. The reversed string is \"{text[::-1]}\".")
    ]


def _gen_tool_call_uppercase(rng: random.Random):
    text = random_word.word()
    return [
        *TOOLS,
        chat_api.UserMessage(f"Use the uppercase tool on \"{text}\""),
        chat_api.AssistantMessage(
            text="I'll use the `uppercase` tool.",
            tool_call=chat_api.ToolCall(
                name="uppercase",
                arguments={"text": text},
                output=text.upper(),
            ),
        ),
        chat_api.AssistantMessage(text=f"Done. The uppercase is \"{text.upper()}\".")
    ]


def _gen_tool_call_weather(rng: random.Random):
    city = rng.choice(["New York", "London", "Tokyo", "Paris", "Sydney"])
    condition = rng.choice(["sunny", "cloudy", "rainy"])
    temp = rng.randint(-5, 35)
    return [
        *TOOLS,
        chat_api.UserMessage(f"Use the lookup_weather tool for \"{city}\""),
        chat_api.AssistantMessage(
            text=f"I'll use the `lookup_weather` tool to look up the weather in {city}.",
            tool_call=chat_api.ToolCall(
                name="lookup_weather",
                arguments={"city": city},
                output=f"{condition}, {temp}°C",
            ),
        ),
        chat_api.AssistantMessage(text=f"The weather in {city} is {condition} at {temp}°C.")
    ]


def _gen_tool_call_prime(rng: random.Random):
    primes = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97,101,103,107,109,113,127,131,137,139,149,151,157,163,167,173,179,181,191,193,197,199,211,223,227,229,233,239,241,251,257,263,269,271,277,281,283,293,307,311,313,317,331,337,347,349,353,359,367,373,379,383,389,397,401,409,419,421,431,433,439,443,449,457,461,463,467,479,487,491,499,503,509,521,523,541,547,557,563,569,571,577,587,593,599,601,607,613,617,619,631,641,643,647,653,659,661,673,677,683,691,701,709,719,727,733,739,743,751,757,761,769,773,787,797,809,811,821,823,827,829,839,853,857,859,863,877,881,883,887,907,911,919,929,937,941,947,953,967,971,977,983,991,997,1009,1013,1019,1021,1031,1033,1039,1049,1051,1061,1063,1069,1087,1091,1093,1097,1103,1109,1117,1123,1129,1151,1153,1163,1171,1181,1187,1193,1201,1213,1217,1223,1229,1231,1237,1249,1259,1277,1279,1283,1289,1291,1297,1301,1303,1307,1319,1321,1327,1361,1367,1373,1381,1399,1409,1423,1427,1429,1433,1439,1447,1451,1453,1459,1471,1481,1483,1487,1489,1493,1499,1511,1523,1531,1543,1549,1553,1559,1567,1571,1579,1583,1597,1601,1607,1609,1613,1619,1621,1627,1637,1657,1663,1667,1669,1693,1697,1699,1709,1721,1723,1733,1741,1747,1753,1759,1777,1783,1787,1789,1801,1811,1823,1831,1847,1861,1867,1871,1873,1877,1879,1889,1901,1907,1913,1931,1933,1949,1951,1973,1979,1987,1993,1997,1999,2003,2011,2017,2027,2029,2039,2053,2063,2069,2081,2083,2087,2089,2099,2111,2113,2129,2131,2137,2141,2143,2153,2161,2179,2203,2207,2213,2221,2237,2239,2243,2251,2267,2269,2273,2281,2287,2293,2297,2309,2311,2333,2339,2341,2347,2351,2357,2371,2377,2381,2383,2389,2393,2399,2411,2417,2423,2437,2441,2447,2459,2467,2473,2477,2503,2521,2531,2539,2543,2549,2551,2557,2579,2591,2593,2609,2617,2621,2633,2647,2657,2659,2663,2671,2677,2683,2687,2689,2693,2699,2707,2711,2713,2719,2729,2731,2741,2749,2753,2767,2777,2789,2791,2797,2801,2803,2819,2833,2837,2843,2851,2857,2861,2879,2887,2897,2903,2909,2917,2927,2939,2953,2957,2963,2969,2971,2999,3001,3011,3019,3023,3037,3041,3049,3061,3067,3079,3083,3089,3109,3119,3121,3137,3163,3167,3169,3181,3187,3191,3203,3209,3217,3221,3229,3251,3253,3257,3259,3271,3299,3301,3307,3313,3319,3323,3329,3331,3343,3347,3359,3361,3371,3373,3389,3391,3407,3413,3433,3449,3457,3461,3463,3467,3469,3491,3499,3511,3517,3527,3529,3533,3539,3541,3547,3557,3559,3571,3581,3583,3593,3607,3613,3617,3623,3631,3637,3643,3659,3671,3673,3677,3691,3697,3701,3709,3719,3727,3733,3739,3761,3767,3769,3779,3793,3797,3803,3821,3823,3833,3847,3851,3853,3863,3877,3881,3889,3907,3911,3917,3919,3923,3929,3931,3943,3947,3967,3989,4001,4003,4007,4013,4019,4021,4027,4049,4051,4057,4073,4079,4091,4093,4099,4111,4127,4129,4133,4139,4153,4157,4159,4177,4201,4211,4217,4219,4229,4231,4241,4243,4253,4259,4261,4271,4273,4283,4289,4297,4327,4337,4339,4349,4357,4363,4373,4391,4397,4409,4421,4423,4441,4447,4451,4457,4463,4481,4483,4493,4507,4513,4517,4519,4523,4547,4549,4561,4567,4583,4591,4597,4603,4621,4637,4639,4643,4649,4651,4657,4663,4673,4679,4691,4703,4721,4723,4729,4733,4751,4759,4783,4787,4789,4793,4799,4801,4813,4817,4831,4861,4871,4877,4889,4903,4909,4919,4931,4933,4937,4943,4951,4957,4967,4969,4973,4987,4993,4999,5003,5009,5011,5021,5023,5039,5051,5059,5077,5081,5087,5099,5101,5107,5113,5119,5147,5153,5167,5171,5179,5189,5197,5209,5227,5231,5233,5237,5261,5273,5279,5281,5297,5303,5309,5323,5333,5347,5351,5381,5387,5393,5399,5407,5413,5417,5419,5431,5437,5441,5443,5449,5471,5477,5479,5483,5501,5503,5507,5519,5521,5527,5531,5557,5563,5569,5573,5581,5591,5623,5639,5641,5647,5651,5653,5657,5659,5669,5683,5689,5693,5701,5711,5717,5737,5741,5743,5749,5779,5783,5791,5801,5807,5813,5821,5827,5839,5843,5849,5851,5857,5861,5867,5869,5879,5881,5897,5903,5923,5927,5939,5953,5981,5987,6007,6011,6029,6037,6043,6047,6053,6067,6073,6079,6089,6091,6101,6113,6121,6131,6133,6143,6151,6163,6173,6197,6199,6203,6211,6217,6221,6229,6247,6257,6263,6269,6271,6277,6287,6299,6301,6311,6317,6323,6329,6337,6343,6353,6359,6361,6367,6373,6379,6389,6397,6421,6427,6449,6451,6469,6473,6481,6491,6521,6529,6547,6551,6553,6563,6569,6571,6577,6581,6599,6607,6619,6637,6653,6659,6661,6673,6679,6689,6691,6701,6703,6709,6719,6733,6737,6761,6763,6779,6781,6791,6793,6803,6823,6827,6829,6833,6841,6857,6863,6869,6871,6883,6899,6907,6911,6917,6947,6949,6959,6961,6967,6971,6977,6983,6991,6997,7001,7013,7019,7027,7039,7043,7057,7069,7079,7103,7109,7121,7127,7129,7151,7159,7177,7187,7193,7207,7211,7213,7219,7229,7237,7243,7247,7253,7283,7297,7307,7309,7321,7331,7333,7349,7351,7369,7393,7411,7417,7433,7451,7457,7459,7477,7481,7487,7489,7499,7507,7517,7523,7529,7537,7541,7547,7549,7559,7561,7573,7577,7583,7589,7591,7603,7607,7621,7639,7643,7649,7669,7673,7681,7687,7691,7699,7703,7717,7723,7727,7741,7753,7757,7759,7789,7793,7817,7823,7829,7841,7853,7867,7873,7877,7879,7883,7901,7907,7919]
    if rng.random() < 0.5:
        n = rng.choice(primes)
        output = "true"
    else:
        n1, n2 = random.choices(primes)
        n = n1 * n2
        output = "false"
    return [
        *TOOLS,
        chat_api.UserMessage(f"Use the is_prime tool on {n}"),
        chat_api.AssistantMessage(
            text=f"I'll use the `is_prime` tool on {n}.",
            tool_call=chat_api.ToolCall(
                name="is_prime",
                arguments={"number": n},
                output=output,
            ),
        ),
        chat_api.AssistantMessage(text=f"{n} is {'a prime' if output == 'true' else 'not a prime'} number.")
    ]


def _gen_tool_call_factorial(rng: random.Random):
    import math
    n = rng.randint(0, 30)
    result = math.factorial(n)
    return [
        *TOOLS,
        chat_api.UserMessage(f"Use the factorial tool on {n}"),
        chat_api.AssistantMessage(
            text=f"I'll use the `factorial` tool on {n}.",
            tool_call=chat_api.ToolCall(
                name="factorial",
                arguments={"n": n},
                output=str(result),
            ),
        ),
        chat_api.AssistantMessage(text=f"{n}! = {result}.")
    ]


def _gen_tool_call_fibonacci(rng: random.Random):

    n = rng.randint(0, 100)
    fibs = [0, 1]
    for _ in range(2, n + 1):
        fibs.append(fibs[-1] + fibs[-2])
    result = fibs[n]
    return [
        *TOOLS,
        chat_api.UserMessage(f"Use the fibonacci tool on {n}"),
        chat_api.AssistantMessage(
            text=f"I'll use the `fibonacci` tool on {n}.",
            tool_call=chat_api.ToolCall(
                name="fibonacci",
                arguments={"n": n},
                output=str(result),
            ),
        ),
        chat_api.AssistantMessage(text=f"The {_get_ordinal(n)} Fibonacci number is {result}.")
    ]


def _gen_tool_call_lowercase(rng: random.Random):
    text = random_word.word().upper()
    return [
        *TOOLS,
        chat_api.UserMessage(f"Use the lowercase tool on \"{text}\""),
        chat_api.AssistantMessage(
            text=f"I'll use the `lowercase` tool on \"{text}\".",
            tool_call=chat_api.ToolCall(
                name="lowercase",
                arguments={"text": text},
                output=text.lower(),
            ),
        ),
        chat_api.AssistantMessage(text=f"Done. The lowercase is \"{text.lower()}\".")
    ]


def _gen_tool_call_count_words(rng: random.Random):
    text = rng.choice(["hello world", "the quick brown fox", "I love programming"])
    count = len(text.split())
    return [
        *TOOLS,
        chat_api.UserMessage(f"Use the count_words tool on \"{text}\""),
        chat_api.AssistantMessage(
            text="I'll use the `count_words` tool.",
            tool_call=chat_api.ToolCall(
                name="count_words",
                arguments={"text": text},
                output=str(count),
            ),
        ),
        chat_api.AssistantMessage(text=f"There are {count} words.")
    ]


def _gen_tool_call_for_task(rng: random.Random):
    if rng.random() < 0.5:
        a, b = rng.randint(1, 50), rng.randint(1, 50)
        result = a * b
        return [
            *TOOLS,
            chat_api.UserMessage(f"What is {a} times {b}? Use the calculator tool."),
            chat_api.AssistantMessage(
                text=f"I'll use the calculator tool to compute {a} * {b}.",
                tool_call=chat_api.ToolCall(
                    name="calculator",
                    arguments={"expression": f"{a}*{b}"},
                    output=str(result),
                ),
            ),
            chat_api.AssistantMessage(text=f"{a} * {b} = {result}.")
        ]
    else:
        text = random_word.word()
        return [
            *TOOLS,
            chat_api.UserMessage(f"How long is \"{text}\"? Use the string_length tool."),
            chat_api.AssistantMessage(
                text=f"I'll use the `string_length` tool on \"{text}\".",
                tool_call=chat_api.ToolCall(
                    name="string_length",
                    arguments={"text": text},
                    output=str(len(text)),
                ),
            ),
            chat_api.AssistantMessage(text=f"The string \"{text}\" has {len(text)} characters.")
        ]


def _gen_tools_for_math(rng: random.Random):
    return [
        *TOOLS,
        chat_api.UserMessage("What tools can I use for math?"),
        chat_api.AssistantMessage(text="For math, you can use: calculator, is_prime, factorial, and fibonacci."),
    ]


def _gen_tools_for_strings(rng: random.Random):
    return [
        *TOOLS,
        chat_api.UserMessage("What tools can I use for strings?"),
        chat_api.AssistantMessage(text="For strings, you can use: string_length, reverse_string, uppercase, lowercase, and count_words."),
    ]


# ---------------------- Multi-turn meta generators -------------------------- #

def _gen_multi_turn_self_intro(rng: random.Random):

    v1 = rng.randint(-100, 100)
    v2 = rng.randint(-100, 100)
    op = rng.choice(['+', '-', '*', '^'])
    if op == "+": res = v1 + v2
    elif op == '-': res = v1 - v2
    elif op == "*": res = v1 * v2
    elif op == '^':
        v1 = abs(v1) + 1
        v2 = abs(v2) + 1
        res = v1 ** v2
    else:
        raise RuntimeError("can't happen")

    return [
        *TOOLS,
        chat_api.UserMessage("Hi, what is your name?"),
        chat_api.AssistantMessage(text="I am tinyreasoner."),
        chat_api.UserMessage("What tools do you have?"),
        chat_api.AssistantMessage(
            text="I have the following tools: calculator, string_length, reverse_string, "
            "uppercase, lowercase, count_words, lookup_weather, is_prime, factorial, and fibonacci."
        ),
        chat_api.UserMessage(f"Use the calculator to compute {v1} {op} {v2}."),
        chat_api.AssistantMessage(
            text=f"I'll use the `calculator` tool to compute {v1} {op} {v2}..",
            tool_call=chat_api.ToolCall(
                name="calculator",
                arguments={"expression": f"{v1}{op}{v2}"},
                output=f"{res}",
            ),
        ),
        chat_api.AssistantMessage(text=f"{v1} {op} {v2} = {res}."),
    ]


def _gen_multi_turn_tool_then_chat(rng: random.Random):
    city = rng.choice(["New York", "London", "Tokyo"])
    condition = rng.choice(["sunny", "cloudy", "rainy"])
    temp = rng.randint(0, 35)
    return [
        *TOOLS,
        chat_api.UserMessage(f"What is the weather in {city}?"),
        chat_api.AssistantMessage(
            text=f"I'll use the `lookup_weather` tool to look up the weather in {city}.",
            tool_call=chat_api.ToolCall(
                name="lookup_weather",
                arguments={"city": city},
                output=f"{condition}, {temp}°C",
            ),
        ),
        chat_api.AssistantMessage(text=f"The weather in {city} is {condition} at {temp}°C."),
        chat_api.UserMessage("What is your name again?"),
        chat_api.AssistantMessage(text="I am tinyreasoner."),
    ]


def _gen_multi_turn_self_then_tool(rng: random.Random):
    text = random_word.word()
    return [
        *TOOLS,
        chat_api.UserMessage("What is your name?"),
        chat_api.AssistantMessage(text="I am tinyreasoner."),
        chat_api.UserMessage(f"Reverse the string \"{text}\"."),
        chat_api.AssistantMessage(
            text=f"I'll use the `reverse_string` tool to reverse \"{text}\".",
            tool_call=chat_api.ToolCall(
                name="reverse_string",
                arguments={"text": text},
                output=text[::-1],
            ),
        ),
        chat_api.AssistantMessage(text=f"The reverse of \"{text}\" is \"{text[::-1]}\".",)
    ]


def _gen_multi_turn_chat_aware(rng: random.Random):
    return [
        chat_api.UserMessage("hello"),
        chat_api.AssistantMessage(text="Hello! How can I help you?"),
        chat_api.UserMessage("what is 2+2?"),
        chat_api.AssistantMessage(text="4"),
        chat_api.UserMessage("And what did I say before that?"),
        chat_api.AssistantMessage(text="Before that, you said: \"hello\"."),
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
        chat_api.AssistantMessage(text="yes"),
        chat_api.UserMessage(f"Use it to find the {ordinal_n} Fibonacci number."),
        chat_api.AssistantMessage(
            text=f"I'll use the `fibonacci` tool to find the {ordinal_n} Fibonacci number.",
            tool_call=chat_api.ToolCall(
                name="fibonacci",
                arguments={"n": n},
                output=str(result),
            ),
        ),
        chat_api.AssistantMessage(text=f"The {ordinal_n} Fibonacci number is {result}.")
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
