"""All are definitely correct, validated through executing the functions."""
import contextlib
import io
import random

from .. import chat_api


def _gen_simple_assignment(rng: random.Random):
    x = rng.randint(1, 50)
    y = rng.randint(1, 50)
    code = f"x = {x}\ny = {y}\nz = x + y\nprint(z)"

    z = x + y
    return f"What does this code print?\n\n{code}", str(z)


def _gen_reassignment(rng: random.Random):
    x = rng.randint(1, 50)
    y = rng.randint(1, 50)
    code = f"x = {x}\ny = {y}\nx = x + y\ny = x - y\nprint(x, y)"

    x = x + y
    y = x - y
    return f"What does this code print?\n\n{code}", f"{x} {y}"


def _gen_swap(rng: random.Random):
    a = rng.randint(1, 50)
    b = rng.randint(1, 50)
    code = f"a = {a}\nb = {b}\na = a + b\nb = a - b\na = a - b\nprint(a, b)"

    a = a + b
    b = a - b
    a = a - b
    return f"What does this code print?\n\n{code}", f"{a} {b}"


def _gen_simple_if(rng: random.Random):
    x = rng.randint(1, 50)
    threshold = rng.randint(1, 50)
    if x > threshold:
        result = x * 2
    else:
        result = x + 10
    code = f"x = {x}\nif x > {threshold}:\n    print(x * 2)\nelse:\n    print(x + 10)"
    return f"What does this code print?\n\n{code}", str(result)


def _gen_nested_if(rng: random.Random):
    x = rng.randint(1, 30)
    y = rng.randint(1, 30)
    if x > 10:
        if y > 10:
            result = "big big"
        else:
            result = "big small"
    else:
        if y > 10:
            result = "small big"
        else:
            result = "small small"
    code = f"x = {x}\ny = {y}\nif x > 10:\n    if y > 10:\n        print('big big')\n    else:\n        print('big small')\nelse:\n    if y > 10:\n        print('small big')\n    else:\n        print('small small')"
    return f"What does this code print?\n\n{code}", result


def _gen_while_sum(rng: random.Random):
    n = rng.randint(3, 10)
    total = sum(range(1, n + 1))
    code = f"total = 0\ni = 1\nwhile i <= {n}:\n    total = total + i\n    i = i + 1\nprint(total)"
    return f"What does this code print?\n\n{code}", str(total)


def _gen_while_count(rng: random.Random):
    target = rng.randint(3, 15)
    count = 0
    n = target
    while n > 0:
        count += 1
        n -= 1
    code = f"count = 0\nn = {target}\nwhile n > 0:\n    count = count + 1\n    n = n - 1\nprint(count)"
    return f"What does this code print?\n\n{code}", str(target)


def _gen_for_range(rng: random.Random):
    n = rng.randint(2, 8)
    total = sum(i * 2 for i in range(1, n + 1))
    code = f"total = 0\nfor i in range(1, {n + 1}):\n    total = total + i * 2\nprint(total)"
    return f"What does this code print?\n\n{code}", str(total)


def _gen_nested_loop(rng: random.Random):
    n = rng.randint(2, 5)
    total = n * n
    code = f"count = 0\nfor i in range({n}):\n    for j in range({n}):\n        count = count + 1\nprint(count)"
    return f"What does this code print?\n\n{code}", str(total)


def _gen_loop_break(rng: random.Random):
    target = rng.randint(3, 10)
    code = f"for i in range(1, 20):\n    if i == {target}:\n        print(i)\n        break"
    return f"What does this code print?\n\n{code}", str(target)


def _gen_list_append(rng: random.Random):
    vals = [rng.randint(1, 20) for _ in range(3)]
    code = "lst = []\n"
    for v in vals:
        code += f"lst.append({v})\n"
    code += "print(lst)"
    return f"What does this code print?\n\n{code}", str(vals)


def _gen_list_comprehension(rng: random.Random):
    n = rng.randint(3, 8)
    result = [i * i for i in range(1, n + 1)]
    code = f"squares = [i * i for i in range(1, {n + 1})]\nprint(squares)"
    return f"What does this code print?\n\n{code}", str(result)


def _gen_dict_lookup(rng: random.Random):
    keys = rng.sample(["a", "b", "c", "d", "e"], 3)
    vals = [rng.randint(1, 20) for _ in range(3)]
    pairs = ", ".join(f"'{k}': {v}" for k, v in zip(keys, vals))
    lookup_key = rng.choice(keys)
    lookup_val = vals[keys.index(lookup_key)]
    code = f"d = {{{pairs}}}\nprint(d['{lookup_key}'])"
    return f"What does this code print?\n\n{code}", str(lookup_val)


def _gen_dict_update(rng: random.Random):
    a = rng.randint(1, 20)
    b = rng.randint(1, 20)
    c = rng.randint(1, 20)
    code = f"d = {{'x': {a}, 'y': {b}}}\nd['z'] = {c}\nprint(d)"
    return f"What does this code print?\n\n{code}", str({"x": a, "y": b, "z": c})


def _gen_string_format(rng: random.Random):
    name = rng.choice(["alice", "bob", "charlie"])
    age = rng.randint(10, 50)
    code = f"name = '{name}'\nage = {age}\nprint(f'{{name}} is {{age}}')"
    return f"What does this code print?\n\n{code}", f"{name} is {age}"


def _gen_string_slice(rng: random.Random):
    s = "".join(rng.choices("abcdefgh", k=rng.randint(4, 8)))
    start = rng.randint(0, len(s) - 2)
    end = rng.randint(start + 1, len(s))
    code = f"s = '{s}'\nprint(s[{start}:{end}])"
    return f"What does this code print?\n\n{code}", s[start:end]


def _gen_function_simple(rng: random.Random):
    a = rng.randint(1, 20)
    b = rng.randint(1, 20)
    result = a + b + 10
    code = f"def add_ten(x, y):\n    return x + y + 10\n\nresult = add_ten({a}, {b})\nprint(result)"
    return f"What does this code print?\n\n{code}", str(result)


def _gen_function_recursive(rng: random.Random):
    n = rng.randint(1, 8)
    result = 1
    for i in range(1, n + 1):
        result *= i
    code = f"def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n\nprint(factorial({n}))"
    return f"What does this code print?\n\n{code}", str(result)


def _gen_function_fibonacci(rng: random.Random):
    n = rng.randint(2, 10)
    fibs = [0, 1]
    for _ in range(2, n + 1):
        fibs.append(fibs[-1] + fibs[-2])
    code = f"def fib(n):\n    if n <= 1:\n        return n\n    return fib(n - 1) + fib(n - 2)\n\nprint(fib({n}))"
    return f"What does this code print?\n\n{code}", str(fibs[n])


def _gen_variable_trace(rng: random.Random):
    a = rng.randint(1, 10)
    b = rng.randint(1, 10)
    c = a * b
    d = c + a
    code = f"a = {a}\nb = {b}\nc = a * b\nd = c + a\nprint(a, b, c, d)"
    return f"What does this code print?\n\n{code}", f"{a} {b} {c} {d}"


def _gen_string_count(rng: random.Random):
    s = "".join(rng.choices("ab", k=rng.randint(4, 10)))
    count_a = s.count("a")
    code = f"s = '{s}'\ncount = 0\nfor c in s:\n    if c == 'a':\n        count = count + 1\nprint(count)"
    return f"What does this code print?\n\n{code}", str(count_a)


def _gen_max_in_list(rng: random.Random):
    nums = [rng.randint(1, 50) for _ in range(rng.randint(3, 6))]
    result = max(nums)
    nums_str = str(nums)
    code = f"nums = {nums_str}\nmax_val = nums[0]\nfor n in nums:\n    if n > max_val:\n        max_val = n\nprint(max_val)"
    return f"What does this code print?\n\n{code}", str(result)


def _gen_sum_even(rng: random.Random):
    n = rng.randint(5, 15)
    total = sum(i for i in range(1, n + 1) if i % 2 == 0)
    code = f"total = 0\nfor i in range(1, {n + 1}):\n    if i % 2 == 0:\n        total = total + i\nprint(total)"
    return f"What does this code print?\n\n{code}", str(total)


def _gen_reverse_list(rng: random.Random):
    nums = [rng.randint(1, 20) for _ in range(rng.randint(3, 6))]
    result = nums[::-1]
    nums_str = str(nums)
    code = f"lst = {nums_str}\nreversed_lst = []\nfor i in range(len(lst) - 1, -1, -1):\n    reversed_lst.append(lst[i])\nprint(reversed_lst)"
    return f"What does this code print?\n\n{code}", str(result)


def _gen_is_palindrome(rng: random.Random):
    choice = rng.choice([1,2,3,4])
    if choice == 1:
        base = "".join(rng.choices("abc", k=rng.randint(2, 4)))
        s = base + base[::-1]
    elif choice == 2:
        base = "".join(rng.choices("abc", k=rng.randint(2, 4)))
        s = base + "x" + base[::-1]
    elif choice == 3:
        base = "".join(rng.choices("abc", k=rng.randint(2, 4)))
        s = base + "x" + base
    else:
        s = "".join(rng.choices("abc", k=rng.randint(2, 10)))
    result = str(s == s[::-1])
    code = f"s = '{s}'\nif s == s[::-1]:\n    print('True')\nelse:\n    print('False')"
    return f"What does this code print?\n\n{code}", result


def _gen_nested_loop_pattern(rng: random.Random):
    n = rng.randint(2, 5)
    total = sum(i * j for i in range(1, n + 1) for j in range(1, n + 1))
    code = f"total = 0\nfor i in range(1, {n + 1}):\n    for j in range(1, {n + 1}):\n        total = total + i * j\nprint(total)"
    return f"What does this code print?\n\n{code}", str(total)


def _gen_list_multiply(rng: random.Random):
    nums = [rng.randint(1, 10) for _ in range(rng.randint(3, 5))]
    result = [x * 2 for x in nums]
    nums_str = str(nums)
    code = f"nums = {nums_str}\ndoubled = [x * 2 for x in nums]\nprint(doubled)"
    return f"What does this code print?\n\n{code}", str(result)


def _gen_string_reverse(rng: random.Random):
    s = "".join(rng.choices("abcdef", k=rng.randint(3, 7)))
    result = s[::-1]
    code = f"s = '{s}'\nreversed_s = ''\nfor c in s:\n    reversed_s = c + reversed_s\nprint(reversed_s)"
    return f"What does this code print?\n\n{code}", result


def _gen_while_factorial(rng: random.Random):
    n = rng.randint(2, 8)
    result = 1
    for i in range(1, n + 1):
        result *= i
    code = f"n = {n}\nresult = 1\ni = 1\nwhile i <= n:\n    result = result * i\n    i = i + 1\nprint(result)"
    return f"What does this code print?\n\n{code}", str(result)


def _gen_conditional_chain(rng: random.Random):
    score = rng.randint(0, 100)
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    elif score >= 60:
        grade = "D"
    else:
        grade = "F"
    code = f"score = {score}\nif score >= 90:\n    print('A')\nelif score >= 80:\n    print('B')\nelif score >= 70:\n    print('C')\nelif score >= 60:\n    print('D')\nelse:\n    print('F')"
    return f"What does this code print?\n\n{code}", grade


def _gen_list_index(rng: random.Random):
    nums = [rng.randint(1, 20) for _ in range(rng.randint(4, 7))]
    idx = rng.randint(0, len(nums) - 1)
    code = f"lst = {nums}\nprint(lst[{idx}])"
    return f"What does this code print?\n\n{code}", str(nums[idx])


def _gen_list_length(rng: random.Random):
    n = rng.randint(3, 10)
    code = f"lst = list(range({n}))\nprint(len(lst))"
    return f"What does this code print?\n\n{code}", str(n)


def _gen_dict_keys(rng: random.Random):
    keys = sorted(rng.sample(["a", "b", "c", "d", "e"], 3))
    vals = [rng.randint(1, 20) for _ in range(3)]
    pairs = ", ".join(f"'{k}': {v}" for k, v in zip(keys, vals))
    code = f"d = {{{pairs}}}\nprint(sorted(d.keys()))"
    result = str(keys)
    return f"What does this code print?\n\n{code}", result


def _gen_absolute_value(rng: random.Random):
    x = rng.randint(-50, 50)
    code = f"x = {x}\nif x < 0:\n    x = -x\nprint(x)"
    return f"What does this code print?\n\n{code}", str(abs(x))


def _gen_counter(rng: random.Random):
    n = rng.randint(5, 15)
    evens = sum(1 for i in range(1, n + 1) if i % 2 == 0)
    odds = n - evens
    code = f"n = {n}\nevens = 0\nodds = 0\nfor i in range(1, n + 1):\n    if i % 2 == 0:\n        evens = evens + 1\n    else:\n        odds = odds + 1\nprint(evens, odds)"
    return f"What does this code print?\n\n{code}", f"{evens} {odds}"


def _gen_string_concat(rng: random.Random):
    parts = [rng.choice(["hello", "world", "foo", "bar"]) for _ in range(3)]
    result = "".join(parts)
    code_parts = [f"s1 = '{parts[0]}'", f"s2 = '{parts[1]}'", f"s3 = '{parts[2]}'", "result = s1 + s2 + s3", "print(result)"]
    code = "\n".join(code_parts)
    return f"What does this code print?\n\n{code}", result


def _gen_sum_digits(rng: random.Random):
    n = rng.randint(100, 9999)
    total = sum(int(d) for d in str(n))
    code = f"n = {n}\nsum_digits = 0\nwhile n > 0:\n    sum_digits = sum_digits + n % 10\n    n = n // 10\nprint(sum_digits)"
    return f"What does this code print?\n\n{code}", str(total)


def _gen_power_loop(rng: random.Random):
    base = rng.randint(2, 5)
    exp = rng.randint(1, 6)
    result = base ** exp
    code = f"base = {base}\nexp = {exp}\nresult = 1\nfor i in range(exp):\n    result = result * base\nprint(result)"
    return f"What does this code print?\n\n{code}", str(result)


def _gen_min_in_list(rng: random.Random):
    nums = [rng.randint(1, 50) for _ in range(rng.randint(3, 6))]
    result = min(nums)
    nums_str = str(nums)
    code = f"nums = {nums_str}\nmin_val = nums[0]\nfor n in nums:\n    if n < min_val:\n        min_val = n\nprint(min_val)"
    return f"What does this code print?\n\n{code}", str(result)


def _gen_filter_list(rng: random.Random):
    nums = [rng.randint(1, 30) for _ in range(rng.randint(5, 10))]
    threshold = rng.randint(5, 25)
    filtered = [x for x in nums if x > threshold]
    nums_str = str(nums)
    code = f"nums = {nums_str}\nresult = []\nfor n in nums:\n    if n > {threshold}:\n        result.append(n)\nprint(result)"
    return f"What does this code print?\n\n{code}", str(filtered)


def _gen_loop_else(rng: random.Random):
    n = rng.randint(5, 15)
    target = rng.randint(1, 4)
    found = False
    for i in range(1, n + 1):
        if i == target:
            found = True
            break
    result = "found" if found else "not found"
    code = f"for i in range(1, {n + 1}):\n    if i == {target}:\n        print('found')\n        break\nelse:\n    print('not found')"
    return f"What does this code print?\n\n{code}", result


def _gen_multiple_returns(rng: random.Random):
    a = rng.randint(1, 20)
    b = rng.randint(1, 20)
    code = f"def swap(x, y):\n    return y, x\n\na, b = swap({a}, {b})\nprint(a, b)"
    return f"What does this code print?\n\n{code}", f"{b} {a}"


def _gen_list_pop(rng: random.Random):
    nums = [rng.randint(1, 20) for _ in range(rng.randint(3, 6))]
    popped = nums[-1]
    remaining = nums[:-1]
    nums_str = str(nums)
    code = f"lst = {nums_str}\nremoved = lst.pop()\nprint(removed)\nprint(lst)"
    return f"What does this code print?\n\n{code}", f"{popped}\n{remaining}"


def _gen_default_dict(rng: random.Random):
    word = rng.choice(["hello", "world", "python", "code"])
    counts = {}
    for c in word:
        counts[c] = counts.get(c, 0) + 1
    result = str(counts)
    code = f"word = '{word}'\ncounts = {{}}\nfor c in word:\n    if c in counts:\n        counts[c] = counts[c] + 1\n    else:\n        counts[c] = 1\nprint(counts)"
    return f"What does this code print?\n\n{code}", result


def _gen_loop_accumulator(rng: random.Random):
    n = rng.randint(2, 8)
    total = 0
    for i in range(1, n + 1):
        total += i * i
    code = f"total = 0\nfor i in range(1, {n + 1}):\n    total += i * i\nprint(total)"
    return f"What does this code print?\n\n{code}", str(total)


def _gen_ternary(rng: random.Random):
    x = rng.randint(1, 50)
    threshold = rng.randint(1, 50)
    result = "big" if x > threshold else "small"
    code = f"x = {x}\nresult = 'big' if x > {threshold} else 'small'\nprint(result)"
    return f"What does this code print?\n\n{code}", result


def _gen_swap_with_temp(rng: random.Random):
    a = rng.randint(1, 50)
    b = rng.randint(1, 50)
    code = f"a = {a}\nb = {b}\ntemp = a\na = b\nb = temp\nprint(a, b)"
    return f"What does this code print?\n\n{code}", f"{b} {a}"


def _gen_while_divisible(rng: random.Random):
    n = rng.randint(20, 50)
    result = n
    while result % 2 == 0:
        result //= 2
    code = f"n = {n}\nwhile n % 2 == 0:\n    n = n // 2\nprint(n)"
    return f"What does this code print?\n\n{code}", str(result)


def _gen_list_sum(rng: random.Random):
    nums = [rng.randint(1, 20) for _ in range(rng.randint(3, 6))]
    total = sum(nums)
    nums_str = str(nums)
    code = f"nums = {nums_str}\ntotal = 0\nfor n in nums:\n    total = total + n\nprint(total)"
    return f"What does this code print?\n\n{code}", str(total)


def _gen_nested_condition(rng: random.Random):
    a = rng.randint(1, 30)
    b = rng.randint(1, 30)
    if a > b:
        result = f"{a} is bigger"
    elif b > a:
        result = f"{b} is bigger"
    else:
        result = "equal"
    code = f"a = {a}\nb = {b}\nif a > b:\n    print(f'{{a}} is bigger')\nelif b > a:\n    print(f'{{b}} is bigger')\nelse:\n    print('equal')"
    return f"What does this code print?\n\n{code}", result


def _gen_list_max_min(rng: random.Random):
    nums = [rng.randint(1, 50) for _ in range(rng.randint(4, 8))]
    code = f"nums = {nums}\nmax_val = max(nums)\nmin_val = min(nums)\nprint(max_val, min_val)"
    return f"What does this code print?\n\n{code}", f"{max(nums)} {min(nums)}"


GENERATORS = [
    _gen_simple_assignment,
    _gen_reassignment,
    _gen_swap,
    _gen_simple_if,
    _gen_nested_if,
    _gen_while_sum,
    _gen_while_count,
    _gen_for_range,
    _gen_nested_loop,
    _gen_loop_break,
    _gen_list_append,
    _gen_list_comprehension,
    _gen_dict_lookup,
    _gen_dict_update,
    _gen_string_format,
    _gen_string_slice,
    _gen_function_simple,
    _gen_function_recursive,
    _gen_function_fibonacci,
    _gen_variable_trace,
    _gen_string_count,
    _gen_max_in_list,
    _gen_sum_even,
    _gen_reverse_list,
    _gen_is_palindrome,
    _gen_nested_loop_pattern,
    _gen_list_multiply,
    _gen_string_reverse,
    _gen_while_factorial,
    _gen_conditional_chain,
    _gen_list_index,
    _gen_list_length,
    _gen_dict_keys,
    _gen_absolute_value,
    _gen_counter,
    _gen_string_concat,
    _gen_sum_digits,
    _gen_power_loop,
    _gen_min_in_list,
    _gen_filter_list,
    _gen_loop_else,
    _gen_multiple_returns,
    _gen_list_pop,
    _gen_default_dict,
    _gen_loop_accumulator,
    _gen_ternary,
    _gen_swap_with_temp,
    _gen_while_divisible,
    _gen_list_sum,
    _gen_nested_condition,
    _gen_list_max_min,
]


def _validate_sample(question: str, answer: str):
    code = '\n\n'.join(question.split('\n\n')[1:])
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        try:
            env = {}
            exec(code, env)
        except Exception as e:
            raise RuntimeError(f"Exception while executing:\n{code}\n\n{e}")
    output = buffer.getvalue()[:-1]
    assert output == answer, f"Code output doesn't match the answer:\nQuestion:\n{question}\nAnswer\n{list(answer)}\nCode output:\n{list(output)}"

def _make_sample(question: str, answer: str) -> list[chat_api.BaseItem]:

    _validate_sample(question, answer)

    return [
        chat_api.UserMessage(f"{question} Only include the answer in your response."),
        chat_api.AssistantMessage(text=answer),
    ]


def load(n: int = 1000, seed: int | None = 0) -> list[list[chat_api.BaseItem]]:
    rng = random.Random(seed)
    samples = []
    for _ in range(n):
        gen = rng.choice(GENERATORS)
        question, answer = gen(rng)
        samples.append(_make_sample(question, answer,))
    return samples
