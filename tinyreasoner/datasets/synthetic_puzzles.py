"""Should be correct, validated by Qwen3.7Plus."""

import random
import math

from .. import chat_api


def _gen_sudoku_cell(rng: random.Random):
    grid = [[0] * 9 for _ in range(9)]
    for i in range(9):
        for j in range(9):
            grid[i][j] = (i * 3 + i // 3 + j) % 9 + 1
    row, col = rng.sample(range(9), 2)
    hidden = grid[row][col]
    grid_str = ""
    for r in range(9):
        row_vals = []
        for c in range(9):
            if r == row and c == col:
                row_vals.append("?")
            else:
                row_vals.append(str(grid[r][c]))
        grid_str += " ".join(row_vals) + "\n"
    return (
        f"In this partially filled Sudoku row, what number replaces the '?'?\n{grid_str.strip()}",
        str(hidden),
    )


def _gen_sudoku_row(rng: random.Random):
    row = list(range(1, 10))
    rng.shuffle(row)
    missing_idx = rng.randint(0, 8)
    missing_val = row[missing_idx]
    shown = [str(v) if i != missing_idx else "?" for i, v in enumerate(row)]
    return (
        f"What number is missing from this Sudoku row (digits 1-9, each used once)? {' '.join(shown)}",
        str(missing_val),
    )


def _gen_mastermind(rng: random.Random):
    colors = ["red", "blue", "green", "yellow"]
    n = 4
    secret = [rng.choice(colors) for _ in range(n)]
    guess = [rng.choice(colors) for _ in range(n)]
    black = sum(s == g for s, g in zip(secret, guess))
    secret_counts = {}
    for c in secret:
        secret_counts[c] = secret_counts.get(c, 0) + 1
    guess_counts = {}
    for c in guess:
        guess_counts[c] = guess_counts.get(c, 0) + 1
    white = sum(min(secret_counts.get(c, 0), guess_counts.get(c, 0)) for c in set(secret + guess)) - black
    return (
        f"Secret code has 4 colors from {colors}. Guess: {', '.join(guess)}. Feedback: {black} black(s), {white} white(s). How many black pegs?",
        str(black),
    )


def _gen_nim_stone(rng: random.Random):
    piles = [rng.randint(1, 5) for _ in range(rng.randint(2, 4))]
    pile_str = ", ".join(str(p) for p in piles)
    xor = 0
    for p in piles:
        xor ^= p
    return (
        f"There are piles with {pile_str} stones. Two players take turns removing any number from one pile. Who wins with optimal play?",
        "first" if xor != 0 else "second",
    )


def _gen_tower_hanoi(rng: random.Random):
    n = rng.randint(1, 6)
    moves = (1 << n) - 1
    return (
        f"How many moves are needed to solve Tower of Hanoi with {n} disks?",
        str(moves),
    )


def _gen_clock_puzzle(rng: random.Random):
    h1 = rng.randint(1, 12)
    m1 = rng.choice([0, 15, 30, 45])
    elapsed = rng.randint(1, 12) * 30
    total_minutes = h1 * 60 + m1 + elapsed
    h2 = (total_minutes // 60) % 12
    if h2 == 0:
        h2 = 12
    m2 = total_minutes % 60
    h1_str = f"{h1}:{m1:02d}"
    h2_str = f"{h2}:{m2:02d}"
    return (
        f"If it is {h1_str}, what time will it be after {elapsed} minutes?",
        h2_str,
    )



def _gen_kayak_river(rng: random.Random):
    current_speed = rng.randint(1, 3)
    kayak_speed = rng.randint(current_speed + 1, 8)
    dist_up = rng.randint(5, 20)
    dist_down = dist_up
    time_up = dist_up / (kayak_speed - current_speed)
    time_down = dist_down / (kayak_speed + current_speed)
    total = time_up + time_down
    return (
        f"A kayak goes {kayak_speed} km/h in still water, current is {current_speed} km/h. Time to go {dist_up} km up and {dist_down} km back (round to 1 decimal)?",
        f"{total:.1f}",
    )


def _gen_paper_folding(rng: random.Random):
    n = rng.randint(1, 7)
    holes = 1 << n
    return (
        f"You fold a paper in half {n} times and punch 1 hole through all layers. How many holes when unfolded?",
        str(holes),
    )


def _gen_binary_search(rng: random.Random):
    n = rng.randint(8, 256)
    max_steps = math.floor(math.log2(n)) + 1
    return (
        f"What is the maximum number of comparisons needed to find an item in a sorted array of {n} elements using binary search?",
        str(max_steps),
    )


def _gen_crc(rng: random.Random):
    data = [rng.randint(0, 1) for _ in range(rng.randint(4, 8))]
    divisor = [1, 0, 1, 1]
    padded = data + [0] * (len(divisor) - 1)
    for i in range(len(data)):
        if padded[i] == 1:
            for j in range(len(divisor)):
                padded[i + j] ^= divisor[j]
    remainder = padded[len(data):]
    return (
        f"What is the CRC remainder of binary { ''.join(str(b) for b in data) } divided by polynomial { ''.join(str(b) for b in divisor) }?",
        "".join(str(b) for b in remainder),
    )


def _gen_checksum(rng: random.Random):
    nums = [rng.randint(0, 255) for _ in range(rng.randint(3, 6))]
    check = sum(nums) % 256
    nums_str = ", ".join(str(n) for n in nums)
    return (
        f"What is the checksum (sum mod 256) of the bytes: {nums_str}?",
        str(check),
    )


def _gen_gcd_lcm(rng: random.Random):
    a = rng.randint(2, 50)
    b = rng.randint(2, 50)
    g = math.gcd(a, b)
    l = a * b // g
    return (
        f"What is the GCD and LCM of {a} and {b}? Format: GCD,LCM",
        f"{g},{l}",
    )


def _gen_modular_inverse(rng: random.Random):
    modulus = rng.choice([7, 11, 13, 17, 19, 23])
    a = rng.randint(2, modulus - 1)
    while math.gcd(a, modulus) != 1:
        a = rng.randint(2, modulus - 1)
    inv = pow(a, -1, modulus)
    return (
        f"What is the modular inverse of {a} mod {modulus}? (i.e., {a} * x ≡ 1 mod {modulus})",
        str(inv),
    )


def _gen_euler_totient(rng: random.Random):
    n = rng.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 16, 18, 20, 24, 30])
    result = sum(1 for i in range(1, n + 1) if math.gcd(i, n) == 1)
    return (
        f"What is Euler's totient function φ({n})?",
        str(result),
    )


def _gen_combinatorial_count(rng: random.Random):
    n = rng.randint(3, 10)
    k = rng.randint(1, n)
    return (
        f"How many ways to choose {k} items from {n} distinct items (order does not matter)?",
        str(math.comb(n, k)),
    )


def _gen_permutation_count(rng: random.Random):
    n = rng.randint(3, 8)
    k = rng.randint(1, n)
    return (
        f"How many ways to arrange {k} items chosen from {n} distinct items (order matters)?",
        str(math.perm(n, k)),
    )


def _gen_partitions(rng: random.Random):
    n = rng.randint(1, 12)
    def count_partitions(n, max_val):
        if n == 0:
            return 1
        if n < 0 or max_val == 0:
            return 0
        return count_partitions(n - max_val, max_val) + count_partitions(n, max_val - 1)
    result = count_partitions(n, n)
    return (
        f"In how many ways can the integer {n} be written as a sum of positive integers (order doesn't matter)?",
        str(result),
    )


def _gen_collatz(rng: random.Random):
    n = rng.randint(2, 20)
    start = n
    steps = 0
    while n != 1:
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        steps += 1
    return (
        f"How many steps does the Collatz sequence take to reach 1 starting from {start}?",
        str(steps),
    )


def _gen_digit_sum(rng: random.Random):
    n = rng.randint(100, 9999)
    ds = sum(int(d) for d in str(n))
    return (
        f"What is the sum of the digits of {n}?",
        str(ds),
    )


def _gen_reverse_digits(rng: random.Random):
    n = rng.randint(10, 9999)
    r = int(str(n)[::-1])
    return (
        f"What do you get when you reverse the digits of {n}?",
        str(r),
    )


def _gen_palindrome_check(rng: random.Random):
    base = "".join(rng.choices("abcde", k=rng.randint(2, 4)))
    choice = rng.choice([1,2,3,4])
    if choice==1:
        s = base + base[::-1]
    elif choice==2:
        s = base + "x" + base[::-1]
    elif choice==3:
        s = base + "x" + base
    else:
        s = "".join(rng.choices("abc", k=rng.randint(2, 10)))

    return (
        f'Is the string "{s}" a palindrome?',
        "yes" if s == s[::-1] else "no",
    )


def _gen_maze_shortest(rng: random.Random):
    rows = rng.randint(3, 6)
    cols = rng.randint(3, 6)
    grid = [[0] * cols for _ in range(rows)]
    num_walls = rng.randint(1, rows * cols // 3)
    for _ in range(num_walls):
        r, c = rng.randint(0, rows - 1), rng.randint(0, cols - 1)
        if not (r == 0 and c == 0) and not (r == rows - 1 and c == cols - 1):
            grid[r][c] = 1
    grid_str = ""
    for r in range(rows):
        row_str = ""
        for c in range(cols):
            if r == 0 and c == 0:
                row_str += "S "
            elif r == rows - 1 and c == cols - 1:
                row_str += "E "
            elif grid[r][c] == 1:
                row_str += "# "
            else:
                row_str += ". "
        grid_str += row_str.strip() + "\n"
    from collections import deque
    q = deque([(0, 0, 0)])
    visited = {(0, 0)}
    found = False
    dist = 0
    while q:
        r, c, d = q.popleft()
        if r == rows - 1 and c == cols - 1:
            dist = d
            found = True
            break
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited and grid[nr][nc] == 0:
                visited.add((nr, nc))
                q.append((nr, nc, d + 1))
    if not found:
        return (
            f"What is the shortest path length from S to E in this maze? (S=start, E=end, #=wall, .=open)\n{grid_str.strip()}",
            "impossible",
        )
    return (
        f"What is the shortest path length from S to E in this maze? (S=start, E=end, #=wall, .=open)\n{grid_str.strip()}",
        str(dist),
    )


def _gen_map_coloring(rng: random.Random):
    n_regions = rng.randint(3, 5)
    n_colors = rng.randint(2, 4)
    adjacency = []
    for i in range(n_regions):
        for j in range(i + 1, n_regions):
            if rng.random() < 0.6:
                adjacency.append((i, j))
    adj_str = ", ".join(f"{a+1}-{b+1}" for a, b in adjacency) if adjacency else "none"

    def _is_colorable(n, edges, k):
        adj_list = [[] for _ in range(n)]
        for a, b in edges:
            adj_list[a].append(b)
            adj_list[b].append(a)
        colors = [0] * n

        def _solve(v):
            if v == n:
                return True
            for c in range(1, k + 1):
                if all(colors[nb] != c for nb in adj_list[v]):
                    colors[v] = c
                    if _solve(v + 1):
                        return True
                    colors[v] = 0
            return False

        return _solve(0)

    colorable = _is_colorable(n_regions, adjacency, n_colors)
    return (
        f"A map has {n_regions} regions with adjacencies: {adj_str}. Using at most {n_colors} colors, is this map colorable?",
        "yes" if colorable else "no",
    )


def _gen_graph_diameter(rng: random.Random):
    n = rng.randint(3, 6)
    edges = []
    for i in range(n - 1):
        edges.append((i, i + 1))
    if rng.random() < 0.5 and n > 3:
        edges.append((0, rng.randint(2, n - 1)))
    adj = {i: [] for i in range(n)}
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    max_dist = 0
    for start in range(n):
        from collections import deque
        q = deque([(start, 0)])
        visited = {start}
        while q:
            node, d = q.popleft()
            max_dist = max(max_dist, d)
            for nb in adj[node]:
                if nb not in visited:
                    visited.add(nb)
                    q.append((nb, d + 1))
    edge_str = ", ".join(f"{a+1}-{b+1}" for a, b in edges)
    return (
        f"What is the diameter (longest shortest path) of this graph with {n} nodes and edges: {edge_str}?",
        str(max_dist),
    )


def _gen_binary_tree_height(rng: random.Random):
    n = rng.randint(1, 31)
    height = math.floor(math.log2(n)) if n > 0 else 0
    return (
        f"What is the height of a complete binary tree with {n} nodes? (height of single node = 0)",
        str(height),
    )


def _gen_topological_sort(rng: random.Random):
    n = rng.randint(3, 6)
    tasks = [chr(65 + i) for i in range(n)]
    deps = []
    for i in range(n - 1):
        deps.append((tasks[i], tasks[i + 1]))
    if rng.random() < 0.5 and n > 3:
        deps.append((tasks[0], tasks[rng.randint(2, n - 1)]))
    deps_str = ", ".join(f"{a}->{b}" for a, b in deps)
    return (
        f"Given dependencies: {deps_str}, is there a valid topological ordering of {n} tasks?",
        "yes",
    )


def _gen_hash_bucket(rng: random.Random):
    num_buckets = rng.choice([5, 7, 10, 11])
    key = rng.randint(0, 100)
    bucket = key % num_buckets
    return (
        f"Using a hash table with {num_buckets} buckets and hash function h(k) = k mod {num_buckets}, which bucket does key {key} go to?",
        str(bucket),
    )


def _gen_binary_representation(rng: random.Random):
    n = rng.randint(1, 255)
    return (
        f"What is the binary representation of {n}?",
        bin(n)[2:],
    )


def _gen_hex_representation(rng: random.Random):
    n = rng.randint(0, 255)
    return (
        f"What is the hexadecimal representation of {n}?",
        hex(n)[2:],
    )


def _gen_base_conversion(rng: random.Random):
    n = rng.randint(1, 100)
    base = rng.choice([2, 8, 16])
    if base == 2:
        result = bin(n)[2:]
        base_name = "binary"
    elif base == 8:
        result = oct(n)[2:]
        base_name = "octal"
    else:
        result = hex(n)[2:]
        base_name = "hexadecimal"
    return (
        f"What is {n} in {base_name}?",
        result,
    )


def _gen_bit_count(rng: random.Random):
    n = rng.randint(0, 255)
    count = bin(n).count("1")
    return (
        f"How many 1-bits are in the binary representation of {n}?",
        str(count),
    )


def _gen_bit_shift(rng: random.Random):
    n = rng.randint(1, 32)
    shift = rng.randint(1, 4)
    direction = rng.choice(["left", "right"])
    if direction == "left":
        result = n << shift
        return (
            f"What is {n} left-shifted by {shift} bits?",
            str(result),
        )
    else:
        result = n >> shift
        return (
            f"What is {n} right-shifted by {shift} bits?",
            str(result),
        )


def _gen_xor_range(rng: random.Random):
    a = rng.randint(1, 50)
    b = rng.randint(a, a + 20)
    result = 0
    for i in range(a, b + 1):
        result ^= i
    return (
        f"What is the XOR of all integers from {a} to {b} inclusive?",
        str(result),
    )


def _gen_factorize(rng: random.Random):
    n = rng.choice([12, 15, 18, 20, 24, 30, 36, 42, 48, 60, 72, 84, 96, 120])
    factors = []
    d = 2
    temp = n
    while d * d <= temp:
        while temp % d == 0:
            factors.append(d)
            temp //= d
        d += 1
    if temp > 1:
        factors.append(temp)
    return (
        f"What is the prime factorization of {n}? Format: product of primes separated by x",
        "x".join(str(f) for f in factors),
    )


def _gen_largest_prime_factor(rng: random.Random):
    n = rng.choice([14, 15, 21, 35, 49, 77, 91, 143, 187, 221])
    d = 2
    temp = n
    largest = 2
    while d * d <= temp:
        while temp % d == 0:
            largest = d
            temp //= d
        d += 1
    if temp > 1:
        largest = temp
    return (
        f"What is the largest prime factor of {n}?",
        str(largest),
    )


def _gen_goldbach(rng: random.Random):
    even = rng.randint(4, 50) * 2
    max_prime = even - 2
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
    if max_prime > 47:
        for n in range(53, max_prime + 1, 2):
            if all(n % p != 0 for p in primes if p * p <= n):
                primes.append(n)
    for p in primes:
        q = even - p
        if q in primes and p <= q:
            return (
                f"Write {even} as the sum of two primes (smaller first). Format: a+b",
                f"{p}+{q}",
            )
    return (
        f"Write {even} as the sum of two primes (smaller first). Format: a+b",
        "no solution",
    )


def _gen_pi_digits(rng: random.Random):
    pi = "314159265358979323846264338327950288419716939937510"
    n = rng.randint(1, 5)
    return (
        f"What are the first {n} digits of pi after the decimal point?",
        pi[1:n+1],
    )


def _gen_triangle_number(rng: random.Random):
    n = rng.randint(1, 20)
    tri = n * (n + 1) // 2
    return (
        f"What is the {n}th triangular number?",
        str(tri),
    )


def _gen_square_free(rng: random.Random):
    n = rng.choice([2, 3, 5, 6, 7, 10, 11, 13, 14, 15])
    return (
        f"Is {n} square-free (no perfect square divides it other than 1)?",
        "yes",
    )


def _gen_square_not_free(rng: random.Random):
    n = rng.choice([4, 8, 9, 12, 16, 18, 20, 24, 25, 27])
    return (
        f"Is {n} square-free (no perfect square divides it other than 1)?",
        "no",
    )


def _gen_digit_product(rng: random.Random):
    n = rng.randint(10, 9999)
    product = 1
    for d in str(n):
        product *= int(d)
    return (
        f"What is the product of the digits of {n}?",
        str(product),
    )


def _gen_sum_of_squares(rng: random.Random):
    n = rng.randint(1, 20)
    squares = sum(i * i for i in range(1, n + 1))
    return (
        f"What is the sum of the first {n} perfect squares (1^2 + 2^2 + ...)?",
        str(squares),
    )


def _gen_triangular(rng: random.Random):
    n = rng.randint(2, 15)
    tri = n * (n + 1) // 2
    return (
        f"Is {tri} a triangular number?",
        "yes",
    )


def _gen_not_triangular(rng: random.Random):
    n = rng.choice([2, 3, 5, 6, 7, 8, 10, 11, 13, 14])
    tri = n * (n + 1) // 2 + 1
    return (
        f"Is {tri} a triangular number?",
        "no",
    )


GENERATORS = [
    _gen_sudoku_row,
    _gen_mastermind,
    _gen_nim_stone,
    _gen_tower_hanoi,
    _gen_clock_puzzle,
    _gen_kayak_river,
    _gen_paper_folding,
    _gen_binary_search,
    _gen_gcd_lcm,
    _gen_modular_inverse,
    _gen_euler_totient,
    _gen_combinatorial_count,
    _gen_permutation_count,
    _gen_partitions,
    _gen_collatz,
    _gen_digit_sum,
    _gen_reverse_digits,
    _gen_palindrome_check,
    _gen_maze_shortest,
    _gen_map_coloring,
    _gen_graph_diameter,
    _gen_binary_tree_height,
    _gen_topological_sort,
    _gen_hash_bucket,
    _gen_binary_representation,
    _gen_hex_representation,
    _gen_base_conversion,
    _gen_bit_count,
    _gen_bit_shift,
    _gen_xor_range,
    _gen_factorize,
    _gen_largest_prime_factor,
    _gen_goldbach,
    _gen_pi_digits,
    _gen_triangle_number,
    _gen_square_free,
    _gen_square_not_free,
    _gen_digit_product,
    _gen_sum_of_squares,
    _gen_triangular,
    _gen_not_triangular,
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
