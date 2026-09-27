import numpy as np
import math
import random
import string

from wonderwords import RandomSentence, RandomWord

from .. import chat_api

_random_word = RandomWord()
_random_sent = RandomSentence()
import sympy


def _random_string():
    if random.random() < 0.5:
        if random.random() > 0.5: return _random_word.word()
        n = random.randint(1, 4)
        return random.choice(['', ' ']).join(_random_word.word() for _ in range(n))

    if random.random() < 0.1:
        choice = random.choice([1,2,3,4])
        if choice == 1: return _random_sent.sentence()
        if choice == 2: return _random_sent.simple_sentence()
        if choice == 2: return _random_sent.bare_bone_sentence()
        if choice == 2: return _random_sent.bare_bone_with_adjective()

    length = random.randint(1, 32)
    chars = ""
    if random.random() < 0.5: chars = chars + string.ascii_lowercase
    if random.random() < 0.5: chars = chars + string.ascii_uppercase
    if random.random() < 0.5: chars = chars + string.digits
    if random.random() < 0.5: chars = chars + " "
    if random.random() < 0.5: chars = chars + "."
    if random.random() < 0.5: chars = chars + ","
    if random.random() < 0.5: chars = chars + "!"
    if random.random() < 0.5: chars = chars + "?"
    if random.random() < 0.5: chars = chars + _random_word.word()
    if len(chars) == 0 or chars == " ":
        chars = _random_word.word()

    return ''.join(random.choices(list(set(chars)), k=length))

_eq_chars = ("="," = ")
def _generate_add():
    x = random.randint(-10_000, 10_000)
    y = random.randint(-10_000, 10_000)
    return f"{x}{random.choice(['+',' + '])}{y}{random.choice(_eq_chars)}?", x+y

def _generate_sub():
    x = random.randint(-10_000, 10_000)
    y = random.randint(-10_000, 10_000)
    return f"{x} - {y}{random.choice(_eq_chars)}?", x-y

def _generate_mul():
    x = random.randint(-100, 100)
    y = random.randint(-100, 100)
    mul_char = random.choice(["*", "×", " * ", " × "])
    return f"{x}{mul_char}{y}{random.choice(_eq_chars)}?", x*y

def _generate_div():
    z = random.randint(-100, 100)
    y = random.randint(-100, 100)
    if y == 0: y = random.randint(1,1000)
    x = z * y
    div_char = random.choice(["/", "÷", " / ", " ÷ "])
    return f"{x}{div_char}{y}{random.choice(_eq_chars)}?", z

def _generate_pow():
    base = random.randint(-10, 10)
    exp = random.randint(0, 10)
    if base == 0 and exp == 0:
        base = 1

    pow_char = random.choice(["^", "**", " ^ ", " ** "])
    if base < 0: return f"({base}){pow_char}{exp}{random.choice(_eq_chars)}?", base ** exp
    return f"{base}{pow_char}{exp}{random.choice(_eq_chars)}?", base ** exp

def _generate_gt():
    x = random.randint(-10_000, 10_000)
    if random.random() > 0.5:
        y = random.randint(-10_000, 10_000)
    else:
        y = x
    return f"{x}{random.choice(['>', ' > '])}{y}? (true or false)", str(x>y).lower()

def _generate_ge():
    x = random.randint(-10_000, 10_000)
    if random.random() > 0.5:
        y = random.randint(-10_000, 10_000)
    else:
        y = x
    return f"{x}{random.choice(['>=', ' >= '])}{y}? (true or false)", str(x>=y).lower()

def _generate_lt():
    x = random.randint(-10_000, 10_000)
    if random.random() > 0.5:
        y = random.randint(-10_000, 10_000)
    else:
        y = x
    return f"{x}{random.choice(['<', ' < '])}{y}? (true or false)", str(x<y).lower()

def _generate_le():
    x = random.randint(-10_000, 10_000)
    x = random.randint(-10_000, 10_000)
    if random.random() > 0.5:
        y = random.randint(-10_000, 10_000)
    else:
        y = x
    return f"{x}{random.choice(['<=', ' <= '])}{y}? (true or false)", str(x<=y).lower()

def _generate_eq():
    x = random.randint(-10_000, 10_000)
    x = random.randint(-10_000, 10_000)
    if random.random() > 0.5:
        y = random.randint(-10_000, 10_000)
    else:
        y = x
    eq_char = random.choice(["=","==", " = ", " == "])
    return f"{x}{eq_char}{y}? (true or false)", str(x==y).lower()

def _generate_neq():
    x = random.randint(-10_000, 10_000)
    x = random.randint(-10_000, 10_000)
    if random.random() > 0.5:
        y = random.randint(-10_000, 10_000)
    else:
        y = x
    neq_char = random.choice(["!=", " != "])
    return f"{x}{neq_char}{y}? (true or false)", str(x!=y).lower()


def _generate_string_length():
    s = _random_string()
    return f'what is the length of string "{s}"', len(s)

def _generate_n_unique():
    s = _random_string()
    return f'how many unique characters are in string "{s}"', len(set(s))

def _generate_specific_char_count():
    s = _random_string()
    if random.random() > 0.5:
        c = random.choice(s)
    else:
        c = random.choice(string.ascii_letters + string.digits)
    count = s.count(c)
    return f'count number of occurences of "{c}" in string "{s}"', count

def _generate_remove_char():
    s = _random_string()
    if random.random() > 0.5:
        c = random.choice(s)
    else:
        c = random.choice(string.ascii_letters + string.digits)
    s_proc = ''.join(char for char in s if char != c)
    return f'remove all occurences of character "{c}" from string "{s}"', f'"{s_proc}"'

def _generate_replace_char():
    s = _random_string()
    if random.random() > 0.5:
        c_old = random.choice(s)
    else:
        c_old = random.choice(string.ascii_letters + string.digits)
    c_new = random.choice(string.ascii_letters + string.digits)
    s_new = s.replace(c_old,c_new)
    return f'replace all occurences of character "{c_old}" with "{c_new}" in string "{s}"', f'"{s_new}"'

_filters = {
    "lowercase letters": str.islower,
    "uppercase letters": str.isupper,
    "alphabetic characters": str.isalpha,
    "numeric characters": str.isnumeric,
}
def _generate_count_filter():
    s = _random_string()
    filter_name = random.choice(list(_filters.keys()))
    filter_fn = _filters[filter_name]
    n_filter = sum(1 for c in s if filter_fn(c))
    return f'how many occurences of {filter_name} are in string "{s}"', n_filter

def _generate_unique_count_filter():
    s = _random_string()
    filter_name = random.choice(list(_filters.keys()))
    filter_fn = _filters[filter_name]
    s_filter = [c for c in s if filter_fn(c)]
    return f'how many unique {filter_name} are in string "{s}"', len(s_filter)

def _generate_missing_chars():
    s = _random_string()
    filter_name = random.choice(["lowercase letters", "uppercase letters", "numeric characters"])
    filter_fn = _filters[filter_name]

    valid = [c for c in string.ascii_letters + string.digits if filter_fn(c)]
    s_filter = [c for c in s if filter_fn(c)]
    missing = set(valid).difference(set(s_filter))

    char_name = {
        "lowercase letters": "lowercase english characters",
        "uppercase letters": "uppercase english characters",
        "alphabetic characters": "english letters",
        "numeric characters": "digit characters",
    }[filter_name]

    return f'how many unique {char_name} are there that are not in string "{s}"', len(missing)

def _generate_filter_chars():
    s = _random_string()
    filter_name = random.choice(list(_filters.keys()))
    filter_fn = _filters[filter_name]
    s_filt = ''.join(c for c in s if filter_fn(c))
    return f'keep only {filter_name} in the string "{s}"', f'"{s_filt}"'

def _generate_remove_filter_chars():
    s = _random_string()
    filter_name = random.choice(list(_filters.keys()))
    filter_fn = _filters[filter_name]
    s_filt = ''.join(c for c in s if not filter_fn(c))
    return f'remove all {filter_name} from the string "{s}"', f'"{s_filt}"'

def _generate_union_chars():
    s1 = _random_string()
    s2 = _random_string()
    s1_filt = ''.join(c for c in s1 if c in s2)
    return f'remove all characters from the string "{s1}" that are not present in string "{s2}"', f'"{s1_filt}"'

def _generate_difference_chars():
    s1 = _random_string()
    s2 = _random_string()
    s1_filt = ''.join(c for c in s1 if c not in s2)
    return f'remove all characters from the string "{s1}" that are present in string "{s2}"', f'"{s1_filt}"'

def _generate_reverse():
    s = _random_string()
    return f'reverse string "{s}"', f'"{"".join(reversed(s))}"'

def _generate_index():
    s = _random_string()
    idx = random.randrange(0, len(s))
    return f'"what character has index {idx} (0-indexed) in string "{s}"', f'"{s[idx]}"'

def _generate_find():
    s = _random_string()
    c = random.choice(s)
    idx = s.index(c)
    return f'"what index (0-indexed) does the first occurence of character "{c}" have in string "{s}"', idx

def _generate_rfind():
    s = _random_string()
    c = random.choice(s)
    idx = s.rindex(c)
    return f'"what index (0-indexed) does the last occurence of character "{c}" have in string "{s}"', idx

def _generate_sort():
    numbers = [random.randint(-1_000_000,1_000_000) for _ in range(random.randint(1,10))]

    numers_s = ', '.join(str(n) for n in numbers)
    return f'sort {numers_s} in ascending order', ', '.join(str(n) for n in sorted(numbers))

def _generate_sort_descending():
    numbers = [random.randint(-1_000_000,1_000_000) for _ in range(random.randint(1,10))]

    numers_s = ', '.join(str(n) for n in numbers)
    return f'sort {numers_s} in descending order', ', '.join(str(n) for n in sorted(numbers, reverse=True))


def _generate_sum():
    numbers = [random.randint(-99,99) for _ in range(random.randint(1,10))]
    return f'what is the sum of those numbers: {", ".join(str(n) for n in numbers)}', sum(numbers)

def _generate_prod():
    numbers = [random.randint(-9,9) for _ in range(random.randint(1,10))]
    return f'what is the product of those numbers: {", ".join(str(n) for n in numbers)}', math.prod(numbers)

def _generate_max():
    numbers = [random.randint(-1_000_000,1_000_000) for _ in range(random.randint(1,10))]
    return f'what is the maximum of those numbers: {", ".join(str(n) for n in numbers)}', max(numbers)

def _generate_min():
    numbers = [random.randint(-1_000_000,1_000_000) for _ in range(random.randint(1,10))]
    return f'what is the minimum of those numbers: {", ".join(str(n) for n in numbers)}', min(numbers)

def _generate_max_abs():
    numbers = [random.randint(-1_000_000,1_000_000) for _ in range(random.randint(1,10))]
    return f'what is the maximum absolute value of those numbers: {", ".join(str(n) for n in numbers)}', max(abs(n) for n in numbers)

def _generate_min_abs():
    numbers = [random.randint(-1_000_000,1_000_000) for _ in range(random.randint(1,10))]
    return f'what is the minimum absolute value of those numbers: {", ".join(str(n) for n in numbers)}', min(abs(n) for n in numbers)

def _generate_number_count():
    numbers = [random.randint(-1_000_000,1_000_000) for _ in range(random.randint(1,10))]
    return f'how many numbers are there: {", ".join(str(n) for n in numbers)}', len(numbers)

def _generate_unique_number_count():
    numbers = [random.randint(-10,10) for _ in range(random.randint(1,20))]
    return f'how many unique numbers are there: {", ".join(str(n) for n in numbers)}', len(set(numbers))


def _generate_convert_base():
    x = random.randint(-100, 100)
    base1 = random.randint(2, 36)
    base2 = random.randint(2, 36)
    x_base1 = np.base_repr(x, base=base1)
    x_base2 = np.base_repr(x, base=base2)
    return f'convert {x_base1} from base-{base1} to base-{base2}', x_base2

_generators = [
    _generate_add,
    _generate_sub,
    _generate_mul,
    _generate_div,
    _generate_pow,
    _generate_gt,
    _generate_ge,
    _generate_lt,
    _generate_le,
    _generate_eq,
    _generate_neq,
    _generate_string_length,
    _generate_n_unique,
    _generate_specific_char_count,
    _generate_remove_char,
    _generate_replace_char,
    _generate_count_filter,
    _generate_unique_count_filter,
    _generate_missing_chars,
    _generate_filter_chars,
    _generate_remove_filter_chars,
    _generate_union_chars,
    _generate_difference_chars,
    _generate_reverse,
    _generate_index,
    _generate_find,
    _generate_rfind,
    _generate_sort,
    _generate_sort_descending,
    _generate_sum,
    _generate_prod,
    _generate_max,
    _generate_min,
    _generate_max_abs,
    _generate_min_abs,
    _generate_number_count,
    _generate_unique_number_count,
    _generate_convert_base,
]

def _create_chat(qa:tuple[str,str]):
    q,a = qa
    return [chat_api.UserMessage(f"{q}\nonly include the answer in your response"), chat_api.AssistantMessage(f"{a}")]

def load(n: int = 1000, seed=None):
    if seed is not None: raise NotImplementedError
    samples = [_create_chat(random.choice(_generators)()) for _ in range(n)]
    return samples
