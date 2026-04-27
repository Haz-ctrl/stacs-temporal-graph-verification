# Limitations and Known Issues

## Current Formal Scope

The verifier is a typed constraint library, not a full general-purpose LTL model checker.

It provides a practical formal-spec direction for:

- antisymmetry
- cycle detection
- simultaneity consistency
- grounding constraints
- reasoning-support consistency

## Dataset Coverage

The canonical synthetic dataset is still dominated by `BEFORE` relations. The code now supports richer relation semantics than the default dataset exercises.

## Benchmark Breadth

The repo now includes a TempEval-3 Platinum event-event import path, but only through a conservative coarse mapping onto the current relation set.

It does not yet support the full TimeML interval algebra end-to-end, and it still does not include broader benchmark adapters such as TORQUE.

## Visualisation

The dissertation survey emphasises visualisation and step-localised counterexamples. The current code returns structured counterexample metadata, but there is not yet a dedicated visual playback or graph-rendering module in the repo.

## Confidence Analysis

The survey also mentions confidence and calibration analysis. That is not yet implemented in the current pipeline. Structured prediction outputs include optional per-step and per-answer confidence fields (captured in `predictions.jsonl`), but no analysis of these fields is performed.

## Research Question 3 (RQ3)

RQ3 — whether graph-based metrics and formal violation counts better predict task correctness than self-reported confidence — is **explicitly scoped as future work for the final dissertation**. The inference pipeline currently does not capture per-step token-level logprob signals; adding this capability and running the correlation analysis is deferred. See `docs/rq3_future_work.md` for the concrete plan.
