"""Should be correct, validated by Qwen3.7Plus."""

import random
import itertools

from .. import chat_api


def _gen_modus_ponens(rng: random.Random):
    a = rng.choice(["sunny", "raining", "snowing", "cloudy", "windy"])
    b = rng.choice(["hot", "cold", "wet", "dry", "warm"])
    return (
        f"If it is {a}, then it is {b}. It is {a}. Is it {b}?",
        "yes",
    )


def _gen_modus_tollens(rng: random.Random):
    a = rng.choice(["sunny", "raining", "snowing", "cloudy"])
    b = rng.choice(["hot", "cold", "wet", "dry"])
    return (
        f"If it is {a}, then it is {b}. It is not {b}. Is it {a}?",
        "no",
    )


def _gen_hypothetical_syllogism(rng: random.Random):
    chain = rng.choice([
        ("sunny", "warm", "happy"),
        ("raining", "wet", "cold"),
        ("early", "tired", "grumpy"),
        ("studying", "learning", "smart"),
        ("running", "sweating", "tired"),
    ])
    a, b, c = chain
    return (
        f"If it is {a}, then it is {b}. If it is {b}, then it is {c}. It is {a}. Is it {c}?",
        "yes",
    )


def _gen_chain_negation(rng: random.Random):
    chain = rng.choice([
        ("sunny", "warm", "happy"),
        ("raining", "wet", "cold"),
        ("early", "tired", "grumpy"),
        ("studying", "learning", "smart"),
    ])
    a, b, c = chain
    return (
        f"If it is {a}, then it is {b}. If it is {b}, then it is {c}. It is not {c}. Is it {a}?",
        "no",
    )


def _gen_disjunctive_syllogism(rng: random.Random):
    a = rng.choice(["apple", "banana", "cherry", "grape"])
    b = rng.choice(["red", "yellow", "purple", "green"])
    return (
        f"It is either {a} or {b}. It is not {a}. Is it {b}?",
        "yes",
    )


def _gen_conjunction(rng: random.Random):
    verb1 = rng.choice(["like", "chase", "eat"])
    verb2 = rng.choice(["like", "chase", "eat"])
    return (
        f"Cats {verb1} fish and cats {verb2} birds. Do cats {verb1} fish and {verb2} birds?",
        "yes",
    )


def _gen_disjunction(rng: random.Random):
    x = rng.randint(1, 50)
    y = rng.randint(1, 50)
    threshold = rng.randint(20, 80)
    x_above = x > threshold
    y_above = y > threshold
    return (
        f"Is {x} > {threshold} OR is {y} > {threshold}?",
        "yes" if x_above or y_above else "no",
    )


def _gen_negation(rng: random.Random):
    x = rng.randint(1, 100)
    is_even = x % 2 == 0
    return (
        f"Is it true that {x} is NOT {'even' if is_even else 'odd'}?",
        "no",
    )


def _gen_xor(rng: random.Random):
    x = rng.randint(1, 50)
    y = rng.randint(1, 50)
    x_even = x % 2 == 0
    y_even = y % 2 == 0
    xor = x_even != y_even
    return (
        f"Exactly one of these is true: {x} is even, {y} is even. Is this statement true?",
        "yes" if xor else "no",
    )


def _gen_biconditional(rng: random.Random):
    a = rng.choice(["sunny", "raining", "snowing"])
    b = rng.choice(["warm", "cold", "wet"])
    both_true = rng.random() < 0.5
    if both_true:
        return (
            f"It is {a} if and only if it is {b}. It is {a}. Is it {b}?",
            "yes",
        )
    else:
        return (
            f"It is {a} if and only if it is {b}. It is not {a}. Is it {b}?",
            "no",
        )


def _gen_transitivity_ordering(rng: random.Random):
    names = rng.sample(["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"], 3)
    n1, n2, n3 = names
    rel = rng.choice(["taller", "heavier", "older", "faster"])
    superlative = {"taller": "tallest", "heavier": "heaviest", "older": "oldest", "faster": "fastest"}[rel]
    return (
        f"{n1} is {rel} than {n2}. {n2} is {rel} than {n3}. Who is the {superlative}?",
        n1,
    )


def _gen_transitivity_simple(rng: random.Random):
    names = rng.sample(["Alice", "Bob", "Charlie", "Diana"], 3)
    n1, n2, n3 = names
    rel = rng.choice(["taller", "heavier", "older"])
    rel_base = {"taller": "tall", "heavier": "heavy", "older": "old"}[rel]
    return (
        f"{n1} is {rel} than {n2}. {n2} is {rel} than {n3}. Who is the least {rel_base}?",
        n3,
    )


def _gen_sequencing(rng: random.Random):
    sequences = [
        ([1, 2, 4, 8], 16, "powers of 2"),
        ([1, 3, 5, 7], 9, "odd numbers"),
        ([2, 4, 6, 8], 10, "even numbers"),
        ([1, 1, 2, 3], 5, "Fibonacci"),
        ([3, 6, 9, 12], 15, "multiples of 3"),
        ([1, 4, 9, 16], 25, "squares"),
        ([1, 8, 27, 64], 125, "cubes"),
        ([2, 6, 18, 54], 162, "powers of 3 times 2"),
        ([5, 10, 15, 20], 25, "multiples of 5"),
        ([10, 20, 40, 80], 160, "doubling"),
    ]
    seq, answer, _ = rng.choice(sequences)
    seq_str = ", ".join(str(x) for x in seq)
    return (
        f"What comes next in the sequence: {seq_str}, ...?",
        str(answer),
    )


def _gen_pattern_next(rng: random.Random):
    a = rng.randint(1, 20)
    d = rng.randint(2, 10)
    seq = [a + i * d for i in range(4)]
    next_val = a + 4 * d
    seq_str = ", ".join(str(x) for x in seq)
    return (
        f"What comes next in the sequence: {seq_str}, ...?",
        str(next_val),
    )


def _gen_count_true_statements(rng: random.Random):
    statements = []
    for _ in range(3):
        x = rng.randint(1, 20)
        y = rng.randint(1, 20)
        op = rng.choice([">", "<", "=="])
        if op == ">":
            result = x > y
            stmt = f"{x} > {y}"
        elif op == "<":
            result = x < y
            stmt = f"{x} < {y}"
        else:
            result = x == y
            stmt = f"{x} == {y}"
        statements.append((stmt, result))
    count = sum(1 for _, r in statements if r)
    stmts_str = ", ".join(s for s, _ in statements)
    return (
        f"How many of these are true: {stmts_str}?",
        str(count),
    )


def _gen_set_intersection(rng: random.Random):
    set_a = set(rng.sample(range(1, 20), rng.randint(3, 6)))
    set_b = set(rng.sample(range(1, 20), rng.randint(3, 6)))
    intersection = set_a & set_b
    a_str = ", ".join(str(x) for x in sorted(set_a))
    b_str = ", ".join(str(x) for x in sorted(set_b))
    return (
        f"Set A = {{{a_str}}}. Set B = {{{b_str}}}. How many elements are in the intersection of A and B?",
        str(len(intersection)),
    )


def _gen_set_union(rng: random.Random):
    set_a = set(rng.sample(range(1, 20), rng.randint(3, 5)))
    set_b = set(rng.sample(range(1, 20), rng.randint(3, 5)))
    union = set_a | set_b
    a_str = ", ".join(str(x) for x in sorted(set_a))
    b_str = ", ".join(str(x) for x in sorted(set_b))
    return (
        f"Set A = {{{a_str}}}. Set B = {{{b_str}}}. How many elements are in the union of A and B?",
        str(len(union)),
    )


def _gen_set_difference(rng: random.Random):
    set_a = set(rng.sample(range(1, 20), rng.randint(4, 7)))
    set_b = set(rng.sample(range(1, 20), rng.randint(2, 4)))
    diff = set_a - set_b
    a_str = ", ".join(str(x) for x in sorted(set_a))
    b_str = ", ".join(str(x) for x in sorted(set_b))
    return (
        f"Set A = {{{a_str}}}. Set B = {{{b_str}}}. How many elements are in A but not in B?",
        str(len(diff)),
    )


def _gen_set_subset(rng: random.Random):
    set_a = set(rng.sample(range(1, 20), rng.randint(3, 6)))
    subset_size = rng.randint(2, len(set_a))
    set_b = set(rng.sample(sorted(set_a), subset_size))
    a_str = ", ".join(str(x) for x in sorted(set_a))
    b_str = ", ".join(str(x) for x in sorted(set_b))
    return (
        f"Set A = {{{a_str}}}. Set B = {{{b_str}}}. Is B a subset of A?",
        "yes",
    )


def _gen_set_not_subset(rng: random.Random):
    set_a = set(rng.sample(range(1, 15), rng.randint(3, 5)))
    extra = [x for x in range(1, 20) if x not in set_a]
    set_b = set(rng.sample(sorted(set_a), rng.randint(2, len(set_a)))) | {rng.choice(extra)}
    a_str = ", ".join(str(x) for x in sorted(set_a))
    b_str = ", ".join(str(x) for x in sorted(set_b))
    return (
        f"Set A = {{{a_str}}}. Set B = {{{b_str}}}. Is B a subset of A?",
        "no",
    )


def _gen_binary_and(rng: random.Random):
    a = rng.choice([0, 1])
    b = rng.choice([0, 1])
    return (
        f"What is {a} AND {b}?",
        str(a & b),
    )


def _gen_binary_or(rng: random.Random):
    a = rng.choice([0, 1])
    b = rng.choice([0, 1])
    return (
        f"What is {a} OR {b}?",
        str(a | b),
    )


def _gen_binary_not(rng: random.Random):
    a = rng.choice([0, 1])
    return (
        f"What is NOT {a}?",
        str(1 - a),
    )


def _gen_binary_xor(rng: random.Random):
    a = rng.choice([0, 1])
    b = rng.choice([0, 1])
    return (
        f"What is {a} XOR {b}?",
        str(a ^ b),
    )


def _gen_if_then_true(rng: random.Random):
    x = rng.randint(1, 50)
    return (
        f"If {x} > 0, then the answer is yes. Is {x} > 0?",
        "yes",
    )


def _gen_if_then_false(rng: random.Random):
    x = rng.randint(1, 50)
    return (
        f"If {x} > 100, then the answer is yes. Is {x} > 100?",
        "no",
    )



def _gen_counting_combinations(rng: random.Random):
    n = rng.randint(3, 6)
    k = rng.randint(2, n)
    from math import comb
    return (
        f"How many ways can you choose {k} items from {n} items?",
        str(comb(n, k)),
    )


def _gen_counting_permutations(rng: random.Random):
    n = rng.randint(3, 6)
    from math import perm
    return (
        f"How many ways can you arrange {n} distinct items?",
        str(perm(n, n)),
    )


def _gen_clock_angle(rng: random.Random):
    hour = rng.randint(1, 12)
    minute = rng.choice([0, 15, 30, 45])
    hour_angle = (hour % 12) * 30 + minute * 0.5
    minute_angle = minute * 6
    angle = abs(hour_angle - minute_angle)
    angle = min(angle, 360 - angle)
    minute_str = f"{minute:02d}"
    return (
        f"What is the smaller angle between the hour and minute hands at {hour}:{minute_str}?",
        str(f"{angle:g}"),
    )


def _gen_day_of_week(rng: random.Random):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    start = rng.randint(0, 6)
    offset = rng.randint(1, 10)
    result = (start + offset) % 7
    return (
        f"If today is {days[start]}, what day is it in {offset} days?",
        days[result],
    )


def _gen_truth_table(rng: random.Random):
    ops = [
        ("AND", lambda a, b: a and b),
        ("OR", lambda a, b: a or b),
        ("XOR", lambda a, b: a != b),
    ]
    op_name, op_fn = rng.choice(ops)
    a = rng.choice([True, False])
    b = rng.choice([True, False])
    result = op_fn(a, b)
    return (
        f"What is {str(a).lower()} {op_name} {str(b).lower()}?",
        str(result).lower(),
    )


def _gen_either_or(rng: random.Random):
    items = [
        ("cat", "dog", "pet"),
        ("red", "blue", "color"),
        ("apple", "banana", "fruit"),
        ("sun", "moon", "celestial body"),
    ]
    a, b, category = rng.choice(items)
    return (
        f"Is it true that every {category} is either a {a} or a {b}?",
        "no",
    )


def _gen_either_or_true(rng: random.Random):
    x = rng.randint(1, 20)
    y = rng.randint(1, 20)
    return (
        f"Is it true that either {x} is odd or {y} is even?",
        "yes" if x % 2 == 1 or y % 2 == 0 else "no",
    )


def _gen_deduction_simple(rng: random.Random):
    facts = [
        ("All cats are animals. Whiskers is a cat. Is Whiskers an animal?", "yes"),
        ("All dogs are animals. Rex is a dog. Is Rex an animal?", "yes"),
        ("All birds can fly. Tweety is a bird. Can Tweety fly?", "yes"),
        ("All fish swim. Nemo is a fish. Does Nemo swim?", "yes"),
        ("All roses are flowers. Red Rose is a rose. Is Red Rose a flower?", "yes"),
        ("All squares have 4 sides. Shape X is a square. Does Shape X have 4 sides?", "yes"),
    ]
    return rng.choice(facts)


def _gen_deduction_negation(rng: random.Random):
    facts = [
        ("No cats are dogs. Whiskers is a cat. Is Whiskers a dog?", "no"),
        ("No birds are fish. Tweety is a bird. Is Tweety a fish?", "no"),
        ("No stones are alive. Rocky is a stone. Is Rocky alive?", "no"),
    ]
    return rng.choice(facts)


def _gen_counting(rng: random.Random):
    a = rng.randint(1, 50)
    b = rng.randint(a + 1, a + 30)
    return (
        f"How many integers are strictly between {a} and {b}?",
        str(b - a - 1),
    )


def _gen_majority(rng: random.Random):
    n_true = rng.randint(3, 8)
    n_false = rng.randint(1, n_true - 1)
    total = n_true + n_false
    return (
        f"In a group of {total} people, {n_true} say yes and {n_false} say no. Do the majority say yes?",
        "yes",
    )


def _gen_majority_no(rng: random.Random):
    n_true = rng.randint(1, 3)
    n_false = rng.randint(n_true + 1, n_true + 5)
    total = n_true + n_false
    return (
        f"In a group of {total} people, {n_true} say yes and {n_false} say no. Do the majority say yes?",
        "no",
    )


def _gen_absurdity(rng: random.Random):
    a = rng.choice(["cat", "dog", "bird", "fish", "horse"])
    b = rng.choice(["fly", "swim", "drive a car", "speak French", "play piano"])
    can_do = {
        "cat": ["swim"],
        "dog": ["swim"],
        "bird": ["fly", "swim"],
        "fish": ["swim"],
        "horse": ["swim"],
    }
    return (
        f"Can a {a} {b}?",
        "yes" if b in can_do.get(a, []) else "no",
    )


def _gen_absurdity_two(rng: random.Random):
    x = rng.randint(1, 20)
    return (
        f"Is {x} both greater than {x + 10} and less than {x - 5}?",
        "no",
    )


def _gen_comparisons(rng: random.Random):
    x = rng.randint(1, 50)
    y = rng.randint(1, 50)
    return (
        f"Is {x} equal to {y}?",
        "yes" if x == y else "no",
    )


def _gen_comparisons_gt(rng: random.Random):
    x = rng.randint(1, 50)
    y = rng.randint(1, 50)
    return (
        f"Is {x} greater than {y}?",
        "yes" if x > y else "no",
    )


def _gen_comparisons_lt(rng: random.Random):
    x = rng.randint(1, 50)
    y = rng.randint(1, 50)
    return (
        f"Is {x} less than {y}?",
        "yes" if x < y else "no",
    )


def _gen_divisibility(rng: random.Random):
    divisor = rng.choice([2, 3, 5, 7])
    quotient = rng.randint(1, 30)
    x = divisor * quotient
    return (
        f"Is {x} divisible by {divisor}?",
        "yes",
    )


def _gen_divisibility_no(rng: random.Random):
    divisor = rng.choice([3, 5, 7])
    x = rng.randint(1, 100)
    while x % divisor == 0:
        x = rng.randint(1, 100)
    return (
        f"Is {x} divisible by {divisor}?",
        "no",
    )


def _gen_positive_negative(rng: random.Random):
    x = rng.randint(-50, 50)
    return (
        f"Is {x} positive?",
        "yes" if x > 0 else "no",
    )


def _gen_odd_even(rng: random.Random):
    x = rng.randint(1, 100)
    return (
        f"Is {x} odd?",
        "yes" if x % 2 == 1 else "no",
    )


def _gen_between(rng: random.Random):
    a = rng.randint(1, 30)
    b = a + rng.randint(5, 20)
    x = rng.randint(a, b)
    return (
        f"Is {x} between {a} and {b} (inclusive)?",
        "yes",
    )


def _gen_between_no(rng: random.Random):
    a = rng.randint(2, 30)
    b = a + rng.randint(5, 20)
    x = rng.choice([rng.randint(1, a - 1), rng.randint(b + 1, b + 10)])
    return (
        f"Is {x} between {a} and {b} (inclusive)?",
        "no",
    )


def _gen_power_of_two(rng: random.Random):
    exp = rng.randint(0, 10)
    x = 2 ** exp
    return (
        f"Is {x} a power of 2?",
        "yes",
    )


def _gen_power_of_two_no(rng: random.Random):
    x = rng.choice([3, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20])
    return (
        f"Is {x} a power of 2?",
        "no",
    )


def _gen_prime(rng: random.Random):
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
    p = rng.choice(primes)
    return (
        f"Is {p} a prime number?",
        "yes",
    )


def _gen_not_prime(rng: random.Random):
    x = rng.choice([4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 21, 22, 24, 25, 26, 27, 28, 30])
    return (
        f"Is {x} a prime number?",
        "no",
    )


def _gen_syllogism(rng: random.Random):
    syllogisms = [
        ("All cats are mammals. All mammals are animals. Are all cats animals?", "yes"),
        ("All dogs are mammals. All mammals are animals. Are all dogs animals?", "yes"),
        ("All roses are plants. All plants need water. Do roses need water?", "yes"),
        ("All squares are rectangles. All rectangles have 4 sides. Do squares have 4 sides?", "yes"),
        ("All fish live in water. All things that live in water get wet. Do fish get wet?", "yes"),
    ]
    return rng.choice(syllogisms)


def _gen_logic_puzzle(rng: random.Random):
    names = rng.sample(["Alice", "Bob", "Charlie"], 2)
    n1, n2 = names
    item = rng.choice(["apple", "book", "ball", "cup"])
    return (
        f"{n1} has a {item}. {n2} does not have a {item}. Who has the {item}?",
        n1,
    )


def _gen_relatives(rng: random.Random):
    names = rng.sample(["Alice", "Bob", "Charlie", "Diana"], 3)
    n1, n2, n3 = names
    return (
        f"{n1} is the mother of {n2}. {n2} is the sister of {n3}. Who is the mother of {n3}?",
        n1,
    )


def _gen_not_relatives(rng: random.Random):
    names = rng.sample(["Alice", "Bob", "Charlie", "Diana"], 3)
    n1, n2, n3 = names
    return (
        f"{n1} is the father of {n2}. {n2} is the brother of {n3}. Is {n1} the father of {n3}?",
        "yes",
    )


def _gen_max_min(rng: random.Random):
    nums = [rng.randint(1, 50) for _ in range(3)]
    nums_str = ", ".join(str(n) for n in nums)
    return (
        f"What is the largest number among {nums_str}?",
        str(max(nums)),
    )


def _gen_min(rng: random.Random):
    nums = [rng.randint(1, 50) for _ in range(3)]
    nums_str = ", ".join(str(n) for n in nums)
    return (
        f"What is the smallest number among {nums_str}?",
        str(min(nums)),
    )


def _gen_sum_compare(rng: random.Random):
    a = rng.randint(1, 30)
    b = rng.randint(1, 30)
    return (
        f"Is {a} + {b} > {a} * {b}?",
        "yes" if a + b > a * b else "no",
    )


def _gen_product_compare(rng: random.Random):
    a = rng.randint(1, 10)
    b = rng.randint(1, 10)
    return (
        f"Is {a} * {b} > {a} + {b}?",
        "yes" if a * b > a + b else "no",
    )


def _gen_absolute(rng: random.Random):
    x = rng.randint(-50, 50)
    return (
        f"What is the absolute value of {x}?",
        str(abs(x)),
    )


def _gen_negation_of_statement(rng: random.Random):
    x = rng.randint(1, 20)
    y = rng.randint(1, 20)
    gt = x > y
    return (
        f'If "{x} > {y}" is {"true" if gt else "false"}, is the negation true?',
        "no" if gt else "yes",
    )


def _gen_complement(rng: random.Random):
    total = rng.randint(10, 30)
    subset = rng.randint(1, total - 1)
    return (
        f"A set has {total} elements. A subset has {subset} elements. How many elements are in the complement?",
        str(total - subset),
    )


def _gen_carinality(rng: random.Random):
    a = rng.randint(3, 10)
    b = rng.randint(3, 10)
    overlap = rng.randint(1, min(a, b))
    return (
        f"Set A has {a} elements. Set B has {b} elements. They share {overlap} elements. How many elements are in A union B?",
        str(a + b - overlap),
    )


def _gen_venn_two(rng: random.Random):
    only_a = rng.randint(1, 10)
    only_b = rng.randint(1, 10)
    both = rng.randint(1, 10)
    return (
        f"In a Venn diagram: {only_a} items are only in A, {only_b} items are only in B, {both} items are in both. How many total items are there?",
        str(only_a + only_b + both),
    )


def _gen_probability_simple(rng: random.Random):
    n = rng.choice([2, 4, 6])
    favorable = rng.randint(1, n)
    return (
        f"A bag has {n} balls, numbered 1 to {n}. How many balls are greater than {n - favorable}?",
        str(favorable),
    )


def _gen_meaningless(rng: random.Random):
    pairs = [
        ("Every even number is divisible by 2", "yes"),
        ("Every odd number is divisible by 2", "no"),
        ("0 is an even number", "yes"),
        ("1 is a prime number", "no"),
        ("A triangle has 4 sides", "no"),
        ("A square has 4 equal sides", "yes"),
        ("The sum of angles in a triangle is 180 degrees", "yes"),
        ("Pi is approximately 3.14", "yes"),
    ]
    return rng.choice(pairs)


def _gen_if_and_only_if(rng: random.Random):
    x = rng.randint(1, 30)
    y = rng.randint(1, 30)
    x_gt = x > 10
    y_gt = y > 10
    same = x_gt == y_gt
    return (
        f"x is greater than 10 if and only if y is greater than 10. x={x}, y={y}. Is this statement true?",
        "yes" if same else "no",
    )


GENERATORS = [
    _gen_modus_ponens,
    _gen_modus_tollens,
    _gen_hypothetical_syllogism,
    _gen_chain_negation,
    _gen_disjunctive_syllogism,
    _gen_conjunction,
    _gen_disjunction,
    _gen_negation,
    _gen_xor,
    _gen_biconditional,
    _gen_transitivity_ordering,
    _gen_transitivity_simple,
    _gen_sequencing,
    _gen_pattern_next,
    _gen_count_true_statements,
    _gen_set_intersection,
    _gen_set_union,
    _gen_set_difference,
    _gen_set_subset,
    _gen_set_not_subset,
    _gen_binary_and,
    _gen_binary_or,
    _gen_binary_not,
    _gen_binary_xor,
    _gen_if_then_true,
    _gen_if_then_false,
    _gen_counting_combinations,
    _gen_counting_permutations,
    _gen_clock_angle,
    _gen_day_of_week,
    _gen_truth_table,
    _gen_either_or,
    _gen_either_or_true,
    _gen_deduction_simple,
    _gen_deduction_negation,
    _gen_counting,
    _gen_majority,
    _gen_majority_no,
    _gen_absurdity,
    _gen_absurdity_two,
    _gen_comparisons,
    _gen_comparisons_gt,
    _gen_comparisons_lt,
    _gen_divisibility,
    _gen_divisibility_no,
    _gen_positive_negative,
    _gen_odd_even,
    _gen_between,
    _gen_between_no,
    _gen_power_of_two,
    _gen_power_of_two_no,
    _gen_prime,
    _gen_not_prime,
    _gen_syllogism,
    _gen_logic_puzzle,
    _gen_relatives,
    _gen_not_relatives,
    _gen_max_min,
    _gen_min,
    _gen_sum_compare,
    _gen_product_compare,
    _gen_absolute,
    _gen_negation_of_statement,
    _gen_complement,
    _gen_carinality,
    _gen_venn_two,
    _gen_probability_simple,
    _gen_meaningless,
    _gen_if_and_only_if,
]


def _make_sample(question: str, answer: str) -> list[chat_api.BaseItem]:
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
        samples.append(_make_sample(question, answer))
    return samples
