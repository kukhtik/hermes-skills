# DeepSpec — Speculative Decoding Full-Stack

**URL:** https://github.com/deepseek-ai/DeepSpec
**Stars:** ~5,969 (844/day) | **Age:** 7 days | **Language:** Python
**Topics:** speculative-decoding, draft-models, llm-inference

## Summary
DeepSeek's full-stack codebase for training and evaluating draft models for speculative decoding. Data preparation, model implementations, training code, evaluation pipeline.

## What to take
- **Speculative decoding architecture**: draft model + verifier pattern for LLM inference acceleration
- **Training pipeline**: data prep → train draft model → evaluate → deploy
- **Evaluation framework**: metrics for speculative decoding quality (acceptance rate, speedup)

## Applicability
- **MPT**: if using local LLM inference — speculative decoding can accelerate Ollama models
- **Vetka_dwg**: Qwen2VL inference could benefit from speculative decoding
- **Hermes Agent**: — нет прямого применения (agent orchestration, not inference)
- **PIVOBOT / geo-converter / FAMILY_TREE / DBDPerksAddonReveal**: — нет прямого применения