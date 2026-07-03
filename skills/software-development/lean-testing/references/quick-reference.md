# Testing Quick Reference Card

## Test Types Decision Tree

```
What am I testing?
│
├── Pure function / algorithm
│   └── Unit tests + Property-based tests (Hypothesis)
│
├── Module interaction / API contract
│   └── Integration tests + Contract tests (Pact)
│
├── Full user workflow
│   └── E2E tests (Playwright/Cypress) — 3-5 critical paths max
│
├── "Does it boot after deploy?"
│   └── Smoke tests (curl health endpoint)
│
├── "Did my change break something?"
│   └── Regression tests (automated, CI-triggered)
│
├── "What happens if X dies?"
│   └── Chaos test (Chaos Mesh / Gremlin)
│
├── "Is it fast enough?"
│   └── Performance test (Locust / k6 / Gatling)
│
├── "Can I hack it?"
│   └── Security test (Bandit / OWASP ZAP / fuzzing)
│
└── "What haven't I thought of?"
    └── Exploratory session (test charter, 60-90 min)
```

## Coverage Targets (Adjust Per Project)

| Metric | Minimum | Good | Excellent |
|--------|---------|------|-----------|
| Line coverage | 60% | 80% | 95%+ |
| Branch coverage | 50% | 70% | 85%+ |
| Mutation score | 40% | 60% | 80%+ |
| Test ratio (unit:other) | 50% | 70% | 80%+ |
| Flaky test rate | <5% | <1% | 0% |
| Avg unit test time | <200ms | <100ms | <50ms |

## Test Naming Conventions

```
test_{unit}_{scenario}_{expected_result}

Examples:
test_parser_handles_empty_input_returns_none
test_auth_token_expired_raises_InvalidTokenError
test_sort_large_list_completes_under_100ms
test_api_post_with_missing_field_returns_400
```

## When to Mock vs Real

| Situation | Mock | Real |
|-----------|------|------|
| External API (Stripe, Twilio) | ✅ | ❌ |
| Database (unit tests) | ✅ | ❌ |
| Database (integration tests) | ❌ | ✅ (test DB) |
| File system (unit tests) | ✅ | ❌ |
| File system (integration) | ❌ | ✅ (tmp dir) |
| Time / random | ✅ (always) | ❌ |
| Network / HTTP | ✅ (unit) | ✅ (integration) |
| Third-party SDK | ✅ | ❌ |

## Test Data Strategies

```python
# 1. Inline — simple, visible
def test_add():
    assert add(2, 3) == 5

# 2. Factory — reusable, parameterized
@pytest.mark.parametrize("a, b, expected", [
    (1, 1, 2),
    (0, 0, 0),
    (-1, 1, 0),
    (100, 200, 300),
])
def test_add_cases(a, b, expected):
    assert add(a, b) == expected

# 3. Fixtures — setup/teardown with lifecycle
@pytest.fixture
def db():
    db = create_test_db()
    yield db          # Test runs here
    db.drop_all()     # Cleanup

def test_user_creation(db):
    db.create_user("test@example.com")
    assert db.count_users() == 1

# 4. Property-based — auto-generated
@given(st.integers(), st.integers())
def test_add_commutative(a, b):
    assert add(a, b) == add(b, a)

# 5. Builder — complex objects
class UserBuilder:
    def __init__(self):
        self._name = "default"
        self._email = "default@test.com"
    def with_name(self, name):
        self._name = name
        return self
    def with_email(self, email):
        self._email = email
        return self
    def build(self):
        return User(name=self._name, email=self._email)

def test_profile_display():
    user = UserBuilder().with_name("Alice").with_email("alice@test.com").build()
    assert user.display_name == "Alice"
```

## Testing Checklist (Before Merge)

- [ ] New code has unit tests
- [ ] All tests pass locally
- [ ] No new flaky tests
- [ ] Coverage on changed files > 80%
- [ ] Critical paths have integration tests
- [ ] Edge cases covered (empty, null, max, boundary)
- [ ] Error paths tested (not just happy path)
- [ ] Test names are descriptive
- [ ] No tests > 5s in unit suite
- [ ] No hardcoded credentials / paths in tests
- [ ] CI pipeline passes
- [ ] At least one exploratory session on new feature