# Progressive Disclosure and Information Hierarchy

Adapted from mattpocock/skills `writing-great-skills` — MIT.

A skill exists to wrangle determinism out of a stochastic system. **Predictability** — the agent taking the same process every run, not producing the same output — is the root virtue.

## The Information Ladder

Three tiers, ranked by how immediately the agent needs the material:

1. **In-skill step** — ordered action in SKILL.md. Primary tier: what the agent does, in order. Each step ends on a **completion criterion** — the condition that tells the agent the work is done. Make it checkable and, where it matters, exhaustive. A vague criterion invites **premature completion**.

2. **In-skill reference** — definition, rule, or fact in SKILL.md, consulted on demand. Often legitimately flat (every rule on one rung). Fine arrangement, not a smell.

3. **External reference** — pushed out of SKILL.md into a linked file (sibling like `GLOSSARY.md`, or fully external). Reached by a **context pointer** loaded only when it fires.

Push too little down and the top bloats; push too much and you hide material the agent actually needs. That tension is the whole decision.

**Co-location** decides what sits beside it once there: keep a concept's definition, rules, and caveats under one heading rather than scattered.

## Leading Words

A **leading word** is a compact concept already living in the model's pretraining that the agent thinks with while running the skill (e.g. _lesson_, _fog of war_, _tracer bullets_). Repeated throughout the text, it accumulates a distributed definition and anchors a whole region of behaviour in the fewest tokens.

It serves predictability twice:
- In the body it anchors **execution** — the agent reaches for the same behaviour every time the word appears
- In the description it anchors **invocation** — when the same word lives in prompts, docs, and code, the agent links that shared language to the skill

Hunt for restatements begging to collapse into a single pretrained word.

## When to Split

Two cuts:

- **By invocation** — split off a model-invoked skill when you have a distinct leading word that should trigger it independently. Context load cost must be worth the independent reach.
- **By sequence** — split steps when post-completion steps tempt the agent to rush the current one (**premature completion**). Hiding them encourages more legwork.

## Failure Modes

- **Premature completion** — sharpen completion criterion first; only split if irreducibly fuzzy AND rush is observed
- **Duplication** — same meaning in more than one place; costs tokens and maintenance
- **Sediment** — stale layers that settle because adding feels safe and removing feels risky
- **Sprawl** — skill too long even when every line is unique; disclose reference behind pointers, split by branch
- **No-op** — line the model already obeys; test: does it change behaviour vs default? Fix with a stronger leading word, not different technique

## Pruning

Keep each meaning in a **single source of truth**. Hunt no-ops sentence by sentence: when one fails, delete the whole sentence rather than trim. Be aggressive — most prose that fails should go, not be rewritten.

## Model-invoked vs User-invoked

- **Model-invoked** (omit `disable-model-invocation`): agent can fire it autonomously, contributes to context load
- **User-invoked** (`disable-model-invocation: true`): only you typing its name can invoke it; zero context load, but you pay cognitive load

Pick model-invocation only when the agent or another skill must reach it independently. If it only fires by hand, make it user-invoked.

When user-invoked skills multiply past what you can remember, that cognitive load is cured by a **router skill** — one user-invoked skill naming the others and when to reach for each.
