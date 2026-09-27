"""Should be correct, validated by Qwen3.7Plus."""
import random
import math
import fractions

from .. import chat_api

from decimal import Decimal, ROUND_HALF_UP

def round_half_up(n):
    return int(Decimal(str(n)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def _gen_addition(rng: random.Random):
    a = rng.randint(-999, 999)
    b = rng.randint(-999, 999)
    return f"What is {a} + {b}?", str(a + b)


def _gen_subtraction(rng: random.Random):
    a = rng.randint(-999, 999)
    b = rng.randint(-999, 999)
    return f"What is {a} - {b}?", str(a - b)


def _gen_multiplication(rng: random.Random):
    a = rng.randint(-99, 99)
    b = rng.randint(-99, 99)
    return f"What is {a} x {b}?", str(a * b)


def _gen_division(rng: random.Random):
    b = rng.randint(-99, 99)
    if b == 0: b = rng.randint(1, 999)
    q = rng.randint(-99, 99)
    a = b * q
    return f"What is {a} / {b}?", str(q)


def _gen_modulo(rng: random.Random):
    b = rng.randint(1, 20)
    a = rng.randint(-200, 200)
    return f"What is {a} mod {b}?", str(a % b)


def _gen_power(rng: random.Random):
    base = rng.randint(-10, 10)
    exp = rng.randint(0, 4)
    if base == 0 and exp == 0:
        base = 1
    if base < 0: return f"What is ({base})^{exp}?", str(base ** exp)
    return f"What is {base}^{exp}?", str(base ** exp)


def _gen_percentage(rng: random.Random):
    value = rng.randint(1, 200) * 5
    pct = rng.choice([10, 15, 20, 25, 30, 40, 50, 75])
    result = value * pct // 100
    return f"What is {pct}% of {value} rounded down?", str(result)


def _gen_gcd(rng: random.Random):
    a = rng.randint(2, 200)
    b = rng.randint(2, 200)
    return f"What is the greatest common divisor of {a} and {b}?", str(math.gcd(a, b))


def _gen_lcm(rng: random.Random):
    a = rng.randint(2, 50)
    b = rng.randint(2, 50)
    return f"What is the least common multiple of {a} and {b}?", str(a * b // math.gcd(a, b))


def _gen_average(rng: random.Random):
    nums = [rng.randint(1, 100) for _ in range(rng.randint(2, 6))]
    avg = fractions.Fraction(sum(nums), len(nums))
    nums_str = ", ".join(str(n) for n in nums)
    return f"What is the average of {nums_str}? If it is not an integer, write it out as a fraction.", str(int(avg)) if avg.denominator == 1 else f"{avg.numerator}/{avg.denominator}"


def _gen_area_rectangle(rng: random.Random):
    w = rng.randint(1, 50)
    h = rng.randint(1, 50)
    return f"What is the area of a rectangle with width {w} and height {h}?", str(w * h)


def _gen_area_circle(rng: random.Random):
    r = rng.randint(1, 20)
    area = 3.14 * r * r
    return f"What is the area of a circle with radius {r}? Use 3.14 for pi and round to the nearest whole number.", str(round_half_up(area))


def _gen_perimeter_rectangle(rng: random.Random):
    w = rng.randint(1, 50)
    h = rng.randint(1, 50)
    return f"What is the perimeter of a rectangle with width {w} and height {h}?", str(2 * (w + h))


def _gen_pythagorean(rng: random.Random):
    triples = [(3, 4, 5), (5, 12, 13), (6, 8, 10), (7, 24, 25), (8, 15, 17), (9, 12, 15)]
    a, b, c = rng.choice(triples)
    unknown = rng.choice(["hypotenuse", "leg"])
    if unknown == "hypotenuse":
        return f"A right triangle has legs {a} and {b}. What is the hypotenuse?", str(c)
    else:
        return f"A right triangle has a leg of {b} and hypotenuse of {c}. What is the other leg?", str(a)


def _gen_quadratic(rng: random.Random):
    x = rng.randint(-10, 10)
    a = rng.choice([1, 2])
    b = rng.choice([i for i in range(-10, 11) if i != 0])
    c_val = a * x * x + b * x
    other = -b // a - x if (-b) % a == 0 else None
    if other is None or other == x:
        return f"Solve for x: {a}x^2 + {b}x = {c_val}. What is the integer solution?", str(x)
    return f"Solve for x: {a}x^2 + {b}x = {c_val}. Find all roots and write them separated by space.", f"{x} {other}"


def _gen_linear(rng: random.Random):
    x = rng.randint(-20, 20)
    a = rng.choice([i for i in range(-10, 11) if i != 0])
    b = rng.randint(-50, 50)
    result = a * x + b
    return f"Solve for x: {a}x + {b} = {result}. What is x?", str(x)


def _gen_counting(rng: random.Random):
    a = rng.randint(-100, 100)
    b = rng.randint(a, 100)
    return f"How many integers are there from {a} to {b} inclusive?", str(b - a + 1)


def _gen_fibonacci(rng: random.Random):
    n = rng.randint(0, 15)
    fibs = [0, 1]
    for _ in range(2, n + 1):
        fibs.append(fibs[-1] + fibs[-2])
    return f"What is the {n}th Fibonacci number? (F(0)=0, F(1)=1)", str(fibs[n])


def _gen_factorial(rng: random.Random):
    n = rng.randint(0, 8)
    return f"What is {n}! ({n} factorial)?", str(math.factorial(n))


def _gen_exponentiation(rng: random.Random):
    base = rng.randint(-12, 12)
    exp = rng.randint(0, 3)
    if base == 0 and exp == 0:
        base = 1
    if base < 0: return f"What is ({base}) raised to the power of {exp}?", str(base ** exp)
    return f"What is {base} raised to the power of {exp}?", str(base ** exp)


GENERATORS = [
    _gen_addition,
    _gen_subtraction,
    _gen_multiplication,
    _gen_division,
    _gen_modulo,
    _gen_power,
    _gen_percentage,
    _gen_gcd,
    _gen_lcm,
    _gen_average,
    _gen_area_rectangle,
    _gen_area_circle,
    _gen_perimeter_rectangle,
    _gen_pythagorean,
    _gen_quadratic,
    _gen_linear,
    _gen_counting,
    _gen_fibonacci,
    _gen_factorial,
    _gen_exponentiation,
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
