# RQ3 Future Work: Confidence–Verification Correlation

## Status

**RQ3 is explicitly scoped as future work for the final dissertation.** At interim submission, no confidence–verification correlation analysis has been run. The research question remains in the project framing but is not addressed by the current pipeline.

The structured prediction schema (`src/schemas.py`) captures optional `confidence` fields in `ReasoningStep` and `ModelPrediction`. These fields are parsed from model JSON output if present and stored in `predictions.jsonl`. They are not yet analysed.

---

## Research Question

> Do graph-based metrics (violation counts, closure coverage) and formal verification flags (`is_valid`, `trace_grounded`) better predict task correctness than the model's self-reported per-step confidence?

This operationalises as: is Spearman ρ between verification-derived features and gold-label correctness larger than Spearman ρ between self-reported confidence and gold-label correctness?

---

## What Needs to Change

### 1. Logprob capture in `src/ollama_client.py`

The Ollama `/api/generate` endpoint returns a `logprobs` field when the request includes `"logprobs": true`. The current `OllamaClient.generate()` ignores this field.

**Change required:** Add a `capture_logprobs: bool = False` parameter. When true, include `"logprobs": true` in the request payload and return the logprob array alongside the text response. Estimated cost: ~2 hours.

```python
# In OllamaClient.generate():
if capture_logprobs:
    payload["logprobs"] = True
# Return body.get("logprobs", []) alongside body.get("response")
```

**Caution:** Not all Ollama backends expose logprobs for all model formats. This must be validated against the specific models (llama.cpp GGUF via Ollama supports logprobs since v0.1.33). If logprobs are unavailable, fall back to self-reported confidence only.

### 2. Per-step confidence signal options

Three options exist, with different cost/quality trade-offs:

| Signal | Description | Cost | Quality |
|--------|-------------|------|---------|
| **Token-level entropy** | H = -Σ p_i log p_i over the vocabulary at each token position; requires logprobs. Captures model uncertainty at the finest granularity. | Medium (requires logprobs capture + storage) | High (direct uncertainty signal) |
| **Sequence logprob** | Sum of token log-probabilities across the reasoning step; also requires logprobs. Captures overall generation plausibility. | Medium (same as above) | Medium |
| **Self-reported confidence** | The `confidence` field already parsed from the model's JSON output. No additional API calls needed. | None (already captured) | Low (often miscalibrated; models frequently output 0.9 regardless of actual uncertainty) |

**Recommended path for final dissertation:** Start with self-reported confidence (already available) for the correlation analysis, then add sequence logprob if logprob capture proves feasible on the lab setup. Token-level entropy requires per-token logprobs which are expensive to store (496 tasks × ~200 tokens = ~100K logprob values per run).

### 3. Correlation analysis design

For each task in a run:

- **Confidence signal** (x): average self-reported confidence across reasoning steps, or sequence logprob for the full prediction.
- **Correctness signal** (y): binary indicator — does the task's gold label match the predicted label? Derived from `pairwise_task_audit.csv` (already computed in `scripts/evaluate_pairwise_run.py`).
- **Verification signal** (z): `is_valid` (0/1), `trace_grounded` (0/1), violation count (integer).

Compute:
- Spearman ρ(x, y) — confidence vs. correctness
- Spearman ρ(z, y) — each verification feature vs. correctness

RQ3 is answered if ρ(z, y) consistently dominates ρ(x, y) across models and both datasets. A two-sided permutation test (B = 10,000 permutations) can establish significance; this requires n ≥ 30 per cell.

A new module `src/analysis/confidence_correlation.py` should implement this, following the same pattern as `src/analysis/axis_correlation.py`.

### 4. Storage changes

Per-task logprobs (if captured) should be stored in a separate sidecar file alongside `predictions.jsonl` to avoid inflating the main record size. Suggested format: `predictions_logprobs.jsonl` with one JSON object per task containing `{"id": ..., "step_logprobs": [...]}`.

---

## Estimated Engineering Cost

| Component | Estimated time |
|-----------|---------------|
| Logprob capture in OllamaClient | ~2 hours |
| Per-run logprob storage (sidecar file) | ~1 hour |
| Confidence correlation analysis module | ~4 hours |
| Re-run inference with logprob capture enabled | ~4 hours (lab compute time, not engineering) |
| Report integration and tests | ~2 hours |
| **Total** | **~9 hours engineering + lab rerun** |

---

## Open Questions

1. Does the Ollama version installed in the lab environment support logprob output for the GGUF models used? This must be verified before committing to the logprob path.
2. Are self-reported confidence values from the current models meaningfully calibrated? Preliminary inspection of `predictions.jsonl` shows many tasks have `confidence: null` — models do not consistently populate this field.
3. Should the correlation be computed at the task level (one confidence value per task) or the step level (one confidence value per reasoning step)? Step-level gives more data points but requires care to avoid within-task autocorrelation inflating ρ.
