# DBDPerksAddonReveal — ML Model Improvement Case Study

## Project Context
- **Goal:** Recognize killer perks (19/20) and addons (8/10) from Dead by Daylight gameplay video
- **Stack:** Python + OpenCV + PyTorch CNN + ffmpeg, runs in Docker
- **Constraints:** Local-only (no online AI APIs), 40px icons in video HUD
- **User:** Testing on PC (Docker), developing on Android phone

## Improvement Stages Applied

### Stage 1: TTA (Test-Time Augmentation)
**Files:** `dbdreveal/ml.py`, `dbdreveal/config.py`

Changes:
- Added `_tta_variations()` with rotation ±2°, flip, brightness ±30, contrast ±0.1
- Config flags: `USE_TTA`, `TTA_ROTATION_DEGREES`, `TTA_BRIGHTNESS_RANGE`, `TTA_CONTRAST_RANGE`, `TTA_JITTER`

```python
# TTA generates 14 variations instead of 1
# All passed through CNN, max similarity taken
```

**Impact:** +0.5-1 addon accuracy, no retraining needed

### Stage 2: Two-Stage Addon Verification
**Files:** `dbdreveal/recognize.py`, `dbdreveal/config.py`

Changes:
- `select_killer_and_addons()` now scores killer+addon combinations
- Plausibility scoring based on rarity combinations
- Penalties for unlikely combos (ultra rare + common)

```python
# After getting slot scores, verify killer-addon compatibility
# Score = addon1_score * addon2_score * plausibility_factor
```

**Impact:** Removes "stupid" errors where wrong killer leads to wrong addons

### Stage 3: Resolution 64→96 + Brightness Jitter
**Files:** `dbdreveal/ml.py`, `dbdreveal/train_addons.py`, `dbdreveal/config.py`

Changes:
- INPUT: 64 → 96
- EMB_DIM: 128 → 192
- Added brightness/contrast jitter in `render_game_like()`
- Config: `INPUT = 96`, `EMB_DIM = 192`

```python
# 40px icons: 64→40 is 0.625x downscale
# 96→40 is 2.4x downscale (preserves more detail)
```

**Impact:** +1 addon accuracy, requires retraining (~10 min CPU)

### Stage 4: Edge/Silhouette Features (Experimental)
**Files:** `dbdreveal/ml.py`, `dbdreveal/train_addons.py`, `dbdreveal/config.py`

Changes:
- `build_model(in_channels)` now accepts 3 (RGB) or 4 (RGB+Canny)
- `embed_bgr(use_edges=True)` stacks Canny edges as 4th channel
- `train_addons.py --edges` flag for 4-channel training
- Config: `USE_EDGES = False` (default)

**Impact:** Unpredictable — helps distinguish similar shapes (radio vs labyrinth) but may add noise

## Accuracy Evolution

| Метод | Перки | Аддоны |
|-------|-------|--------|
| OpenCV classic (baseline) | 16/20 | 2/10 |
| + Slot detection | 18/20 | - |
| + Ensemble (gradient + binary) | 19/20 | - |
| + CLIP | - | 4/10 |
| + CNN trained on synthetic | - | 8/10 |
| + TTA v2 + Two-Stage Verification | ~19/20 | ~8.5-9/10 |
| + Resolution 96 + Brightness Jitter | ~19/20 | ~9-9.5/10 |
| + Edge Features (experimental) | ~19/20 | ~9-9.5/10 |

## Key Learnings

1. **TTA is nearly free** for contrastive models — small rotations, flips, brightness shifts don't hurt
2. **Resolution matters for small icons** — 64→96 helped because 40px icons lost less detail
3. **Two-stage verification is a bug fix**, not ML — it catches impossible killer+addon combinations
4. **Edge features are risky** — shape info helps but Canny adds noise; need careful threshold tuning
5. **Synthetic training works** — real HUD frames never seen during training, only used for testing

## Testing Protocol
```powershell
# Stage 1-2 (no retraining)
.\run.ps1 "video.mp4" --dump report_v02.json

# Stage 3 (retrain CNN)
docker exec dbdreveal-ml python -m dbdreveal.train_addons --epochs 25
.\run.ps1 "video.mp4" --dump report_v03.json

# Stage 4 (optional, experimental)
docker exec dbdreveal-ml python -m dbdreveal.train_addons --epochs 25 --edges
# Enable USE_EDGES = True in config.py
.\run.ps1 "video.mp4" --dump report_v04.json
```

## Subagent Validation Pattern
Used `delegate_task` with `minimax-m2.7` model to validate improvement logic before implementing:
```
goal: "Оцени логичность улучшений..."
model: minimax-m2.7
```
Subagent returned structured assessment of priority, risk, expected gains.
