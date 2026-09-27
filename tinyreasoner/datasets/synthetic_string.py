"""Should be correct, validated by Qwen3.7Plus."""
import random

from .. import chat_api


def _gen_reverse(rng: random.Random):
    s = _random_word(rng)
    return f"Reverse the string: \"{s}\"", s[::-1]


def _gen_uppercase(rng: random.Random):
    s = _random_phrase(rng)
    return f"Convert to uppercase: \"{s}\"", s.upper()


def _gen_lowercase(rng: random.Random):
    s = _random_phrase(rng)
    return f"Convert to lowercase: \"{s}\"", s.lower()


def _gen_length(rng: random.Random):
    s = _random_word(rng)
    return f"How many characters are in the string \"{s}\"?", str(len(s))


def _gen_count_vowels(rng: random.Random):
    s = _random_word(rng)
    count = sum(1 for c in s.lower() if c in "aeiou")
    return f"How many vowels are in \"{s}\"?", str(count)


def _gen_count_consonants(rng: random.Random):
    s = _random_word(rng)
    count = sum(1 for c in s.lower() if c.isalpha() and c not in "aeiou")
    return f"How many consonants are in \"{s}\"?", str(count)


def _gen_first_char(rng: random.Random):
    s = _random_word(rng)
    return f"What is the first character of \"{s}\"?", s[0]


def _gen_last_char(rng: random.Random):
    s = _random_word(rng)
    return f"What is the last character of \"{s}\"?", s[-1]


def _gen_middle_char(rng: random.Random):
    length = rng.choice([3, 5, 7, 9, 11])
    s = "".join(rng.choices("abcdefghijklmnopqrstuvwxyz", k=length))
    mid = s[length // 2]
    return f"What is the middle character of \"{s}\"? The string has {length} characters.", mid


def _gen_contains(rng: random.Random):
    s = _random_word(rng)
    idx = rng.randint(0, len(s) - 1)
    length = rng.randint(1, min(3, len(s) - idx))
    sub = s[idx:idx + length]
    answer = "yes" if rng.random() < 0.5 else "no"
    if answer == "no":
        sub = _random_word(rng)
        while sub in s:
            sub = _random_word(rng)
    return f"Does the string \"{s}\" contain the substring \"{sub}\"?", answer


def _gen_find_char(rng: random.Random):
    s = _random_word(rng)
    idx = rng.randint(0, len(s) - 1)
    c = s[idx]
    return f"What is the position (0-indexed) of the first occurrence of '{c}' in \"{s}\"?", str(s.index(c))


def _gen_replace(rng: random.Random):
    s = _random_word(rng)
    idx = rng.randint(0, len(s) - 1)
    old = s[idx]
    new = rng.choice([c for c in "abcdefghijklmnopqrstuvwxyz" if c != old])
    result = s[:idx] + new + s[idx + 1:]
    return f"Replace the character at index {idx} with '{new}' in \"{s}\". What is the result?", result


def _gen_remove_char(rng: random.Random):
    s = _random_word(rng)
    idx = rng.randint(0, len(s) - 1)
    c = s[idx]
    result = s.replace(c, "")
    return f"Remove all occurrences of '{c}' from \"{s}\". What is the result?", result


def _gen_substring(rng: random.Random):
    s = _random_word(rng)
    start = rng.randint(0, len(s) - 2)
    end = rng.randint(start + 1, len(s))
    return f"What is the substring of \"{s}\" from index {start} to {end} (exclusive)?", s[start:end]


def _gen_split_count(rng: random.Random):
    words = [_random_word(rng) for _ in range(rng.randint(2, 5))]
    s = " ".join(words)
    return f"How many words are in the string \"{s}\"?", str(len(words))


def _gen_palindrome(rng: random.Random):
    base = _random_word(rng, min_len=3, max_len=5)
    s = base + base[::-1]
    half = len(s) // 2
    return f"What is the first half of the palindrome \"{s}\"?", s[:half]


def _gen_char_frequency(rng: random.Random):
    s = _random_word(rng, min_len=3, max_len=8)
    target = rng.choice(list(set(s)))
    count = s.count(target)
    return f"How many times does the character '{target}' appear in \"{s}\"?", str(count)


def _gen_sort_chars(rng: random.Random):
    s = _random_word(rng, min_len=3, max_len=6)
    sorted_s = "".join(sorted(s))
    return f"Sort the characters in \"{s}\" alphabetically. What is the result?", sorted_s


def _gen_deduplicate(rng: random.Random):
    chars = [rng.choice("abcdef") for _ in range(rng.randint(4, 8))]
    s = "".join(chars)
    deduped = "".join(dict.fromkeys(s))
    return f"Remove duplicate characters from \"{s}\" (keep first occurrence). What is the result?", deduped


def _gen_repeat(rng: random.Random):
    s = _random_word(rng, min_len=1, max_len=4)
    n = rng.randint(2, 5)
    return f"Repeat the string \"{s}\" {n} times. What is the result?", s * n


def _gen_is_alpha(rng: random.Random):
    if rng.random() < 0.5:
        s = _random_word(rng)
        answer = "yes"
    else:
        s = _random_word(rng) + rng.choice(["123", "!", " "])
        answer = "no"
    return f"Does the string \"{s}\" contain only alphabetic characters?", answer


def _gen_is_numeric(rng: random.Random):
    if rng.random() < 0.5:
        s = "".join(rng.choices("0123456789", k=rng.randint(2, 6)))
        answer = "yes"
    else:
        s = "".join(rng.choices("0123456789", k=rng.randint(2, 6))) + rng.choice(["a", "!", "."])
        answer = "no"
    return f"Does the string \"{s}\" contain only numeric characters?", answer


def _gen_swap_case(rng: random.Random):
    s = _random_word(rng)
    result = s.swapcase()
    return f"Swap the case of each character in \"{s}\". What is the result?", result


def _gen_trim(rng: random.Random):
    s = _random_word(rng)
    padded = " " * rng.randint(1, 3) + s + " " * rng.randint(1, 3)
    return f"Remove leading and trailing spaces from \"{padded}\". What is the result?", s


def _gen_join_words(rng: random.Random):
    words = [_random_word(rng, min_len=2, max_len=5) for _ in range(rng.randint(2, 4))]
    separator = rng.choice(["-", "_", ",", " "])
    result = separator.join(words)
    return f"Join the words {words} using \"{separator}\" as separator. What is the result?", result


def _gen_startswith(rng: random.Random):
    s = _random_word(rng, min_len=4)
    prefix = s[:rng.randint(2, 3)]
    answer = "yes" if rng.random() < 0.7 else "no"
    if answer == "no":
        prefix = _random_word(rng, min_len=2, max_len=3)
        while s.startswith(prefix):
            prefix = _random_word(rng, min_len=2, max_len=3)
    return f"Does the string \"{s}\" start with \"{prefix}\"?", answer


def _gen_endswith(rng: random.Random):
    s = _random_word(rng, min_len=4)
    suffix = s[-rng.randint(2, 3):]
    answer = "yes" if rng.random() < 0.7 else "no"
    if answer == "no":
        suffix = _random_word(rng, min_len=2, max_len=3)
        while s.endswith(suffix):
            suffix = _random_word(rng, min_len=2, max_len=3)
    return f"Does the string \"{s}\" end with \"{suffix}\"?", answer


WORD_LIST = [
    "apple", "banana", "cherry", "delta", "eagle", "falcon", "grape", "harbor",
    "igloo", "jungle", "kettle", "lemon", "mango", "noble", "ocean", "piano",
    "quilt", "river", "stone", "tiger", "ultra", "vivid", "whale", "xenon",
    "yellow", "zebra", "amber", "blaze", "coral", "dusk", "ember", "flint",
    "glow", "haze", "ivory", "jade", "kite", "lava", "mist", "neon",
    "opal", "plum", "ruby", "sage", "tide", "vine", "wren", "yarn",
    "bolt", "crest", "dawn", "edge", "forge", "gale", "helm", "iron",
    "jazz", "knot", "lens", "moss", "noir", "onyx", "peak", "rift",
]


def _random_word(rng: random.Random, min_len: int = 3, max_len: int = 8) -> str:
    candidates = [w for w in WORD_LIST if min_len <= len(w) <= max_len]
    if not candidates:
        candidates = WORD_LIST
    return rng.choice(candidates)


def _random_phrase(rng: random.Random) -> str:
    n = rng.randint(2, 4)
    return " ".join(_random_word(rng) for _ in range(n))


GENERATORS = [
    _gen_reverse,
    _gen_uppercase,
    _gen_lowercase,
    _gen_length,
    _gen_count_vowels,
    _gen_count_consonants,
    _gen_first_char,
    _gen_last_char,
    _gen_middle_char,
    _gen_contains,
    _gen_find_char,
    _gen_replace,
    _gen_remove_char,
    _gen_substring,
    _gen_split_count,
    _gen_palindrome,
    _gen_char_frequency,
    _gen_sort_chars,
    _gen_deduplicate,
    _gen_repeat,
    _gen_is_alpha,
    _gen_is_numeric,
    _gen_swap_case,
    _gen_trim,
    _gen_join_words,
    _gen_startswith,
    _gen_endswith,
]


def _make_sample(question: str, answer: str) -> list[chat_api.BaseItem]:
    return [
        chat_api.UserMessage(f"{question} Only include the answer in your response."),
        chat_api.AssistantMessage(answer),
    ]


def load(n: int = 1000, seed: int | None = 0) -> list[list[chat_api.BaseItem]]:
    rng = random.Random(seed)
    samples = []
    for _ in range(n):
        gen = rng.choice(GENERATORS)
        question, answer = gen(rng)
        samples.append(_make_sample(question, answer))
    return samples
