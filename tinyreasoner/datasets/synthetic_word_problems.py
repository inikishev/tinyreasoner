"""Should be correct, validated by Qwen3.7Plus (thought its correct 1st try which was sus)."""
import random
from fractions import Fraction

from .. import chat_api

# -- Ratio problems --

def _gen_ratio_find_other(rng: random.Random):
    a = rng.randint(1, 10)
    b = rng.randint(1, 10)
    given = rng.choice(["a", "b"])
    val = rng.randint(2, 50) * (a if given == "a" else b)
    if given == "a":
        answer = val * b // a
        return (
            f"The ratio of apples to oranges is {a}:{b}. If there are {val} apples, how many oranges are there?",
            str(answer),
        )
    else:
        answer = val * a // b
        return (
            f"The ratio of apples to oranges is {a}:{b}. If there are {val} oranges, how many apples are there?",
            str(answer),
        )


def _gen_ratio_total(rng: random.Random):
    a = rng.randint(1, 8)
    b = rng.randint(1, 8)
    total = (a + b) * rng.randint(3, 20)
    part_a = total * a // (a + b)
    return (
        f"The ratio of boys to girls is {a}:{b}. If there are {total} students total, how many boys are there?",
        str(part_a),
    )


def _gen_ratio_simplify(rng: random.Random):
    factor = rng.randint(2, 10)
    a = rng.randint(1, 10) * factor
    b = rng.randint(1, 10) * factor
    from math import gcd
    g = gcd(a, b)
    return (
        f"What is the simplest form of the ratio {a}:{b}?",
        f"{a // g}:{b // g}",
    )


def _gen_ratio_three_parts(rng: random.Random):
    a = rng.randint(1, 5)
    b = rng.randint(1, 5)
    c = rng.randint(1, 5)
    unit = rng.randint(2, 20)
    total = (a + b + c) * unit
    return (
        f"A recipe uses ingredients in the ratio {a}:{b}:{c}. If you use {total} cups total, how many cups of the first ingredient?",
        str(a * unit),
    )


def _gen_price_ratio(rng: random.Random):
    items = rng.sample(["apples", "oranges", "bananas", "pears", "grapes"], 2)
    a_ratio = rng.randint(1, 8)
    b_ratio = rng.randint(1, 8)
    unit_price = rng.randint(3, 25)
    total_a = unit_price * a_ratio
    answer = unit_price * b_ratio
    return (
        f"{a_ratio} {items[0]} cost {total_a} cents. At the same rate, how much do {b_ratio} {items[1]} cost?",
        str(answer),
    )


# -- Rate / Speed / Time problems --

def _gen_distance_speed_time(rng: random.Random):
    speed = rng.randint(5, 80)
    time = rng.randint(1, 12)
    distance = speed * time
    return (
        f"A car travels at {speed} km/h for {time} hours. How far does it travel?",
        str(distance),
    )


def _gen_speed_from_distance(rng: random.Random):
    time = rng.choice([2, 3, 4, 5, 6])
    distance = rng.randint(10, 200) * time
    speed = distance // time
    return (
        f"A car travels {distance} km in {time} hours. What is its speed in km/h?",
        str(speed),
    )


def _gen_time_from_distance(rng: random.Random):
    speed = rng.randint(10, 60)
    distance = speed * rng.randint(1, 8)
    time = distance // speed
    return (
        f"A car travels {distance} km at {speed} km/h. How many hours does the trip take?",
        str(time),
    )


def _gen_two_trains(rng: random.Random):
    speed1 = rng.randint(40, 100)
    speed2 = rng.randint(40, 100)
    distance = rng.randint(200, 800)
    combined = speed1 + speed2
    answer = f"{distance / combined:.1f}"
    return (
        f"Two trains are {distance} km apart, moving toward each other. One goes {speed1} km/h, the other {speed2} km/h. How many hours until they meet? (round to 1 decimal)",
        answer,
    )


def _gen_upstream_downstream(rng: random.Random):
    boat_speed = rng.randint(5, 20)
    current = rng.randint(1, boat_speed - 1)
    dist = rng.randint(5, 30)
    time_up = dist / (boat_speed - current)
    time_down = dist / (boat_speed + current)
    total = time_up + time_down
    return (
        f"A boat goes {boat_speed} km/h in still water. The current is {current} km/h. How many hours to go {dist} km upstream and {dist} km back? (round to 1 decimal)",
        f"{total:.1f}",
    )


def _gen_work_rate(rng: random.Random):
    time_alone = rng.randint(2, 12)
    time_other = rng.randint(2, 12)
    combined = Fraction(1, time_alone) + Fraction(1, time_other)
    answer_hours = Fraction(1, combined)
    if answer_hours.denominator == 1:
        answer = str(answer_hours.numerator)
    else:
        answer = f"{answer_hours.numerator}/{answer_hours.denominator}"
    return (
        f"Alice can paint a room in {time_alone} hours. Bob can paint it in {time_other} hours. How many hours to paint it together? Answer as a fraction if needed.",
        answer,
    )


def _gen_combined_work(rng: random.Random):
    people = rng.randint(2, 5)
    rate_each = rng.choice([2, 3, 4, 5, 6, 10])
    combined = Fraction(1, rate_each) * people
    answer_hours = Fraction(1, combined)
    if answer_hours.denominator == 1:
        answer = str(answer_hours.numerator)
    else:
        answer = f"{answer_hours.numerator}/{answer_hours.denominator}"
    return (
        f"{people} workers each can complete a job in {rate_each} hours alone. How many hours to complete the job together? Answer as a fraction if needed.",
        answer,
    )


# -- Proportion problems --

def _gen_simple_proportion(rng: random.Random):
    a = rng.randint(1, 10)
    b = rng.randint(1, 10)
    x = rng.randint(2, 20)
    answer = Fraction(x * b, a)
    if answer.denominator == 1:
        ans_str = str(answer.numerator)
    else:
        ans_str = f"{answer.numerator}/{answer.denominator}"
    return (
        f"If {a} items cost {b} dollars, how much do {x} items cost? Answer as a fraction if needed.",
        ans_str,
    )


def _gen_scale_factor(rng: random.Random):
    factor = rng.randint(2, 8)
    value = rng.randint(10, 100)
    result = value * factor
    return (
        f"A map has a scale of 1:{factor}. If a road measures {value} cm on the map, what is its actual length in cm?",
        str(result),
    )


def _gen_inverse_proportion(rng: random.Random):
    workers = rng.randint(2, 8)
    days_alone = rng.randint(3, 15)
    total_work = workers * days_alone
    candidates = [w for w in range(2, 13) if w != workers and total_work % w == 0]
    if not candidates:
        days_alone = workers * rng.choice([2, 3, 4])
        total_work = workers * days_alone
        candidates = [w for w in range(2, 13) if w != workers and total_work % w == 0]
    more_workers = rng.choice(candidates)
    new_days = total_work // more_workers
    return (
        f"{workers} workers can build a wall in {days_alone} days. How many days would {more_workers} workers take?",
        str(new_days),
    )


def _gen_unit_rate(rng: random.Random):
    items = rng.choice(["apples", "pencils", "notebooks", "socks"])
    quantity = rng.choice([3, 4, 5, 6, 8, 10, 12])
    total_cost = rng.randint(2, 20) * quantity
    return (
        f"What is the unit rate if {quantity} {items} cost ${total_cost}?",
        f"${total_cost // quantity}",
    )


def _gen_percent_proportion(rng: random.Random):
    part = rng.randint(5, 50)
    whole = rng.randint(part + 10, 100)
    pct = Fraction(part * 100, whole)
    if pct.denominator == 1:
        answer = str(pct.numerator) + "%"
    else:
        answer = f"{pct.numerator}/{pct.denominator}%"
    return (
        f"{part} out of {whole} students passed. What percent passed? Answer as a fraction if needed.",
        answer,
    )


# -- Mixture problems --

def _gen_mixture_two(rng: random.Random):
    price_a = rng.randint(2, 8)
    price_b = rng.randint(2, 8)
    while price_a == price_b:
        price_b = rng.randint(2, 8)
    kg_a = rng.randint(1, 10)
    kg_b = rng.randint(1, 10)
    total_cost = price_a * kg_a + price_b * kg_b
    total_kg = kg_a + kg_b
    avg = Fraction(total_cost, total_kg)
    if avg.denominator == 1:
        answer = f"${avg.numerator}"
    else:
        answer = f"${avg.numerator}/{avg.denominator}"
    return (
        f"Mix {kg_a} kg of nuts at ${price_a}/kg with {kg_b} kg at ${price_b}/kg. What is the price per kg of the mixture? Answer as a fraction if needed.",
        answer,
    )


def _gen_mixture_concentration(rng: random.Random):
    conc_a = rng.choice([10, 20, 30, 40, 50])
    conc_b = rng.choice([60, 70, 80, 90, 100])
    vol_a = rng.randint(1, 10)
    vol_b = rng.randint(1, 10)
    solute = conc_a * vol_a + conc_b * vol_b
    total_vol = vol_a + vol_b
    answer = solute / total_vol
    return (
        f"Mix {vol_a} liters of {conc_a}% solution with {vol_b} liters of {conc_b}% solution. What is the resulting concentration? (round to 1 decimal)",
        f"{answer:.1f}%",
    )


def _gen_alloy(rng: random.Random):
    metal = rng.choice(["gold", "silver", "copper", "zinc"])
    pct_a = rng.choice([30, 40, 50, 60, 70])
    pct_b = 100 - rng.choice([30, 40, 50, 60, 70])
    kg_a = rng.randint(1, 10)
    kg_b = rng.randint(1, 10)
    metal_kg_a = kg_a * pct_a / 100
    metal_kg_b = kg_b * pct_b / 100
    total_metal = metal_kg_a + metal_kg_b
    if total_metal == int(total_metal):
        answer = str(int(total_metal))
    else:
        answer = f"{total_metal:.1f}"
    return (
        f"Alloy A is {pct_a}% {metal}. Alloy B is {pct_b}% {metal}. Mix {kg_a} kg of A with {kg_b} kg of B. How many kg of {metal} are in the mixture?",
        answer,
    )


def _gen_price_mixture(rng: random.Random):
    kind_a = rng.choice(["rice", "wheat", "coffee", "tea"])
    kind_b = rng.choice(["rice", "wheat", "coffee", "tea"])
    while kind_a == kind_b:
        kind_b = rng.choice(["rice", "wheat", "coffee", "tea"])
    price_a = rng.randint(20, 80)
    price_b = rng.randint(20, 80)
    while price_a == price_b:
        price_b = rng.randint(20, 80)
    kg_a = rng.randint(1, 10)
    kg_b = rng.randint(1, 10)
    total_cost = price_a * kg_a + price_b * kg_b
    return (
        f"Mix {kg_a} kg of {kind_a} at ${price_a}/kg with {kg_b} kg of {kind_b} at ${price_b}/kg. What is the total cost?",
        f"${total_cost}",
    )


# -- Age puzzles --

def _gen_age_difference(rng: random.Random):
    names = rng.sample(["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"], 2)
    n1, n2 = names
    age2 = rng.randint(5, 60)
    diff = rng.randint(2, 20)
    age1 = age2 + diff
    return (
        f"{n1} is {diff} years older than {n2}. If {n2} is {age2} years old, how old is {n1}?",
        str(age1),
    )


def _gen_age_in_years(rng: random.Random):
    names = rng.sample(["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"], 2)
    n1, n2 = names
    age1 = rng.randint(5, 50)
    age2 = rng.randint(5, 50)
    years = rng.randint(1, 15)
    return (
        f"{n1} is {age1} years old and {n2} is {age2} years old. How many years from now will {n1} be {age1 + years} years old?",
        str(years),
    )


def _gen_age_sum(rng: random.Random):
    names = rng.sample(["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"], 2)
    n1, n2 = names
    age2 = rng.randint(5, 40)
    age1 = rng.randint(5, 40)
    total = age1 + age2
    return (
        f"{n1} and {n2} are {total} years old in total. If {n2} is {age2}, how old is {n1}?",
        str(age1),
    )


def _gen_age_ratio(rng: random.Random):
    names = rng.sample(["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"], 2)
    n1, n2 = names
    r1 = rng.randint(1, 5)
    r2 = rng.randint(1, 5)
    unit = rng.randint(3, 15)
    age1 = r1 * unit
    age2 = r2 * unit
    return (
        f"The ratio of {n1}'s age to {n2}'s age is {r1}:{r2}. If {n2} is {age2} years old, how old is {n1}?",
        str(age1),
    )


def _gen_age_double(rng: random.Random):
    names = rng.sample(["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"], 2)
    n1, n2 = names
    age2 = rng.randint(3, 25)
    age1 = 2 * age2
    return (
        f"{n1} is twice as old as {n2}. If {n1} is {age1} years old, how old is {n2}?",
        str(age2),
    )


def _gen_age_future(rng: random.Random):
    names = rng.sample(["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"], 2)
    n1, n2 = names
    age2 = rng.randint(5, 30)
    years = rng.randint(3, 15)
    future_age2 = age2 + years
    future_age1 = 2 * future_age2
    age1 = future_age1 - years
    return (
        f"In {years} years, {n1} will be twice as old as {n2}. {n2} is currently {age2}. How old is {n1} now?",
        str(age1),
    )


def _gen_age_past(rng: random.Random):
    names = rng.sample(["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"], 2)
    n1, n2 = names
    past_age2 = rng.randint(1, 20)
    past_age1 = past_age2 + rng.randint(2, 15)
    years_ago = rng.randint(2, 10)
    age2 = past_age2 + years_ago
    return (
        f"{years_ago} years ago, {n1} was {past_age1} years old and {n2} was {past_age2}. How old is {n2} now?",
        str(age2),
    )


def _gen_age_multiple(rng: random.Random):
    names = rng.sample(["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"], 3)
    n1, n2, n3 = names
    age3 = rng.randint(3, 20)
    age2 = age3 + rng.randint(2, 10)
    age1 = age2 + rng.randint(2, 10)
    return (
        f"{n1} is {age1 - age2} years older than {n2}, and {n2} is {age2 - age3} years older than {n3}. If {n3} is {age3}, how old is {n1}?",
        str(age1),
    )


GENERATORS = [
    _gen_ratio_find_other,
    _gen_ratio_total,
    _gen_ratio_simplify,
    _gen_ratio_three_parts,
    _gen_price_ratio,
    _gen_distance_speed_time,
    _gen_speed_from_distance,
    _gen_time_from_distance,
    _gen_two_trains,
    _gen_upstream_downstream,
    _gen_work_rate,
    _gen_combined_work,
    _gen_simple_proportion,
    _gen_scale_factor,
    _gen_inverse_proportion,
    _gen_unit_rate,
    _gen_percent_proportion,
    _gen_mixture_two,
    _gen_mixture_concentration,
    _gen_alloy,
    _gen_price_mixture,
    _gen_age_difference,
    _gen_age_in_years,
    _gen_age_sum,
    _gen_age_ratio,
    _gen_age_double,
    _gen_age_future,
    _gen_age_past,
    _gen_age_multiple,
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
