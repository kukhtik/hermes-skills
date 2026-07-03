---
name: systematic-debugging
description: "4-phase root cause debugging: understand bugs before fixing."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, troubleshooting, problem-solving, root-cause, investigation]
    related_skills: [test-driven-development, writing-plans, subagent-driven-development]
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Someone wants it fixed NOW (systematic is faster than thrashing)

## The Four Phases

You MUST complete each phase before proceeding to the next.

---

## Phase 1: Build a Tight Feedback Loop

**"If you have a tight pass/fail signal for the bug — one that goes red on this bug — you will find the cause. If you don't have one, no amount of staring at code will save you."**

Everything else in this skill is mechanical. Spend disproportionate effort here. Be aggressive, creative, and relentless.

### Ways to Build the Loop (try in order)

1. **Failing test** at whatever seam reaches the bug — unit, integration, e2e
2. **Curl / HTTP script** against a running dev server
3. **CLI invocation** with a fixture input, diffing stdout against a known-good snapshot
4. **Headless browser script** (Playwright / Puppeteer) — drives the UI, asserts on DOM/console/network
5. **Replay a captured trace** — save a real network request / payload / event log to disk; replay through the code path in isolation
6. **Throwaway harness** — spin up a minimal subset of the system (one service, mocked deps) that exercises the bug code path with a single function call
7. **Property / fuzz loop** — if the bug is "sometimes wrong output", run 1000 random inputs and look for the failure mode
8. **Bisection harness** — if the bug appeared between two known states (commit, dataset, version), automate "boot at state X, check, repeat" so you can `git bisect run` it
9. **Differential loop** — run the same input through old-version vs new-version (or two configs) and diff outputs
10. **HITL bash script** — last resort. If a human must click, drive them with a structured loop script so the loop is still structured

### Tighten the Loop

Treat the loop as a product. Once you have a loop, tighten it:

- **Faster?** Cache setup, skip unrelated init, narrow the test scope
- **Sharper signal?** Assert on the specific symptom, not "didn't crash"
- **More deterministic?** Pin time, seed RNG, isolate filesystem, freeze network

A 30-second flaky loop is barely better than no loop; a 2-second deterministic one is a debugging superpower.

### Non-Deterministic Bugs

The goal is not a clean repro but a **higher reproduction rate**. Loop the trigger 100×, parallelize, add stress, narrow timing windows, inject sleeps. A 50%-flake bug is debuggable; 1% is not — keep raising the rate until it's debuggable.

### When You Genuinely Cannot Build a Loop

Stop and say so explicitly. List what you tried. Ask the user for: (a) access to the reproducing environment, (b) a captured artifact (HAR file, log dump, core dump, screen recording with timestamps), or (c) permission to add temporary production instrumentation. Do NOT proceed to hypothesize without a loop.

### Phase 1 Completion Criteria

Phase 1 is done when you can name **one command** — a script path, a test invocation, a curl — that you have **already run at least once**, and that is:

- [ ] **Red-capable** — it drives the actual bug code path and asserts the **user's exact symptom**. Not "runs without erroring" — it must catch this specific bug
- [ ] **Deterministic** — same verdict every run (or high, pinned reproduction rate for non-deterministic bugs)
- [ ] **Fast** — seconds, not minutes
- [ ] **Agent-runnable** — you can run it unattended; a human in the loop only via structured script

If you catch yourself reading code to build a theory before this command exists, **stop — jumping straight to a hypothesis is the exact failure this skill prevents.** No tight red-capable command, no Phase 2.

---

## Phase 2: Reproduce and Minimise

Run the loop. Watch it go red — the bug appears.

Confirm:
- [ ] The loop produces the failure mode the **user** described — not a different failure that happens to be nearby
- [ ] The failure is reproducible (or pinned at high rate for non-deterministic bugs)
- [ ] You captured the exact symptom (error message, wrong output, slow timing) so later phases can verify the fix

### Minimise

Once it's red, shrink the repro to the **smallest scenario that still goes red**. Cut inputs, callers, config, and data **one at a time**, re-running after each cut — keep only what's load-bearing for the failure.

Done when **every remaining element is load-bearing** — removing any one makes the loop go green.

Do not proceed until you have reproduced **and** minimised.
**STOP:** Do not proceed to Phase 2 until you understand WHY it's happening.

---

## Phase 3: Hypothesise

Generate **3–5 ranked hypotheses** before testing any of them. Single-hypothesis generation anchors on the first plausible idea.

Each hypothesis must be **falsifiable**: state the prediction it makes.

> Format: "If \<X\> is the cause, then \<changing Y\> will make the bug disappear / \<changing Z\> will make it worse."

If you cannot state the prediction, the hypothesis is a vibe — discard or sharpen it.

Show the ranked list to the user before testing. They often have domain knowledge that instantly re-ranks ("we just deployed a change to #3"), or know hypotheses already ruled out. Cheap checkpoint, big time saver. Proceed with your ranking if the user is AFK.

---

## Phase 4: Instrument

Each probe must map to a specific prediction from Phase 3. **Change one variable at a time.**

Tool preference:
1. **Debugger / REPL inspection** if the env supports it — one breakpoint beats ten logs
2. **Targeted logs** at the boundaries that distinguish hypotheses
3. Never "log everything and grep"

**Tag every debug log** with a unique prefix, e.g. `[DEBUG-a4f2]`. Cleanup at the end becomes a single grep. Untagged logs survive; tagged logs die.

**Perf branch.** For performance regressions, logs are usually wrong. Instead: establish a baseline measurement (timing harness, `performance.now()`, profiler, query plan), then bisect. Measure first, fix second.

---

## Phase 5: Fix and Regression Test

Write the regression test **before the fix** — but only if there is a **correct seam** for it.

A correct seam is one where the test exercises the **real bug pattern** as it occurs at the call site. If the only available seam is too shallow, a regression test there gives false confidence. Flag this.

If a correct seam exists:

1. Turn the minimised repro into a failing test at that seam
2. Watch it fail
3. Apply the fix
4. Watch it pass
5. Re-run the Phase 1 feedback loop against the original (un-minimised) scenario

---

## Phase 6: Cleanup and Post-Mortem

Required before declaring done:

- [ ] Original repro no longer reproduces (re-run the Phase 1 loop)
- [ ] Regression test passes (or absence of seam is documented)
- [ ] All `[DEBUG-...]` instrumentation removed (`grep` the prefix)
- [ ] Throwaway prototypes deleted (or moved to a clearly-marked debug location)
- [ ] The hypothesis that turned out correct is stated in the commit / PR message — so the next debugger learns

**Then ask: what would have prevented this bug?** If the answer involves architectural change, hand off to a codebase improvement skill. Make the recommendation **after** the fix is in, not before — you have more information now than when you started.

---

## Rule of Three

If 3+ fixes have failed, stop. This is not a failed hypothesis — this is a wrong architecture. Discuss with the user:
- Is the pattern fundamentally sound?
- Should we refactor the architecture vs. continue fixing symptoms?

---

## Red Flags — STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals a new problem in a different place**

**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ fixes failed:** Question the architecture (Phase 4 step 5).

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question the pattern, don't fix again. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Tight Loop** | Build red-capable, deterministic, fast, runnable feedback loop | One named command that goes red on this bug |
| **2. Reproduce+Minimise** | Run loop, confirm exact symptom, shrink repro to smallest load-bearing case | Every remaining element is load-bearing |
| **3. Hypothesise** | 3–5 ranked falsifiable hypotheses, show to user before testing | Each hypothesis states its prediction |
| **4. Instrument** | One variable at a time, tag logs `[DEBUG-xxx]`, perf: measure first | Each probe maps to a specific prediction |
| **5. Fix+Regression** | Failing test before fix at correct seam, verify pass | Original repro goes green, test locks bug down |
| **6. Cleanup** | Repro gone, instrumentation gone, commit msg states root cause | Ready for next task |

## Hermes Agent Integration

### Investigation Tools

Use these Hermes tools during Phase 1:

- **`search_files`** — Find error strings, trace function calls, locate patterns
- **`read_file`** — Read source code with line numbers for precise analysis
- **`terminal`** — Run tests, check git history, reproduce bugs
- **`web_search`/`web_extract`** — Research error messages, library docs

### With delegate_task

For complex multi-component debugging, dispatch investigation subagents:

```python
delegate_task(
    goal="Investigate why [specific test/behavior] fails",
    context="""
    Follow systematic-debugging skill:
    1. Read the error message carefully
    2. Reproduce the issue
    3. Trace the data flow to find root cause
    4. Report findings — do NOT fix yet

    Error: [paste full error]
    File: [path to failing code]
    Test command: [exact command]
    """,
    toolsets=['terminal', 'file']
)
```

### With test-driven-development

When fixing bugs:
1. Write a test that reproduces the bug (RED)
2. Debug systematically to find root cause
3. Fix the root cause (GREEN)
4. The test proves the fix and prevents regression

## Real-World Impact

From debugging sessions:
- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common

**No shortcuts. No guessing. Systematic always wins.**
