"""Should be correct, validated by Qwen3.7Plus."""

import fractions
import math
import random

from .. import chat_api


def _simplify(num: int, den: int) -> str:
    f = fractions.Fraction(num, den)
    return f"{f.numerator}/{f.denominator}"


def _gen_coin_flip_one(rng: random.Random):
    outcome = rng.choice(["heads", "tails"])
    return f"What is the probability of getting {outcome} when flipping a fair coin?", "1/2"


def _gen_coin_flip_streak(rng: random.Random):
    n = rng.randint(2, 4)
    return f"What is the probability of getting heads on all {n} flips of a fair coin?", f"1/{2**n}"


def _gen_coin_flip_at_least_one(rng: random.Random):
    n = rng.randint(2, 5)
    p_none = 2 ** n
    p_at_least = p_none - 1
    return f"What is the probability of getting at least one heads in {n} flips of a fair coin?", f"{p_at_least}/{p_none}"


def _gen_coin_flip_no_heads(rng: random.Random):
    n = rng.randint(2, 5)
    return f"What is the probability of getting no heads (all tails) in {n} flips of a fair coin?", f"1/{2**n}"


def _gen_unfair_coin(rng: random.Random):
    p_num = rng.randint(1, 3)
    p_den = rng.choice([4, 5, 6, 8, 10])
    q_num = p_den - p_num
    return f"A coin has probability {p_num}/{p_den} of landing heads. What is the probability of tails?", _simplify(q_num, p_den)


def _gen_two_coins(rng: random.Random):
    return "What is the probability of getting one heads and one tails when flipping two fair coins?", "1/2"


def _gen_two_coins_both(rng: random.Random):
    target = rng.choice(["both heads", "both tails"])
    return f"What is the probability of getting {target} when flipping two fair coins?", "1/4"


def _gen_three_coins_majority(rng: random.Random):
    return "What is the probability of getting more heads than tails when flipping three fair coins?", "1/2"


def _gen_dice_one(rng: random.Random):
    target = rng.randint(1, 6)
    return f"What is the probability of rolling a {target} on a fair six-sided die?", "1/6"


def _gen_dice_even(rng: random.Random):
    return "What is the probability of rolling an even number on a fair six-sided die?", "1/2"


def _gen_dice_odd(rng: random.Random):
    return "What is the probability of rolling an odd number on a fair six-sided die?", "1/2"


def _gen_dice_gt(rng: random.Random):
    threshold = rng.randint(2, 4)
    favorable = 6 - threshold
    return f"What is the probability of rolling a number greater than {threshold} on a fair six-sided die?", _simplify(favorable, 6)


def _gen_dice_sum_seven(rng: random.Random):
    return "What is the probability of rolling a sum of 7 with two fair six-sided dice?", "1/6"


def _gen_dice_sum_two(rng: random.Random):
    return "What is the probability of rolling a sum of 2 with two fair six-sided dice?", "1/36"


def _gen_dice_sum_twelve(rng: random.Random):
    return "What is the probability of rolling a sum of 12 with two fair six-sided dice?", "1/36"


def _gen_dice_custom(rng: random.Random):
    sides = rng.choice([4, 8, 10, 12])
    target = rng.randint(1, sides)
    return f"What is the probability of rolling a {target} on a fair {sides}-sided die?", f"1/{sides}"


def _gen_dice_range(rng: random.Random):
    low = rng.randint(1, 3)
    high = rng.randint(low + 1, 6)
    favorable = high - low + 1
    return f"What is the probability of rolling a number between {low} and {high} (inclusive) on a fair six-sided die?", _simplify(favorable, 6)


def _gen_conditional_rain(rng: random.Random):
    return ("Given that the probability of rain is 1/3 and the probability of rain AND carrying an umbrella is 1/4, "
            "what is the probability of carrying an umbrella given that it is raining? (Use P(umbrella|rain) = P(rain and umbrella) / P(rain))", "3/4")


def _gen_conditional_disease(rng: random.Random):
    return ("Given: P(disease) = 1/100, P(positive test | disease) = 9/10, P(positive test | no disease) = 1/10. "
            "What is P(disease | positive test)? Use Bayes' theorem.", "1/12")


def _gen_conditional_marble(rng: random.Random):
    red = rng.randint(2, 5)
    blue = rng.randint(2, 5)
    total = red + blue
    return (f"A bag has {red} red marbles and {blue} blue marbles. "
            f"What fraction of marbles are red?", _simplify(red, total))


def _gen_expected_value_simple(rng: random.Random):
    n = rng.choice([4, 6])
    total = sum(range(1, n + 1))
    return f"What is the expected value of rolling a fair {n}-sided die?", _simplify(total, n)


def _gen_expected_value_coins(rng: random.Random):
    n = rng.randint(2, 5)
    ev = n / 2
    if ev == int(ev):
        return f"If you flip {n} fair coins, what is the expected number of heads?", str(int(ev))
    return f"If you flip {n} fair coins, what is the expected number of heads?", _simplify(n, 2)


def _gen_expected_value_two_dice(rng: random.Random):
    return "What is the expected value of the sum when rolling two fair six-sided dice?", "7"


def _gen_expected_value_weighted(rng: random.Random):
    vals = rng.sample([1, 2, 3, 4, 5], 3)
    total = sum(vals)
    return (f"A spinner has three equal sections labeled {vals[0]}, {vals[1]}, and {vals[2]}. "
            f"What is the expected value of one spin?", _simplify(total, 3))


def _gen_combinatorial_arrange(rng: random.Random):
    n = rng.randint(3, 7)
    return f"In how many ways can you arrange {n} distinct books on a shelf?", str(math.factorial(n))


def _gen_combinatorial_choose(rng: random.Random):
    n = rng.randint(4, 10)
    k = rng.randint(2, n - 1)
    return f"How many ways can you choose {k} students from a group of {n}?", str(math.comb(n, k))


def _gen_combinatorial_permute(rng: random.Random):
    n = rng.randint(4, 8)
    k = rng.randint(2, n - 1)
    return f"How many ways can you choose and arrange {k} students from a group of {n}?", str(math.perm(n, k))


def _gen_combinatorial_committee(rng: random.Random):
    n = rng.randint(5, 10)
    k = rng.randint(2, 4)
    return f"How many ways can you form a committee of {k} people from {n} people?", str(math.comb(n, k))


def _gen_combinatorial_dice_sum(rng: random.Random):
    target = rng.randint(3, 11)
    count = 0
    for i in range(1, 7):
        for j in range(1, 7):
            if i + j == target:
                count += 1
    return f"What is the probability of rolling a sum of {target} with two fair six-sided dice?", _simplify(count, 36)


def _gen_combinatorial_password(rng: random.Random):
    length = rng.randint(3, 5)
    pool = rng.choice([10, 26, 36])
    pool_name = {10: "digits (0-9)", 26: "lowercase letters", 36: "digits and lowercase letters"}[pool]
    total = pool ** length
    return f"How many {length}-character passwords can be made using {pool_name}?", str(total)


def _gen_pascal_triangle(rng: random.Random):
    n = rng.randint(2, 6)
    k = rng.randint(1, n - 1)
    return f"What is the entry in row {n}, position {k} of Pascal's triangle? (0-indexed)", str(math.comb(n, k))


def _gen_binomial_probability(rng: random.Random):
    n = rng.randint(3, 5)
    k = rng.randint(1, n - 1)
    ans = _simplify(math.comb(n, k), 2**n)
    return (f"What is the probability of getting exactly {k} heads in {n} flips of a fair coin?", ans)


def _gen_geometric_distribution(rng: random.Random):
    target = rng.randint(2, 5)
    p = rng.choice([fractions.Fraction(1, 2), fractions.Fraction(1, 3), fractions.Fraction(1, 4)])
    p_str = str(p)
    prob = fractions.Fraction(1) - fractions.Fraction(p)
    prob = prob ** (target - 1) * fractions.Fraction(p)
    return (f"A biased coin has probability {p_str} of heads. What is the probability the first heads "
            f"occurs on flip {target}?", f"{prob.numerator}/{prob.denominator}")


def _gen_mutually_exclusive(rng: random.Random):
    return ("Given P(A) = 1/3 and P(B) = 1/4, and A and B are mutually exclusive, what is P(A or B)?", "7/12")


def _gen_independent(rng: random.Random):
    p1_num = rng.choice([1, 2, 3])
    p1_den = rng.choice([4, 5, 6])
    p2_num = rng.choice([1, 2, 3])
    p2_den = rng.choice([4, 5, 6])
    result_num = p1_num * p2_num
    result_den = p1_den * p2_den
    return (f"Event A has probability {p1_num}/{p1_den}. Event B has probability {p2_num}/{p2_den}. "
            f"If they are independent, what is P(A and B)?", _simplify(result_num, result_den))


def _gen_complement(rng: random.Random):
    p_num = rng.randint(1, 4)
    p_den = rng.choice([5, 6, 7, 8, 10])
    return f"The probability of an event is {p_num}/{p_den}. What is the probability of it NOT happening?", _simplify(p_den - p_num, p_den)



_BAYES_DISEASE_VALS = [
    (fractions.Fraction(1, 10), "1/10"),
    (fractions.Fraction(1, 20), "1/20"),
    (fractions.Fraction(1, 50), "1/50"),
]
_BAYES_TEST_VALS = [
    (fractions.Fraction(9, 10), "9/10"),
    (fractions.Fraction(4, 5), "4/5"),
]
_BAYES_FALSE_VALS = [
    (fractions.Fraction(1, 10), "1/10"),
    (fractions.Fraction(1, 5), "1/5"),
]


def _gen_bayes_simple(rng: random.Random):
    p_disease, p_disease_str = rng.choice(_BAYES_DISEASE_VALS)
    p_test_given, p_test_str = rng.choice(_BAYES_TEST_VALS)
    p_false, p_false_str = rng.choice(_BAYES_FALSE_VALS)
    num = p_disease * p_test_given
    den = num + (1 - p_disease) * p_false
    result = num / den
    return (f"Given: P(disease) = {p_disease_str}, P(positive|disease) = {p_test_str}, "
            f"P(positive|no disease) = {p_false_str}. What is P(disease|positive)?", f"{result.numerator}/{result.denominator}")


def _gen_coupon_collector(rng: random.Random):
    n = rng.choice([3, 4, 5])
    expected = sum(fractions.Fraction(n, i) for i in range(1, n + 1))
    return f"If there are {n} types of coupons and each is equally likely, what is the expected number to collect all types?", f"{expected.numerator}/{expected.denominator}"


def _gen_dice_probability_all_different(rng: random.Random):
    return "What is the probability that three fair six-sided dice all show different numbers?", _simplify(120, 216)


def _gen_permutation_repeated(rng: random.Random):
    n = rng.choice([3, 4, 5])
    return f"How many distinct ways can you arrange {n} items where all are different?", str(math.factorial(n))



GENERATORS = [
    _gen_coin_flip_one,
    _gen_coin_flip_streak,
    _gen_coin_flip_at_least_one,
    _gen_coin_flip_no_heads,
    _gen_unfair_coin,
    _gen_two_coins,
    _gen_two_coins_both,
    _gen_three_coins_majority,
    _gen_dice_one,
    _gen_dice_even,
    _gen_dice_odd,
    _gen_dice_gt,
    _gen_dice_sum_seven,
    _gen_dice_sum_two,
    _gen_dice_sum_twelve,
    _gen_dice_custom,
    _gen_dice_range,
    _gen_conditional_rain,
    _gen_conditional_disease,
    _gen_conditional_marble,
    _gen_expected_value_simple,
    _gen_expected_value_coins,
    _gen_expected_value_two_dice,
    _gen_expected_value_weighted,
    _gen_combinatorial_arrange,
    _gen_combinatorial_choose,
    _gen_combinatorial_permute,
    _gen_combinatorial_committee,
    _gen_combinatorial_dice_sum,
    _gen_combinatorial_password,
    _gen_pascal_triangle,
    _gen_binomial_probability,
    _gen_geometric_distribution,
    _gen_mutually_exclusive,
    _gen_independent,
    _gen_complement,
    _gen_bayes_simple,
    _gen_coupon_collector,
    _gen_dice_probability_all_different,
    _gen_permutation_repeated,
]


def _make_sample(question: str, answer: str, rng: random.Random) -> list[chat_api.BaseItem]:
    if "/" in answer:
        assert answer.count("/") == 1
        num, denom = answer.split("/")

        if rng.random() > 0.5:
            question = f'{question} Write the answer as a simplified fraction.'
            answer = _simplify(int(num), int(denom))
        else:
            question = f'{question} Write the answer in percents rounded to nearest integer.'
            answer = f"{round(fractions.Fraction(int(num), int(denom)) * 100)}%"


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
        samples.append(_make_sample(question, answer, rng))
    return samples
