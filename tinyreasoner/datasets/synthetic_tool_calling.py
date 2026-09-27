"""Should be correct, validated by Qwen3.7Plus."""

import json
import math
import random

import wonderwords

from .. import chat_api

random_word = wonderwords.RandomWord()



# ----------------------------- Tool definitions ----------------------------- #

TOOL_NAMES = [
    "calculator", "string_length", "reverse_string", "uppercase", "lowercase",
    "count_words", "lookup_weather", "lookup_population", "distance_between",
    "convert_currency", "is_prime", "factorial", "fibonacci", "sort_list",
    "list_contains", "get_user_info", "send_notification", "create_reminder",
    "get_date_info", "format_number",
]

TOOLS = [
    chat_api.ToolDefinition(
        "calculator",
        "Evaluate a mathematical expression.",
        {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Math expression to evaluate, e.g. '2 + 3 * 4'"},
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
        "lookup_population",
        "Look up the population of a city.",
        {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
            },
            "required": ["city"],
        },
    ),
    chat_api.ToolDefinition(
        "distance_between",
        "Calculate the distance between two cities in km.",
        {
            "type": "object",
            "properties": {
                "city1": {"type": "string", "description": "First city"},
                "city2": {"type": "string", "description": "Second city"},
            },
            "required": ["city1", "city2"],
        },
    ),
    chat_api.ToolDefinition(
        "convert_currency",
        "Convert an amount from one currency to another.",
        {
            "type": "object",
            "properties": {
                "amount": {"type": "number", "description": "Amount to convert"},
                "from_currency": {"type": "string", "description": "Source currency code (e.g. USD)"},
                "to_currency": {"type": "string", "description": "Target currency code (e.g. EUR)"},
            },
            "required": ["amount", "from_currency", "to_currency"],
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
    chat_api.ToolDefinition(
        "sort_list",
        "Sort a list of numbers.",
        {
            "type": "object",
            "properties": {
                "numbers": {"type": "array", "items": {"type": "number"}, "description": "List of numbers to sort"},
            },
            "required": ["numbers"],
        },
    ),
    chat_api.ToolDefinition(
        "list_contains",
        "Check if a list contains a specific value.",
        {
            "type": "object",
            "properties": {
                "list": {"type": "array", "items": {"type": "string"}, "description": "List to search"},
                "value": {"type": "string", "description": "Value to look for"},
            },
            "required": ["list", "value"],
        },
    ),
    chat_api.ToolDefinition(
        "get_user_info",
        "Retrieve information about a user by their ID.",
        {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "The user's ID"},
            },
            "required": ["user_id"],
        },
    ),
    chat_api.ToolDefinition(
        "send_notification",
        "Send a notification to a user.",
        {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "Recipient user ID"},
                "message": {"type": "string", "description": "Notification message"},
            },
            "required": ["user_id", "message"],
        },
    ),
    chat_api.ToolDefinition(
        "create_reminder",
        "Create a reminder for a user at a specific time.",
        {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "User ID"},
                "text": {"type": "string", "description": "Reminder text"},
                "time": {"type": "string", "description": "Time for the reminder (e.g. '2024-01-15 09:00')"},
            },
            "required": ["user_id", "text", "time"],
        },
    ),
    chat_api.ToolDefinition(
        "get_date_info",
        "Get information about a date (day of week, whether it's a weekend, etc.).",
        {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
            },
            "required": ["date"],
        },
    ),
    chat_api.ToolDefinition(
        "format_number",
        "Format a number with commas and specified decimal places.",
        {
            "type": "object",
            "properties": {
                "number": {"type": "number", "description": "Number to format"},
                "decimals": {"type": "integer", "description": "Number of decimal places"},
            },
            "required": ["number", "decimals"],
        },
    ),
]


# -------------------------------- Generators -------------------------------- #

def _gen_calculator_single(rng: random.Random):
    a = rng.randint(1, 100)
    b = rng.randint(1, 100)
    op = rng.choice(["+", "-", "*"])
    if op == "+": result = a + b
    elif op == "-": result = a - b
    else: result = a * b
    return (
        f"What is {a} {op} {b}?",
        [(f"I'll use calculator tool to compute {a} {op} {b}.",{"name": "calculator", "arguments": {"expression": f"{a}{op}{b}"}, "output": str(result)})],
        f"The result of {a} {op} {b} is {result}.",
    )


def _gen_calculator_complex(rng: random.Random):
    a = rng.randint(1, 50)
    b = rng.randint(1, 20)
    c = rng.randint(1, 10)
    result = (a + b) * c
    return (
        f"Calculate ({a} + {b}) * {c}.",
        [(f"I'll use calculator tool to compute ({a} + {b}) * {c}.",{"name": "calculator", "arguments": {"expression": f"({a}+{b})*{c}"}, "output": str(result)})],
        f"The result of ({a} + {b}) * {c} is {result}.",
    )


def _gen_string_operations(rng: random.Random):
    text = ' '.join(random_word.word() for _ in range(rng.randint(1, 10)))
    return (
        f"What is the length of the string \"{text}\"?",
        [("I'll use `string_length` tool to find the length of the string.",{"name": "string_length", "arguments": {"text": text}, "output": str(len(text))})],
        f"The string \"{text}\" has {len(text)} characters.",
    )


def _gen_reverse_string(rng: random.Random):
    text = ' '.join(random_word.word() for _ in range(rng.randint(1, 10)))
    reversed_text = text[::-1]
    return (
        f"Reverse the string \"{text}\".",
        [("I'll use `reverse_string` tool to reverse the string.", {"name": "reverse_string", "arguments": {"text": text}, "output": reversed_text})],
        f"The reverse of \"{text}\" is \"{reversed_text}\".",
    )


def _gen_case_conversion(rng: random.Random):
    text = ' '.join(random_word.word() for _ in range(rng.randint(1, 10)))
    if rng.random() < 0.5:
        tool_name = "uppercase"
        result = text.upper()
        action = "uppercase"
    else:
        tool_name = "lowercase"
        result = text.lower()
        action = "lowercase"
    return (
        f"Convert \"{text}\" to {action}.",
        [(f"I'll use `{tool_name}` tool to convert the string to {action}.", {"name": tool_name, "arguments": {"text": text}, "output": result})],
        f"The {action} of \"{text}\" is \"{result}\".",
    )


def _gen_count_words(rng: random.Random):
    text = ' '.join(random_word.word() for _ in range(rng.randint(1, 20)))
    count = len(text.split())
    return (
        f"How many words are in \"{text}\"?",
        [("I'll use `count_words` tool to count the number of words.",{"name": "count_words", "arguments": {"text": text}, "output": str(count)})],
        f"There are {count} words in the text.",
    )


def _gen_weather(rng: random.Random):
    cities = ["New York", "London", "Tokyo", "Paris", "Sydney", "Berlin", "Moscow", "Dubai"]
    conditions = ["sunny", "cloudy", "rainy", "snowy", "windy", "foggy"]

    city = rng.choice(cities)
    condition = rng.choice(conditions)
    temp = rng.randint(-10, 40)
    return (
        f"What's the weather like in {city}?",
        [(f"I'll use `lookup_weather` tool to look up the weather in {city}.", {"name": "lookup_weather", "arguments": {"city": city}, "output": f"{condition}, {temp}°C"})],
        f"The weather in {city} is {condition} with a temperature of {temp}°C.",
    )


def _gen_population(rng: random.Random):
    cities = {
        "New York": "8,336,817",
        "London": "8,982,000",
        "Tokyo": "13,960,000",
        "Paris": "2,161,000",
        "Sydney": "5,312,000",
        "Berlin": "3,645,000",
    }
    city = rng.choice(list(cities.keys()))
    pop = cities[city]
    return (
        f"What is the population of {city}?",
        [(f"I'll use `lookup_population` tool to look up the population in {city}.", {"name": "lookup_population", "arguments": {"city": city}, "output": pop})],
        f"The population of {city} is {pop}.",
    )


def _gen_distance(rng: random.Random):
    city_pairs = [
        ("New York", "London", "5,570"),
        ("Paris", "Berlin", "1,050"),
        ("Tokyo", "Sydney", "7,826"),
        ("London", "Paris", "344"),
        ("New York", "Los Angeles", "3,944"),
    ]
    c1, c2, dist = rng.choice(city_pairs)
    return (
        f"How far is it from {c1} to {c2}?",
        [(f"I'll use `distance_between` tool to find the distance between {c1} and {c2}.", {"name": "distance_between", "arguments": {"city1": c1, "city2": c2}, "output": f"{dist} km"})],
        f"The distance from {c1} to {c2} is {dist} km.",
    )


def _gen_currency(rng: random.Random):
    rates = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 149.5, "CAD": 1.36}
    currencies = list(rates.keys())
    from_cur = rng.choice(currencies)
    to_cur = rng.choice([c for c in currencies if c != from_cur])
    amount = rng.randint(10, 1000)
    converted = round(amount * rates[to_cur] / rates[from_cur], 2)
    return (
        f"Convert {amount} {from_cur} to {to_cur}.",
        [("I'll use `convert_currency` tool to find convert the currency.", {"name": "convert_currency", "arguments": {"amount": amount, "from_currency": from_cur, "to_currency": to_cur}, "output": f"{converted} {to_cur}"})],
        f"{amount} {from_cur} is equal to {converted} {to_cur}.",
    )


def _gen_is_prime(rng: random.Random):
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
    composites = [4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 21, 22, 24, 25]
    if rng.random() < 0.5:
        n = rng.choice(primes)
        answer = "true"
    else:
        n = rng.choice(composites)
        answer = "false"
    return (
        f"Is {n} a prime number?",
        [(f"I'll use `is_prime` tool to check if {n} is prime.",{"name": "is_prime", "arguments": {"number": n}, "output": answer})],
        f"Yes, {n} is a prime number." if answer == "true" else f"No, {n} is not a prime number.",
    )


def _gen_factorial(rng: random.Random):
    n = rng.randint(0, 10)
    result = math.factorial(n)
    return (
        f"What is {n} factorial?",
        [(f"I'll use `factorial` tool to calculate {n} factorial.",{"name": "factorial", "arguments": {"n": n}, "output": str(result)})],
        f"{n}! = {result}.",
    )


def _gen_fibonacci(rng: random.Random):
    n = rng.randint(0, 100)
    fibs = [0, 1]
    for _ in range(2, n + 1):
        fibs.append(fibs[-1] + fibs[-2])
    result = fibs[n]
    return (
        f"What is the {n}th Fibonacci number?",
        [(f"I'll use `fibonacci` tool to find {n}th Fibonacci number.",{"name": "fibonacci", "arguments": {"n": n}, "output": str(result)})],
        f"The {n}th Fibonacci number is {result}.",
    )


def _gen_sort(rng: random.Random):
    size = rng.randint(3, 8)
    numbers = [rng.randint(1, 100) for _ in range(size)]
    sorted_nums = sorted(numbers)
    nums_str = json.dumps(numbers)
    result_str = json.dumps(sorted_nums)
    return (
        f"Sort this list of numbers: {nums_str}",
        [("I'll use `sort_list` tool to sort the list.",{"name": "sort_list", "arguments": {"numbers": numbers}, "output": result_str})],
        f"The sorted list is {result_str}.",
    )


def _gen_list_contains(rng: random.Random):
    items = [random_word.word() for _ in range(rng.randint(3, 20))]
    if rng.random() < 0.7:
        value = rng.choice(items)
        output = "true"
    else:
        value = random_word.word()
        while value in items: value = random_word.word()
        output = "false"

    return (
        f"Does the list {items} contain \"{value}\"?",
        [(f"I'll use `list_contains` tool to check if the list contains \"{value}\".",{"name": "list_contains", "arguments": {"list": items, "value": value}, "output": output})],
        f"{'Yes' if output == 'true' else 'No'}, the list {'contains' if output == 'true' else 'does not contain'} \"{value}\".",
    )


def _gen_user_info(rng: random.Random):
    user_id = rng.randint(1, 1000)
    names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"]
    name = rng.choice(names)
    return (
        f"Get info for user {user_id}.",
        [(f"I'll use `get_user_info` tool to get user info for user {user_id}.",{"name": "get_user_info", "arguments": {"user_id": user_id}, "output": f"{{\"name\": \"{name}\", \"id\": {user_id}}}"})],
        f"User {user_id} is named {name}.",
    )


def _gen_send_notification(rng: random.Random):
    user_id = rng.randint(1, 1000)
    messages = [
        "Your order has shipped!",
        "You have a new message.",
        "Your subscription expires tomorrow.",
        "Welcome to our platform!",
        "Your password was changed.",
    ]
    message = rng.choice(messages)
    return (
        f"Send a notification to user {user_id} saying \"{message}\".",
        [("I'll use `send_notification` tool to send a notification.",{"name": "send_notification", "arguments": {"user_id": user_id, "message": message}, "output": "sent"})],
        f"Notification sent to user {user_id}: \"{message}\".",
    )


def _gen_create_reminder(rng: random.Random):
    user_id = rng.randint(1, 1000)
    reminders = [
        "Buy groceries",
        "Call the dentist",
        "Finish report",
        "Team meeting",
        "Pay rent",
    ]
    text = rng.choice(reminders)
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    hour = rng.randint(8, 18)
    time_str = f"2024-{month:02d}-{day:02d} {hour:02d}:00"
    return (
        f"Remind user {user_id} to \"{text}\" on {time_str}.",
        [("I'll use `create_reminder` tool to create a reminder.",{"name": "create_reminder", "arguments": {"user_id": user_id, "text": text, "time": time_str}, "output": "created"})],
        f"Reminder created for user {user_id}: \"{text}\" at {time_str}.",
    )


def _gen_date_info(rng: random.Random):
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    date_str = f"2024-{month:02d}-{day:02d}"
    import datetime
    dt = datetime.date(2024, month, day)
    day_name = dt.strftime("%A")
    is_weekend = dt.weekday() >= 5
    return (
        f"What day of the week is {date_str}?",
        [(f"I'll use `get_date_info` tool to find date of week of {date_str}.",{"name": "get_date_info", "arguments": {"date": date_str}, "output": f"{day_name}, {'weekend' if is_weekend else 'weekday'}"})],
        f"{date_str} is a {day_name} ({'weekend' if is_weekend else 'weekday'}).",
    )


def _gen_format_number(rng: random.Random):
    number = rng.uniform(1000, 999999)
    decimals = rng.choice([1, 2, 3, 4, 5])
    if decimals == 0:
        formatted = f"{round(number):,}"
    else:
        formatted = f"{number:,.{decimals}f}"
    return (
        f"Format the number {round(number, decimals)} with commas and {decimals} decimal places.",
        [("I'll use `format_number` tool to format the number.",{"name": "format_number", "arguments": {"number": round(number, decimals), "decimals": decimals}, "output": formatted})],
        f"The formatted number is {formatted}.",
    )


def _gen_multi_step_calc(rng: random.Random):
    a = rng.randint(1, 50)
    b = rng.randint(1, 50)
    sum_result = a + b
    product_result = sum_result * 2
    return (
        f"Add {a} and {b}, then multiply the result by 2.",
        [
            (f"First, I'll use calculator tool to compute {a} + {b}", {"name": "calculator", "arguments": {"expression": f"{a}+{b}"}, "output": str(sum_result)}),
            (f"{a} + {b} = {sum_result}. Now compute {sum_result} * 2.", {"name": "calculator", "arguments": {"expression": f"{sum_result} * 2"}, "output": str(product_result)}),
        ],
        f"First, {a} + {b} = {sum_result}. Then, {sum_result} * 2 = {product_result}.",
    )


def _gen_multi_step_string(rng: random.Random):
    words = ' '.join(random_word.word() for _ in range(rng.randint(1, 10)))
    text = " ".join(words)
    upper_text = text.upper()
    length = len(upper_text)
    return (
        f"Take the text \"{text}\", convert it to uppercase, and tell me its length.",
        [
            ("First, I'll use `uppercase` tool to convert the text to uppercase.", {"name": "uppercase", "arguments": {"text": text}, "output": upper_text}),
            ("Now I'll use `string_length` tool to find it's length.", {"name": "string_length", "arguments": {"text": upper_text}, "output": str(length)}),
        ],
        f"Converting \"{text}\" to uppercase gives \"{upper_text}\", which has {length} characters.",
    )


def _gen_weather_and_distance(rng: random.Random):
    c1, c2 = rng.sample(["New York", "London", "Paris", "Tokyo"], 2)
    condition1 = rng.choice(["sunny", "rainy", "cloudy"])
    temp1 = rng.randint(0, 35)
    condition2 = rng.choice(["sunny", "rainy", "cloudy"])
    temp2 = rng.randint(0, 35)
    dist = rng.randint(500, 10000)
    return (
        f"What's the weather in {c1} and {c2}, and how far apart are they?",
        [
            (f"I'll use `lookup_weather` tool to look up the weather in {c1} and {c2}.", {"name": "lookup_weather", "arguments": {"city": c1}, "output": f"{condition1}, {temp1}°C"}),
            (f"Now {c2}.", {"name": "lookup_weather", "arguments": {"city": c2}, "output": f"{condition2}, {temp2}°C"}),
            (f"Now I'll use `distance_between` tool to find distance between {c1} and {c2}.",{"name": "distance_between", "arguments": {"city1": c1, "city2": c2}, "output": f"{dist} km"}),
        ],
        f"{c1} is {condition1} at {temp1}°C, {c2} is {condition2} at {temp2}°C. They are {dist} km apart.",
    )


def _gen_prime_and_factorial(rng: random.Random):
    n = rng.randint(2, 30)
    is_p = all(n % i != 0 for i in range(2, int(n**0.5) + 1)) and n > 1
    fact = math.factorial(n)
    return (
        f"Is {n} prime? Also, what is {n}!?",
        [
            (f"First, I'll use `is_prime` tool to find if {n} is prime", {"name": "is_prime", "arguments": {"number": n}, "output": "true" if is_p else "false"}),
            (f"Now I'll use `factorial` tool to find {n} factorial.", {"name": "factorial", "arguments": {"n": n}, "output": str(fact)}),
        ],
        f"{n} is {'a prime' if is_p else 'not a prime'} number, and {n}! = {fact}.",
    )


def _gen_currency_and_notify(rng: random.Random):
    user_id = rng.randint(1, 1000)
    amount = rng.randint(50, 500)
    converted = round(amount * 0.92, 2)
    return (
        f"Convert {amount} USD to EUR and notify user {user_id} with the result.",
        [
            (f"I'll use `convert_currency` to convert the currency and `send_notification` to notify user {user_id}.", {"name": "convert_currency", "arguments": {"amount": amount, "from_currency": "USD", "to_currency": "EUR"}, "output": f"{converted} EUR"}),
            (f"Now notify user {user_id}.", {"name": "send_notification", "arguments": {"user_id": user_id, "message": f"{amount} USD = {converted} EUR"}, "output": "sent"}),
        ],
        f"{amount} USD is {converted} EUR. User {user_id} has been notified.",
    )


# -------------------------------- Generator list ---------------------------- #

GENERATORS = [
    _gen_calculator_single,
    _gen_calculator_complex,
    _gen_string_operations,
    _gen_reverse_string,
    _gen_case_conversion,
    _gen_count_words,
    _gen_weather,
    _gen_population,
    _gen_distance,
    _gen_currency,
    _gen_is_prime,
    _gen_factorial,
    _gen_fibonacci,
    _gen_sort,
    _gen_list_contains,
    _gen_user_info,
    _gen_send_notification,
    _gen_create_reminder,
    _gen_date_info,
    _gen_format_number,
    _gen_multi_step_calc,
    _gen_multi_step_string,
    _gen_weather_and_distance,
    _gen_prime_and_factorial,
    _gen_currency_and_notify,
]


# ----------------------------------- Load ----------------------------------- #

_TOOL_NAME_TO_DEF = {name: defn for name, defn in zip(TOOL_NAMES, [td for td in TOOLS])}


def _make_tool_call(tc: dict) -> chat_api.ToolCall:
    return chat_api.ToolCall(
        name=tc["name"],
        arguments=tc["arguments"],
        output=tc["output"],
    )


def _make_sample(
    user_query: str,
    tool_calls: list[tuple[str, dict]],
    final_response: str,
    rng: random.Random,
) -> list[chat_api.BaseItem]:
    required = list({tc["name"] for _, tc in tool_calls})
    irrelevant_pool = [n for n in TOOL_NAMES if n not in required]
    n_irrelevant = rng.randint(0, min(len(irrelevant_pool), rng.randint(0, 5)))
    irrelevant = rng.sample(irrelevant_pool, n_irrelevant)
    selected = required + irrelevant
    rng.shuffle(selected)

    asst_msgs = []
    for msg, tc in tool_calls:
        asst_msgs.append(chat_api.AssistantMessage(text=msg, tool_call=_make_tool_call(tc)))

    return [
        *[_TOOL_NAME_TO_DEF[n] for n in selected],
        chat_api.UserMessage(user_query),
        *asst_msgs,
        chat_api.AssistantMessage(
            text=final_response,
        ),
    ]


def load(n: int = 1000, seed: int | None = 0) -> list[list[chat_api.BaseItem]]:
    rng = random.Random(seed)
    samples = []
    for _ in range(n):
        gen = rng.choice(GENERATORS)
        user_query, tool_calls, final_response = gen(rng)
        samples.append(_make_sample(user_query, tool_calls, final_response, rng))
    return samples
