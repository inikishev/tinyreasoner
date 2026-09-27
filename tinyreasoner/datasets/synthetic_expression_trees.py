"""Synthetic dataset of expression trees for math and logic.

Generates random expression trees of configurable depth, evaluates/simplifies
them using sympy to guarantee correct answers. Covers arithmetic, boolean logic,
relational comparisons, algebraic simplification, substitution, and more.

Tree nodes: ('num', value) | ('var', name) | ('op', opname, *children)
Operators: add, sub, mul, div, pow, neg, and, or, xor, not, implies,
           lt, le, gt, ge, eq, ne

Should be correct, verified by Qwen3.7-Max
"""
import random
import re
import sympy as sp
from fractions import Fraction

from .. import chat_api


# ---------------------------------------------------------------------------
# Expression tree helpers
# ---------------------------------------------------------------------------

_VAR_NAMES = list('xyzabnpq')
_BOOL_VARS = list('PQRS')
_REL_SYMBOL = {
    'lt': '<', 'le': '≤', 'gt': '>', 'ge': '≥', 'eq': '=', 'ne': '≠',
}


def _rand_int(rng: random.Random, lo: int = -99, hi: int = 99):
    return ('num', rng.randint(lo, hi))


def _rand_var(rng: random.Random, names: list[str] | None = None):
    names = names or _VAR_NAMES
    return ('var', rng.choice(names))


def _rand_bool_var(rng: random.Random):
    return ('var', rng.choice(_BOOL_VARS))


# -- Arithmetic expression tree builders -----------------------------------

_ARITH_UNARY = ('neg',)
_ARITH_BINARY = ('add', 'sub', 'mul', 'div', 'pow')


def _build_arith_tree(
    rng: random.Random,
    depth: int = 0,
    max_depth: int = 8,
    with_vars: bool = False,
):
    """Build a random arithmetic expression tree (tuple-based)."""
    if depth >= max_depth:
        if with_vars and rng.random() < 0.35:
            return _rand_var(rng)
        return _rand_int(rng)

    op = rng.choice(_ARITH_UNARY + _ARITH_BINARY)

    if op == 'neg':
        child = _build_arith_tree(rng, depth + 1, max_depth, with_vars)
        return ('neg', child)

    left = _build_arith_tree(rng, depth + 1, max_depth, with_vars)
    right = _build_arith_tree(rng, depth + 1, max_depth, with_vars)

    if op == 'div' and _tree_eval_int(right) == 0:
        right = _rand_int(rng, 1, 9)

    if op == 'pow':
        # Keep exponent as a small non-negative integer
        if isinstance(right, tuple) and right[0] == 'num':
            e = abs(right[1]) % 5
            right = ('num', e)
        elif isinstance(right, tuple):
            right = ('num', rng.randint(0, 4))
        if _tree_is_zero(left) and _tree_is_zero(right):
            right = ('num', 2)

    return (op, left, right)


def _tree_is_zero(node) -> bool:
    return isinstance(node, tuple) and node[0] == 'num' and node[1] == 0


def _tree_eval_int(node) -> int:
    """Quickly evaluate a numeric (no variables) tree to an int if possible."""
    try:
        sp_expr = _tree_to_sympy(node)
        s = sp.simplify(sp_expr)
        if s.is_Integer:
            return int(s)
    except Exception:
        pass
    return 1  # conservative default


def _tree_to_sympy(node) -> sp.Expr:
    """Convert a tuple-based tree to a sympy expression (for evaluation)."""
    if node[0] == 'num':
        return sp.Integer(node[1])
    if node[0] == 'var':
        return sp.Symbol(node[1])
    if node[0] == 'neg':
        return -_tree_to_sympy(node[1])
    if node[0] == 'add':
        return _tree_to_sympy(node[1]) + _tree_to_sympy(node[2])
    if node[0] == 'sub':
        return _tree_to_sympy(node[1]) - _tree_to_sympy(node[2])
    if node[0] == 'mul':
        return _tree_to_sympy(node[1]) * _tree_to_sympy(node[2])
    if node[0] == 'div':
        return _tree_to_sympy(node[1]) / _tree_to_sympy(node[2])
    if node[0] == 'pow':
        return _tree_to_sympy(node[1]) ** _tree_to_sympy(node[2])
    raise ValueError(f"Unknown node type: {node[0]}")


def _tree_to_str(node, parent_prec: int = 0) -> str:
    """Convert a tree to a human-readable math string with parentheses.

    Precedence levels: 0=top, 1=add/sub, 2=mul/div, 3=pow/neg, 4=atom
    """
    tag = node[0]

    if tag == 'num':
        return str(node[1])
    if tag == 'var':
        return node[1]
    if tag == 'neg':
        child = _tree_to_str(node[1], 3)
        s = f"-({child})" if _tree_prec(node[1]) <= 1 else f"-{child}"
        return f"({s})" if parent_prec > 3 else s
    if tag == 'add':
        prec = 1
        left = _tree_to_str(node[1], prec)
        right = _tree_to_str(node[2], prec)
        s = f"{left} + {right}"
        return f"({s})" if parent_prec > prec else s
    if tag == 'sub':
        prec = 1
        left = _tree_to_str(node[1], prec)
        right = _tree_to_str(node[2], prec + 1)
        s = f"{left} - {right}"
        return f"({s})" if parent_prec > prec else s
    if tag == 'mul':
        prec = 2
        left = _tree_to_str(node[1], prec)
        right = _tree_to_str(node[2], prec)
        s = f"{left} × {right}"
        return f"({s})" if parent_prec > prec else s
    if tag == 'div':
        prec = 2
        left = _tree_to_str(node[1], prec + 1)
        right = _tree_to_str(node[2], prec + 1)
        s = f"{left} ÷ {right}"
        return f"({s})" if parent_prec > prec else s
    if tag == 'pow':
        prec = 3
        left = _tree_to_str(node[1], prec + 1)
        right = _tree_to_str(node[2], prec)
        s = f"{left}^{right}"
        return f"({s})" if parent_prec > prec else s
    return str(node)


def _tree_prec(node) -> int:
    """Return precedence level of a tree node."""
    tag = node[0]
    if tag in ('num', 'var'):
        return 4
    if tag in ('neg', 'pow'):
        return 3
    if tag in ('mul', 'div'):
        return 2
    if tag in ('add', 'sub'):
        return 1
    return 0


# -- Boolean expression tree builders --------------------------------------

_BOOL_UNARY = ('not',)
_BOOL_BINARY = ('and', 'or', 'xor', 'implies')


def _build_bool_tree(
    rng: random.Random,
    depth: int = 0,
    max_depth: int = 16,
    force_concrete: bool = False,
):
    """Build a random boolean expression tree.

    When force_concrete is True, all leaves are True/False constants.
    """
    if depth >= max_depth:
        if force_concrete or rng.random() < 0.5:
            return ('bool', rng.choice([True, False]))
        return _rand_bool_var(rng)

    op = rng.choice(_BOOL_UNARY + _BOOL_BINARY)
    if op == 'not':
        child = _build_bool_tree(rng, depth + 1, max_depth, force_concrete)
        return ('not', child)

    left = _build_bool_tree(rng, depth + 1, max_depth, force_concrete)
    right = _build_bool_tree(rng, depth + 1, max_depth, force_concrete)
    return (op, left, right)


def _bool_tree_to_sympy(node) -> sp.Expr:
    """Convert a boolean tree to a sympy expression."""
    if node[0] == 'bool':
        return sp.true if node[1] else sp.false
    if node[0] == 'var':
        return sp.Symbol(node[1])
    if node[0] == 'not':
        return ~_bool_tree_to_sympy(node[1])
    if node[0] == 'and':
        return sp.And(_bool_tree_to_sympy(node[1]), _bool_tree_to_sympy(node[2]))
    if node[0] == 'or':
        return sp.Or(_bool_tree_to_sympy(node[1]), _bool_tree_to_sympy(node[2]))
    if node[0] == 'xor':
        return sp.Xor(_bool_tree_to_sympy(node[1]), _bool_tree_to_sympy(node[2]))
    if node[0] == 'implies':
        return sp.Implies(_bool_tree_to_sympy(node[1]), _bool_tree_to_sympy(node[2]))
    raise ValueError(f"Unknown boolean node: {node[0]}")


def _bool_tree_to_str(node, parent_op: str | None = None) -> str:
    """Convert a boolean tree to a human-readable string."""
    if node[0] == 'bool':
        return str(node[1])
    if node[0] == 'var':
        return node[1]
    if node[0] == 'not':
        child = _bool_tree_to_str(node[1], 'not')
        return f"NOT {child}"
    if node[0] == 'and':
        left = _bool_tree_to_str(node[1], 'and')
        right = _bool_tree_to_str(node[2], 'and')
        s = f"{left} AND {right}"
        return f"({s})" if parent_op in ('not', 'xor', 'implies') else s
    if node[0] == 'or':
        left = _bool_tree_to_str(node[1], 'or')
        right = _bool_tree_to_str(node[2], 'or')
        s = f"{left} OR {right}"
        return f"({s})" if parent_op in ('not', 'and', 'xor', 'implies') else s
    if node[0] == 'xor':
        left = _bool_tree_to_str(node[1], 'xor')
        right = _bool_tree_to_str(node[2], 'xor')
        s = f"{left} XOR {right}"
        return f"({s})" if parent_op in ('not', 'and', 'or', 'implies') else s
    if node[0] == 'implies':
        left = _bool_tree_to_str(node[1], 'implies')
        right = _bool_tree_to_str(node[2], 'implies')
        s = f"{left} IMPLIES {right}"
        return f"({s})" if parent_op in ('not', 'and', 'or', 'xor', 'implies') else s
    return str(node)


def _bool_is_binary(node) -> bool:
    return node[0] in ('and', 'or', 'xor', 'implies')


def _eval_bool_with_assignment(sp_expr, assignments: dict) -> bool:
    """Evaluate a boolean sympy expression with concrete truth assignments."""
    subs = {}
    for var, val in assignments.items():
        subs[sp.Symbol(var)] = sp.true if val else sp.false
    result = sp_expr.subs(subs)
    if result == sp.true:
        return True
    if result == sp.false:
        return False
    return bool(result)


# -- Relational expression tree builders -----------------------------------

_REL_BINARY = ('lt', 'le', 'gt', 'ge', 'eq', 'ne')


def _build_rel_tree(rng: random.Random):
    """Build a relational expression tree."""
    left = _build_arith_tree(rng, max_depth=rng.randint(2, 3))
    right = _build_arith_tree(rng, max_depth=rng.randint(2, 3))
    op = rng.choice(_REL_BINARY)
    return (op, left, right)


def _rel_tree_to_str(node) -> str:
    """Convert a relational tree to a string."""
    op_sym = _REL_SYMBOL[node[0]]
    left = _tree_to_str(node[1])
    right = _tree_to_str(node[2])
    return f"{left} {op_sym} {right}"


def _rel_tree_to_sympy(node) -> sp.Expr | None:
    """Convert a relational tree to a sympy expression.

    Returns None if the comparison is invalid (e.g. non-real values).
    """
    try:
        left = _tree_to_sympy(node[1])
        right = _tree_to_sympy(node[2])
    except Exception:
        return None
    op = node[0]
    try:
        if op == 'lt':
            return left < right
        if op == 'le':
            return left <= right
        if op == 'gt':
            return left > right
        if op == 'ge':
            return left >= right
        if op == 'eq':
            return sp.Eq(left, right)
        if op == 'ne':
            return sp.Ne(left, right)
        return left > right
    except TypeError:
        return None


# ---------------------------------------------------------------------------
# Generator functions
# ---------------------------------------------------------------------------

def _gen_arithmetic_eval(rng: random.Random) -> tuple[str, str]:
    """Evaluate a random arithmetic expression tree."""
    tree = _build_arith_tree(rng, max_depth=rng.randint(2, 4))
    expr_str = _tree_to_str(tree)
    sp_expr = _tree_to_sympy(tree)
    ans_str = str(sp.simplify(sp_expr))
    return (
        f"Evaluate the expression: {expr_str}",
        ans_str,
    )


def _gen_deep_arithmetic_eval(rng: random.Random) -> tuple[str, str]:
    """Evaluate a deeper arithmetic expression tree."""
    tree = _build_arith_tree(rng, max_depth=rng.randint(4, 6))
    expr_str = _tree_to_str(tree)
    sp_expr = _tree_to_sympy(tree)
    ans_str = str(sp.simplify(sp_expr))
    return (
        f"What is the value of {expr_str}? Write it as an integer or simplified fraction.",
        ans_str,
    )


def _gen_simplify_expression(rng: random.Random) -> tuple[str, str]:
    """Simplify an algebraic expression."""
    tree = _build_arith_tree(rng, max_depth=rng.randint(2, 3), with_vars=True)
    expr_str = _tree_to_str(tree)
    sp_expr = _tree_to_sympy(tree)
    simplified = sp.simplify(sp_expr)
    ans_str = str(simplified)
    return (
        f"Simplify the expression: {expr_str}",
        ans_str,
    )


def _gen_expand_expression(rng: random.Random) -> tuple[str, str]:
    """Expand an algebraic expression."""
    a = rng.randint(-5, 5)
    b = rng.randint(-5, 5)
    expr_type = rng.choice(['product', 'square', 'power3'])

    x = sp.Symbol('x')
    if expr_type == 'product':
        expr = (x + a) * (x + b)
        expr_str = f"(x + {a}) × (x + {b})" if a >= 0 and b >= 0 else f"(x - {abs(a)}) × (x - {abs(b)})" if a < 0 and b < 0 else f"(x {'+' if a >= 0 else '-'} {abs(a)}) × (x {'+' if b >= 0 else '-'} {abs(b)})"
    elif expr_type == 'square':
        expr = (x + a) ** 2
        expr_str = f"(x {'+' if a >= 0 else '-'} {abs(a)})²"
    else:
        expr = (x + a) ** 3
        expr_str = f"(x {'+' if a >= 0 else '-'} {abs(a)})³"
    if a == 0 and b == 0:
        expr_str = "x × x"

    expanded = sp.expand(expr)
    ans_str = str(expanded)
    return (
        f"Expand the expression: {expr_str}",
        ans_str,
    )


def _gen_substitute_eval(rng: random.Random) -> tuple[str, str]:
    """Substitute a value into an expression and evaluate."""
    var_name = rng.choice(['x', 'y', 'z'])
    var = sp.Symbol(var_name)
    val = rng.randint(-10, 10)

    tree = _build_arith_tree(rng, max_depth=rng.randint(2, 3), with_vars=True)
    sp_expr = _tree_to_sympy(tree)
    had_var = var in sp_expr.free_symbols
    if not had_var:
        sp_expr = sp_expr + var
    tree_str = _tree_to_str(tree)

    # Rebuild string with guaranteed variable
    if not had_var:
        tree_str = f"{tree_str} + {var_name}"

    evaluated = sp_expr.subs({var: val})
    ans_str = str(sp.simplify(evaluated))
    return (
        f"If {var_name} = {val}, evaluate {tree_str}",
        ans_str,
    )


def _gen_boolean_eval(rng: random.Random) -> tuple[str, str]:
    """Evaluate a concrete boolean expression (no variables)."""
    tree = _build_bool_tree(
        rng, max_depth=rng.randint(1, 2), force_concrete=True
    )
    sp_expr = _bool_tree_to_sympy(tree)
    result = sp_expr == sp.true
    expr_str = _bool_tree_to_str(tree)
    return (
        f"Evaluate this boolean expression: {expr_str}",
        str(result),
    )


def _gen_boolean_with_assignment(rng: random.Random) -> tuple[str, str]:
    """Evaluate a boolean expression with variable assignments."""
    tree = _build_bool_tree(rng, max_depth=rng.randint(2, 3))
    sp_expr = _bool_tree_to_sympy(tree)

    free_vars = sorted(sp_expr.free_symbols, key=str)
    if not free_vars:
        return _gen_boolean_with_assignment(rng)

    assignments = {}
    assign_strs = []
    for fv in free_vars:
        val = rng.choice([True, False])
        assignments[str(fv)] = val
        assign_strs.append(f"{fv} = {val}")

    result = _eval_bool_with_assignment(sp_expr, assignments)
    expr_str = _bool_tree_to_str(tree)
    assign_str = ", ".join(assign_strs)
    return (
        f"If {assign_str}, what is the truth value of ({expr_str})?",
        str(result),
    )


def _gen_logical_equivalence(rng: random.Random) -> tuple[str, str]:
    """Check if two boolean expressions are logically equivalent."""
    mode = rng.choice(['equivalent', 'not_equivalent'])
    vname = rng.choice(_BOOL_VARS)

    def _v(name):
        return ('var', name)

    if mode == 'equivalent':
        pair_type = rng.choice(['double_neg', 'demorgan', 'distribute'])
        if pair_type == 'double_neg':
            e1 = _v(vname)
            e2 = ('not', ('not', _v(vname)))
        elif pair_type == 'demorgan':
            other = rng.choice([n for n in _BOOL_VARS if n != vname])
            e1 = ('not', ('and', _v(vname), _v(other)))
            e2 = ('or', ('not', _v(vname)), ('not', _v(other)))
        else:
            others = [n for n in _BOOL_VARS if n != vname]
            other1 = rng.choice(others)
            other2 = rng.choice([n for n in others if n != other1])
            e1 = ('and', _v(vname), ('or', _v(other1), _v(other2)))
            e2 = ('or', ('and', _v(vname), _v(other1)), ('and', _v(vname), _v(other2)))
    else:
        e1 = _v(vname)
        e2 = ('not', _v(vname))

    e1_str = _bool_tree_to_str(e1)
    e2_str = _bool_tree_to_str(e2)
    e1_sp = _bool_tree_to_sympy(e1)
    e2_sp = _bool_tree_to_sympy(e2)

    is_equiv = sp.simplify_logic(e1_sp ^ e2_sp) == sp.false
    expected = "Yes" if is_equiv else "No"

    return (
        f"Are the following two expressions logically equivalent?\n"
        f"1: {e1_str}\n2: {e2_str}",
        expected,
    )


def _gen_inequality_check(rng: random.Random) -> tuple[str, str]:
    """Check if an inequality/equality holds (all concrete values)."""
    for _ in range(10):
        tree = _build_rel_tree(rng)
        sp_expr = _rel_tree_to_sympy(tree)
        if sp_expr is not None:
            rel_str = _rel_tree_to_str(tree)
            try:
                result = bool(sp_expr)
            except Exception:
                result = False
            return (
                f"Is the following statement true or false?\n{rel_str}",
                str(result),
            )
    return "Is 1 = 1?", "True"


def _gen_expression_compare(rng: random.Random) -> tuple[str, str]:
    """Compare two arithmetic expressions: which is larger/smaller?"""
    t1 = _build_arith_tree(rng, max_depth=rng.randint(2, 3))
    t2 = _build_arith_tree(rng, max_depth=rng.randint(2, 3))
    s1 = _tree_to_str(t1)
    s2 = _tree_to_str(t2)
    e1 = _tree_to_sympy(t1)
    e2 = _tree_to_sympy(t2)

    try:
        v1 = float(e1.evalf())
        v2 = float(e2.evalf())
    except Exception:
        return _gen_expression_compare(rng)

    if abs(v1 - v2) < 0.001:
        return _gen_expression_compare(rng)

    if v1 > v2:
        return (
            f"Which expression is larger: {s1} or {s2}?",
            s1,
        )
    else:
        return (
            f"Which expression is larger: {s1} or {s2}?",
            s2,
        )


def _gen_modular_expression(rng: random.Random) -> tuple[str, str]:
    """Evaluate an arithmetic expression and take modulo."""
    tree = _build_arith_tree(rng, max_depth=rng.randint(2, 3))
    modulus = rng.randint(2, 12)
    sp_expr = _tree_to_sympy(tree)
    simplified = sp.simplify(sp_expr)
    if not simplified.is_Integer:
        return _gen_modular_expression(rng)
    val = int(simplified)
    result = val % modulus
    expr_str = _tree_to_str(tree)
    return (
        f"What is ({expr_str}) mod {modulus}?",
        str(result),
    )


def _gen_fraction_expression(rng: random.Random) -> tuple[str, str]:
    """Evaluate an expression involving fractions."""
    a, b = rng.randint(1, 12), rng.randint(1, 12)
    c, d = rng.randint(1, 12), rng.randint(1, 12)

    op = rng.choice(['add', 'sub', 'mul', 'div'])
    f1 = Fraction(a, b)
    f2 = Fraction(c, d)

    if op == 'add':
        result = f1 + f2
        symbol = '+'
    elif op == 'sub':
        result = f1 - f2
        symbol = '-'
    elif op == 'mul':
        result = f1 * f2
        symbol = '×'
    else:
        result = f1 / f2
        symbol = '÷'

    ans_str = (f"{result.numerator}/{result.denominator}"
               if result.denominator != 1 else str(result.numerator))
    return (
        f"What is {a}/{b} {symbol} {c}/{d}? "
        f"Give the answer as a simplified fraction or integer.",
        ans_str,
    )


def _gen_polynomial_eval(rng: random.Random) -> tuple[str, str]:
    """Evaluate a polynomial at a given point."""
    x = sp.Symbol('x')
    degree = rng.randint(1, 4)
    coeffs = [rng.randint(-5, 5) for _ in range(degree + 1)]
    poly = sum(coeffs[i] * x ** (degree - i) for i in range(degree + 1))

    pt = rng.randint(-5, 5)
    val = poly.subs({x: pt})

    def _poly_to_nice_str(coeffs, degree):
        terms = []
        deg = degree
        first = True
        for c in coeffs:
            if c == 0:
                deg -= 1
                continue
            if deg == 0:
                term = str(c)
            elif deg == 1:
                term = f"{c}x" if abs(c) != 1 else ("x" if c > 0 else "-x")
            else:
                term = f"{c}x^{deg}" if abs(c) != 1 else (f"x^{deg}" if c > 0 else f"-x^{deg}")
            if first:
                terms.append(term)
                first = False
            else:
                if c > 0:
                    terms.append(f" + {term}")
                else:
                    terms.append(f" - {term[1:]}" if term.startswith('-') else f" - {term}")
            deg -= 1
        return "".join(terms)

    nice_str = _poly_to_nice_str(coeffs, degree)
    return (
        f"Given the polynomial P(x) = {nice_str}, find P({pt}).",
        str(val),
    )


def _gen_equation_solve(rng: random.Random) -> tuple[str, str]:
    """Solve a simple linear or quadratic equation."""
    x = sp.Symbol('x')
    mode = rng.choice(['linear', 'quadratic'])

    if mode == 'linear':
        a = rng.choice([i for i in range(-10, 11) if i != 0])
        b = rng.randint(-20, 20)
        solution = rng.randint(-10, 10)
        rhs = a * solution + b
        a_str = "" if a == 1 else f"-" if a == -1 else str(a)
        return (
            f"Solve for x: {a_str}x + {b} = {rhs}",
            str(solution),
        )
    else:
        a = rng.choice([1, 2])
        b = rng.randint(-10, 10)
        c = rng.randint(-10, 10)
        discrim = b * b - 4 * a * c
        if discrim <= 0:
            return _gen_equation_solve(rng)
        solutions = sp.solve(a * x ** 2 + b * x + c, x)
        sol_strs = [str(s) for s in sorted(solutions, key=float)]
        a_str = "" if a == 1 else str(a)
        b_str = f" + {b}x" if b > 0 else f" - {abs(b)}x" if b < 0 else ""
        c_str = f" + {c}" if c > 0 else f" - {abs(c)}" if c < 0 else ""
        return (
            f"Solve for x: {a_str}x²{b_str}{c_str} = 0",
            ", ".join(sol_strs),
        )


def _gen_truth_table_row(rng: random.Random) -> tuple[str, str]:
    """Evaluate a boolean expression with specific variable assignments."""
    tree = _build_bool_tree(rng, max_depth=rng.randint(2, 3))
    sp_expr = _bool_tree_to_sympy(tree)
    free_vars = sorted(sp_expr.free_symbols, key=str)
    if not free_vars:
        return _gen_truth_table_row(rng)

    assignments = {}
    assign_strs = []
    for fv in free_vars:
        val = rng.choice([True, False])
        assignments[str(fv)] = val
        assign_strs.append(f"{fv} = {val}")

    result = _eval_bool_with_assignment(sp_expr, assignments)
    expr_str = _bool_tree_to_str(tree)
    assign_str = ", ".join(assign_strs)
    return (
        f"In the truth table of the expression ({expr_str}), "
        f"what is the output when {assign_str}?",
        str(result),
    )


def _gen_nested_boolean(rng: random.Random) -> tuple[str, str]:
    """Evaluate a deeply nested boolean expression without variables."""
    tree = _build_bool_tree(
        rng, max_depth=rng.randint(3, 5), force_concrete=True
    )
    sp_expr = _bool_tree_to_sympy(tree)
    result = sp_expr == sp.true
    expr_str = _bool_tree_to_str(tree)
    return (
        f"Evaluate this boolean expression step by step:\n{expr_str}",
        str(result),
    )


def _gen_mixed_expression(rng: random.Random) -> tuple[str, str]:
    """Mix arithmetic and relational operators, resulting in a boolean."""
    for _ in range(10):
        tree = _build_rel_tree(rng)
        sp_expr = _rel_tree_to_sympy(tree)
        if sp_expr is not None:
            rel_str = _rel_tree_to_str(tree)
            try:
                result = bool(sp_expr)
            except Exception:
                result = False
            return (
                f"Determine if this statement is true or false: {rel_str}",
                str(result),
            )
    return "Determine if this statement is true or false: 1 = 1", "true"


def _gen_derivative_basic(rng: random.Random) -> tuple[str, str]:
    """Compute the derivative of a simple expression."""
    x = sp.Symbol('x')
    expr = _build_arith_tree(rng, max_depth=rng.randint(1, 2), with_vars=True)
    sp_expr = _tree_to_sympy(expr)
    had_x = x in sp_expr.free_symbols
    if not had_x:
        sp_expr = sp_expr + x

    deriv = sp.diff(sp_expr, x)
    expr_str = _tree_to_str(expr)
    # Rebuild question if variable was added
    if not had_x:
        expr_str = f"{expr_str} + x"
    ans_str = str(sp.simplify(deriv))
    return (
        f"Find the derivative of the function f(x) = {expr_str}",
        ans_str,
    )


def _gen_simplify_boolean(rng: random.Random) -> tuple[str, str]:
    """Simplify a boolean expression."""
    tree = _build_bool_tree(rng, max_depth=rng.randint(2, 3))
    sp_expr = _bool_tree_to_sympy(tree)
    simplified = sp.simplify_logic(sp_expr)
    expr_str = _bool_tree_to_str(tree)
    ans_str = str(simplified)
    ans_str = ans_str.replace('&', ' AND ').replace('|', ' OR ').replace('~', 'NOT ').replace('^', ' XOR ')
    ans_str = re.sub(r'Implies\(([^,]+),\s*([^)]+)\)', r'\1 IMPLIES \2', ans_str)
    if ans_str == 'True':
        ans_str = 'True'
    elif ans_str == 'False':
        ans_str = 'False'
    return (
        f"Simplify the boolean expression: {expr_str}",
        ans_str,
    )


def _gen_expr_math_word_problem(rng: random.Random) -> tuple[str, str]:
    """A word-style problem that requires building and evaluating an expression."""
    problem_type = rng.choice(['age', 'consecutive', 'digit', 'money'])

    if problem_type == 'age':
        x = rng.randint(2, 15)
        now_mult = rng.randint(2, 5)
        future_add = rng.randint(5, 20)

        child_now = x
        parent_now = now_mult * x
        future = child_now + future_add
        ratio_expr = (parent_now + future_add) / future
        try:
            ratio_val = float(ratio_expr)
        except Exception:
            ratio_val = 0.0
        if ratio_val != int(ratio_val) or ratio_val < 1:
            return _gen_expr_math_word_problem(rng)
        return (
            f"A parent is {now_mult} times as old as their child. "
            f"The child is {child_now} years old. "
            f"In {future_add} years, how many times as old will the parent be?",
            str(int(ratio_val)),
        )

    elif problem_type == 'consecutive':
        n = rng.randint(3, 8)
        start = rng.randint(1, 20)
        total = sum(list(range(start, start + n)))
        return (
            f"What is the sum of {n} consecutive integers starting from {start}?",
            str(total),
        )

    elif problem_type == 'digit':
        tens = rng.randint(1, 9)
        ones = rng.randint(0, 9)
        number = 10 * tens + ones
        reversed_num = 10 * ones + tens
        diff = abs(number - reversed_num)
        return (
            f"The tens digit of a number is {tens} and the ones digit is {ones}. "
            f"What is the absolute difference between the number "
            f"and the number with digits reversed?",
            str(diff),
        )

    else:
        n_items = rng.randint(2, 5)
        price = rng.randint(5, 50) * 10
        paid = rng.randint(1, 5) * 100
        total_cost = n_items * price
        if total_cost >= paid:
            return _gen_expr_math_word_problem(rng)
        change = paid - total_cost
        return (
            f"You buy {n_items} items at "
            f"${price // 100}.{price % 100:02d} each "
            f"and pay with ${paid // 100}.{paid % 100:02d}. "
            f"How much change do you get?",
            f"${change // 100}.{change % 100:02d}",
        )


# ---------------------------------------------------------------------------
# GENERATORS list
# ---------------------------------------------------------------------------

GENERATORS = [
    _gen_arithmetic_eval,
    _gen_deep_arithmetic_eval,
    _gen_simplify_expression,
    _gen_expand_expression,
    _gen_substitute_eval,
    _gen_boolean_eval,
    _gen_boolean_with_assignment,
    _gen_logical_equivalence,
    _gen_inequality_check,
    _gen_expression_compare,
    _gen_modular_expression,
    _gen_fraction_expression,
    _gen_polynomial_eval,
    _gen_equation_solve,
    _gen_truth_table_row,
    _gen_nested_boolean,
    _gen_mixed_expression,
    _gen_derivative_basic,
    _gen_simplify_boolean,
    _gen_expr_math_word_problem,
]


# ---------------------------------------------------------------------------
# Standard dataset interface
# ---------------------------------------------------------------------------

def _make_sample(question: str, answer: str) -> list[chat_api.BaseItem]:
    return [
        chat_api.UserMessage(f"{question.replace('True','true').replace('False','false').replace('  ', ' ')}\nOnly include the answer in your response."),
        chat_api.AssistantMessage(answer.replace('True','true').replace('False','false').replace('  ', ' ')),
    ]

def _is_over_limit(s: str):
    l = 0
    for c in s:
        if c.isnumeric(): l += 1
        else: l = 0
        if l >= 5: return True
    return False

def load(n: int = 1000, seed: int | None = 0) -> list[list[chat_api.BaseItem]]:
    rng = random.Random(seed)
    samples = []
    for _ in range(n):
        gen = rng.choice(GENERATORS)
        question, answer = gen(rng)
        while _is_over_limit(answer):
            question, answer = gen(rng)
        samples.append(_make_sample(question, answer.replace("**", "^")))
    return samples
