#!/usr/bin/env python3
"""
Property-based testing templates using Hypothesis.

Install: pip install hypothesis pytest

Run: pytest tests/property/ -v
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis.strategies import (
    integers, floats, text, lists, dictionaries, 
    booleans, dates, datetimes, binary, composite
)


# ============================================================
# 1. Roundtrip Property — encode/decode symmetry
# ============================================================

@given(st.text())
@settings(max_examples=500)
def test_json_roundtrip(s):
    """json.dumps → json.loads returns original string."""
    import json
    assert json.loads(json.dumps(s)) == s


@given(st.text())
def test_base64_roundtrip(s):
    """base64 encode/decode is symmetric."""
    import base64
    encoded = base64.b64encode(s.encode()).decode()
    assert base64.b64decode(encoded).decode() == s


# ============================================================
# 2. Commutativity / Associativity — math functions
# ============================================================

@given(st.integers(), st.integers())
def test_add_commutative(a, b):
    """a + b == b + a for all integers."""
    assert a + b == b + a


@given(st.integers(), st.integers(), st.integers())
def test_add_associative(a, b, c):
    """(a + b) + c == a + (b + c)."""
    assert (a + b) + c == a + (b + c)


@given(st.integers(), st.integers())
def test_multiply_distributes_over_add(a, b, c=0):
    """a * (b + c) == a*b + a*c. (simplified: b=0 case)"""
    # Full version with c:
    pass  # Replace with actual function under test


# ============================================================
# 3. Idempotency — applying twice = applying once
# ============================================================

@given(st.lists(st.integers()))
def test_sort_idempotent(lst):
    """sort(sort(x)) == sort(x)."""
    sorted_once = sorted(lst)
    sorted_twice = sorted(sorted_once)
    assert sorted_once == sorted_twice


@given(st.text())
def test_dedup_idempotent(s):
    """Removing duplicates twice = once."""
    chars_once = list(dict.fromkeys(s))
    chars_twice = list(dict.fromkeys(chars_once))
    assert chars_once == chars_twice


# ============================================================
# 4. Invariant — property holds after operation
# ============================================================

@given(st.lists(st.integers(), min_size=1))
def test_max_is_in_list(lst):
    """max(lst) is always an element of lst."""
    assert max(lst) in lst


@given(st.lists(st.integers()))
def test_sum_preserved_after_sort(lst):
    """sum(lst) == sum(sorted(lst))."""
    assert sum(lst) == sum(sorted(lst))


@given(st.lists(st.integers(min_value=0, max_value=100), min_size=2))
def test_filter_reduces_or_maintains_size(lst):
    """Filtering never increases list size."""
    filtered = [x for x in lst if x > 50]
    assert len(filtered) <= len(lst)


# ============================================================
# 5. Boundary — extreme values
# ============================================================

@given(st.integers(min_value=0, max_value=2**31 - 1))
def test_non_negative_squares_are_non_negative(n):
    """n² >= 0 for all non-negative n."""
    assert n * n >= 0


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_float_abs_is_non_negative(x):
    """abs(x) >= 0 for all finite floats."""
    assert abs(x) >= 0


# ============================================================
# 6. State Machine — sequential operations
# ============================================================

from hypothesis.stateful import RuleBasedStateMachine, rule, initialize


class StackMachine(RuleBasedStateMachine):
    """Test a stack implementation through random operations."""
    
    def __init__(self):
        super().__init__()
        self.stack = []
        self.model = []  # Reference implementation
    
    @rule(value=st.integers())
    def push(self, value):
        self.stack.append(value)
        self.model.append(value)
    
    @rule()
    def pop(self):
        if self.stack:
            assert self.stack.pop() == self.model.pop()
    
    @rule()
    def peek(self):
        if self.stack:
            assert self.stack[-1] == self.model[-1]
    
    @rule()
    def check_size(self):
        assert len(self.stack) == len(self.model)


TestStackMachine = StackMachine.TestCase


# ============================================================
# 7. Custom strategies — domain-specific generators
# ============================================================

@composite
def valid_email(draw):
    """Generate syntactically valid emails."""
    local = draw(text(min_size=1, max_size=20, alphabet=st.characters(blacklist_categories=('Cs',))))
    domain = draw(text(min_size=1, max_size=10))
    tld = draw(text(min_size=2, max_size=4, alphabet='abcdefghijklmnopqrstuvwxyz'))
    return f"{local}@{domain}.{tld}"


@given(valid_email())
def test_email_validation_accepts_valid(email_str):
    """Validator accepts all syntactically valid emails."""
    # assert is_valid_email(email_str)  # Replace with actual validator
    assert '@' in email_str


@composite
def json_value(draw, max_depth=3):
    """Generate arbitrary JSON-compatible values."""
    depth_strategy = st.integers(min_value=0, max_value=max_depth)
    return draw(st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(),
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=5),
            st.dictionaries(st.text(min_size=1), children, max_size=5),
        ),
        max_leaves=10,
    ))


@given(json_value())
def test_json_serialize_roundtrip(value):
    """Any JSON value survives serialize → parse roundtrip."""
    import json
    serialized = json.dumps(value)
    parsed = json.loads(serialized)
    assert parsed == value


# ============================================================
# 8. API Contract — Schemathesis style
# ============================================================

# Requires: pip install schemathesis
# Run: pytest tests/property/test_api_contract.py -v

# import schemathesis
#
# schema = schemathesis.from_uri("http://localhost:8080/openapi.json")
#
# @schema.parametrize()
# def test_api_no_500_errors(case):
#     """No valid API call should return 500."""
#     response = case.call()
#     case.validate_response(response)
#
# @schema.parametrize(endpoint="/users/{user_id}")
# def test_get_user_returns_validated_schema(case):
#     """GET /users/{id} returns matching schema."""
#     response = case.call()
#     case.validate_response(response)


if __name__ == "__main__":
    # Quick self-test
    print("Running property tests...")
    pytest.main([__file__, "-v", "--tb=short"])