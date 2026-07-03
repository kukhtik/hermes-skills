---
name: ml-model-improvement
description: Structured multi-stage ML model improvement pipeline — subagent validation, staged implementation, versioned delivery. For improving recognition accuracy (perks, addons, objects) through TTA, architecture changes, data augmentation, and two-stage verification.
category: mlops
---

# ML Model Improvement Pipeline

Structured workflow for improving ML model accuracy through staged, validated improvements.

## When to Use

- Improving classification/regression accuracy on a specific domain (games, objects, faces)
- Need to validate improvement logic before implementing
- User wants staged rollout with clear versioning
- Results need to be delivered to user via Telegram/file transfer

## Pipeline Stages

### 1. Analyze & Plan
1. Read and understand current model code (`*.py` files)
2. Identify accuracy bottlenecks (per-class error analysis)
3. Design improvements with expected impact

### 2. Subagent Validation (before implementing)
```
delegate_task → validate improvement logic on minimax-m2.7
```
Pass the full context: current accuracy, error cases, proposed changes.
Ask: "Оцени логичность улучшений" — subagent returns structured assessment.

### 3. Implement by Stages
Implement ONE improvement at a time. Each stage:
1. Modify code
2. Update `CHANGELOG.md` with stage details
3. Update version (v0.2.0, v0.3.0, etc.)
4. Create zip archive
5. Send to user via Telegram

### 4. Document Each Stage
```markdown
## Этап N: [Name]

**Дата:** YYYY-MM-DD
**Статус:** ✅ Готово / ⏳ Запланировано

### Что изменено
- File1: change
- File2: change

### Как тестировать
```powershell
# commands to run
```

### Ожидаемый результат
- +X% accuracy
- Trade-offs (speed, memory)
```

## Version Naming
- v0.1.0 — original
- v0.2.0 — stages 1-2 (no retraining)
- v0.3.0 — stage 3 (retraining required)
- v0.4.0 — stage 4 (experimental)

## File Delivery via Telegram
```bash
hermes send --to telegram:<user_id> --file <zip_path> "<message>"
```

## Accuracy Tracking Table
```markdown
| Метод | Точность |
|-------|----------|
| Baseline | X% |
| + Stage 1 | X% |
| + Stage 2 | X% |
```

## Common Improvement Patterns

### Test-Time Augmentation (TTA)
- Add rotation, flip, brightness variations at inference
- Near-free accuracy boost for contrastive models
- Config flags: `USE_TTA`, `TTA_ROTATION_DEGREES`, `TTA_BRIGHTNESS_RANGE`

### Input Resolution Increase
- 64→96 often helps for small icons (40px in HUD)
- Must retrain model after change

### Two-Stage Classification
- First predict class (killer), then verify attributes (addons belong to that class)
- Reduces false positives from cross-class confusion

### Edge/Silhouette Features
- Add Canny edges as additional input channel
- Helps distinguish objects with similar color but different shape
- Requires `--edges` flag during training

## Pitfalls
- Don't change multiple things at once — can't attribute improvement
- Always update CHANGELOG before zipping
- Retraining-required changes must be clearly flagged in docs
- Experimental features (like edge detection) should default OFF
- **hermes send --file limitation**: `hermes send --file` only works with text files. Binary files (ZIP, images, etc.) fail with "'utf-8' codec can't decode byte" error. Workaround: copy to `~/.hermes/cache/documents/` and send without `--file` flag, or use GitHub releases / direct file hosting.
- **User delivery expectation**: User expects actual file delivery via Telegram, not just text notifications. If sending ZIP, always use the file path approach (`~/.hermes/cache/documents/` + Hermes send) even if Hermes reports "sent" — the file must actually arrive. If Hermes file delivery fails, use Telegram Bot API directly via curl with the bot token. Never just send a text message saying "file is ready" — the user interprets this as ignoring their request.

## References

- `references/dbd-perks-case-study.md` — case study from DBDPerksAddonReveal project
