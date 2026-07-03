# Test Charter Templates

## Basic Charter
```
CHARTER: Explore [TARGET] with [APPROACH] to discover [RISK]
DURATION: [45-90] min
FOCUS: [specific area]
RESOURCES: [test data, tools, environment needed]
```

## Session Report Template
```
## Session Report

**Charter:** [charter text]
**Tester:** [name]
**Date:** [YYYY-MM-DD]
**Duration:** [actual minutes]
**Environment:** [staging/local/production-mirror]

### Findings
| # | Severity | Description | Steps to reproduce |
|---|----------|-------------|-------------------|
| 1 | High     | ...         | ...               |
| 2 | Medium   | ...         | ...               |

### Coverage
- Areas explored: [list]
- Areas skipped: [list + reason]
- Bugs found: [count]
- Questions raised: [list]

### Debrief notes
- [What worked, what didn't, what to charter next]
```

## Charter Library — By Risk Type

### Security Charters
```
CHARTER: Explore authentication with malformed tokens to discover bypass vulnerabilities
DURATION: 90 min
FOCUS: JWT parsing, token expiry, role escalation, empty/null tokens
```

```
CHARTER: Explore file upload with crafted filenames (path traversal, double extensions) to discover RCE
DURATION: 60 min
FOCUS: ../../etc/passwd, shell.php.jpg, unicode filenames, null byte injection
```

### Performance Charters
```
CHARTER: Explore API endpoints with concurrent requests (1000 RPS) to discover rate-limiting and race conditions
DURATION: 90 min
FOCUS: Connection pool exhaustion, DB deadlock, memory leaks under load
```

```
CHARTER: Explore bulk operations with maximum payload size to discover OOM and timeout behavior
DURATION: 60 min
FOCUS: 10MB JSON body, 10000-item arrays, nested depth 100+, long strings
```

### Data Integrity Charters
```
CHARTER: Explore database operations with concurrent writes to the same record to discover lost updates
DURATION: 90 min
FOCUS: Optimistic locking gaps, race conditions, transaction isolation level mismatches
```

```
CHARTER: Explore encoding/decoding roundtrip with unicode/emoji/RTL to discover data corruption
DURATION: 60 min
FOCUS: UTF-8 boundaries, surrogate pairs, zero-width chars, combining sequences
```

### Edge Case Charters
```
CHARTER: Explore date/time handling across timezone boundaries and DST transitions to discover off-by-one errors
DURATION: 60 min
FOCUS: UTC midnight, DST spring-forward, Feb 29, year boundary, negative timestamps
```

```
CHARTER: Explore numeric inputs with boundary values (0, -1, MAX_INT, float precision) to discover overflow and underflow
DURATION: 45 min
FOCUS: Integer overflow, float NaN/Infinity, division by zero, negative zero
```

### UI/UX Charters
```
CHARTER: Explore forms with extreme input lengths and special characters to discover layout breaks and XSS
DURATION: 60 min
FOCUS: 10000-char input, HTML tags in fields, RTL text, emoji in names
```

```
CHARTER: Explore navigation with browser back/forward and double-click to discover duplicate submissions and state corruption
DURATION: 45 min
FOCUS: CSRF tokens, idempotency, double-submit, stale cache
```

### API Contract Charters
```
CHARTER: Explore API with missing/extra/null fields in request body to discover silent failures and crashes
DURATION: 60 min
FOCUS: Required fields omitted, extra unknown fields, null vs empty string, type coercion
```

```
CHARTER: Explore API pagination with extreme page sizes and offsets to discover DoS and data leaks
DURATION: 45 min
FOCUS: page=0, page=-1, limit=999999, offset=MAX_INT, cursor wraparound
```