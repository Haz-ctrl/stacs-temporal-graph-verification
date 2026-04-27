# Threats to Validity

This document catalogues threats to the validity of the evaluation results produced by this framework. It is structured following the standard four-validity taxonomy (construct, internal, external, statistical), plus two domain-specific additions (formal-methods scope and dataset validity). Each section states what is threatened, the evidence from the repository, and the appropriate mitigation or caveat.

---

## Construct Validity

**What is threatened:** Whether the metrics operationalise the constructs they claim to measure.

- `parse_success_rate` operationalises structured-output reliability, not temporal reasoning ability. A model can score 1.0 while reasoning incorrectly.
- `conditional_validity_rate` operationalises internal structural self-consistency of the predicted graph, not agreement with gold temporal facts. Validity is a necessary but not sufficient signal for correctness.
- `fidelity_closure_f1_full` operationalises ordering recovery at the transitive closure level. It measures whether the model's ordering commitments align with the gold ordering, but does not measure whether the reasoning trace that produced those commitments is sound.
- The violation taxonomy (acyclicity, grounding, simultaneity consistency, etc.) is drawn from graph theory and the LTL fragment implemented in `src/constraints.py`. It is not derived from a cognitive or linguistic taxonomy of temporal reasoning errors.

**Mitigation:** The framework explicitly separates intrinsic (structural) metrics from gold (correctness) metrics. Dissertation claims should not conflate high intrinsic validity with high reasoning quality.

---

## Internal Validity

**What is threatened:** Whether observed differences reflect the intended variables rather than confounds.

- **Verifier not externally calibrated.** The constraint library in `src/constraints.py` has not been evaluated against human-annotated violation examples. It is possible that the verifier fires on valid predictions (false positives) or fails to fire on invalid ones (false negatives), distorting `conditional_validity_rate` comparisons across models.

- **Qwen 3.5 9B transport failure confound.** On the TempEval full run, Qwen 3.5 9B has a 19% transport failure rate (`transport_failure_rate = 0.190`). Tasks that failed to receive a response are treated as parse failures. Any comparative claim for Qwen on TempEval must acknowledge this infrastructure confound, as the model may have performed better or worse on the tasks it never processed.

- **Repair hit rate.** The JSON repair mechanism in `src/prediction_schema.py` may introduce systematic bias if it more frequently succeeds on structurally simpler outputs, artificially raising `parse_success_rate` for models that produce near-valid JSON.

**Mitigation:** Report `transport_failure_rate` alongside all Qwen comparisons. Do not rank models on TempEval without noting Qwen's infrastructure confound. Treat `conditional_validity_rate` as an instrument reading, not a ground-truth validity measure, until verifier calibration is performed.

---

## External Validity

**What is threatened:** Whether results generalise beyond the specific conditions of this study.

- **Model scale.** The five evaluated models (DeepSeek R1 7B, Qwen 3.5 9B, Llama 3.1 8B, Mistral 7B, Gemma 3 12B) are all in the 7B–12B parameter range. Findings may not generalise to smaller models (< 3B) or larger models (≥ 70B).

- **Benchmark scope.** Evaluation covers TempEval-3 Platinum event-event relations (one domain, conservative label mapping) and a controlled synthetic dataset. The synthetic dataset is author-constructed and may not reflect the distribution of temporal reasoning failures in real-world text.

- **Dataset conservatism.** The TempEval import uses a conservative coarse mapping that discards interval algebra relations (`INCLUDES`, `IS_INCLUDED`, `BEGINS`, `ENDS`, etc.), retaining only `BEFORE`, `AFTER`, `SIMULTANEOUS`, and `UNKNOWN`. Results are not representative of the full TimeML relation set.

- **Prompt sensitivity.** The structured prediction prompt is fixed across runs. Results reflect performance under this specific prompt; other prompting strategies may yield different ordering patterns.

**Mitigation:** Frame results as an analysis of 7B-scale models on event-ordering tasks under a specific structured prediction protocol. Avoid unqualified generalisations about LLM temporal reasoning.

---

## Statistical Validity

**What is threatened:** Whether numerical comparisons are statistically reliable.

- **Small per-cell n in category breakdowns.** The canonical synthetic dataset has 40 tasks per category (linear_chain, transitive_reasoning, ambiguous, contradiction). Category-level metrics are computed on n ≤ 40 tasks. Some subcells (e.g. parse failures within a category) may have n < 10. The 95% bootstrap confidence intervals in `summary.csv` cover run-level aggregates only; category-level CIs are not computed.

- **No significance tests.** Differences between models on any metric are not subjected to statistical significance testing. All comparisons are descriptive.

- **Bootstrap seed fixed.** The bootstrap CI computation uses `BOOTSTRAP_SEED = 7` in `src/run_summary.py`. This is intentional for reproducibility, but means CIs reflect one specific resampling sequence.

- **Single run per model.** Each model is evaluated once per dataset. Run-level variance (e.g. from temperature sampling) is not measured.

**Mitigation:** Mark any category-level metric computed on n < 30 with its n in tables (implemented as `num_tasks` column). Do not rank models based on small-n category differences. Describe all comparisons as descriptive rather than inferential.

---

## Formal-Methods Scope

**What is threatened:** Whether the LTL framing in the dissertation accurately describes what is implemented.

The verifier implements a **graph-grounded LTL fragment** over step-indexed reasoning traces, not general LTL model checking:

- Supported operators: `G` (globally), `F` (eventually), `X` (next step), `U` (until), and boolean connectives (`¬`, `∧`, `∨`).
- Supported predicates: `before(a,b)`, `after(a,b)`, `simultaneous(a,b)`, `unknown(a,b)`, `supports(edge)`, `mentions_event(e)`, `has_violation(kind)`.
- Traces are bounded (one step per reasoning annotation in the prediction); no unbounded state space is explored.
- Not supported: past-time operators, nested fixpoints, CTL* / μ-calculus, full TimeML interval algebra.

Claims of "LTL verification" in the dissertation should be scoped as "a graph-grounded LTL fragment over step-indexed traces." Claims of "model checking" should not be made without the above qualifications.

---

## Dataset Validity

**What is threatened:** Whether the datasets used support the evaluations claimed.

- **Synthetic dataset (author-constructed).** The canonical evaluation set (`data/temporal_reasoning_eval.jsonl`) was generated by `scripts/generate_temporal_dataset.py`, which is part of this repository. The generation procedure, the relation distribution, and the difficulty parameterisation all reflect the author's design choices. This introduces potential experimenter bias: the dataset may inadvertently favour the structured prediction format or the verifier's constraint coverage.

- **TempEval-3 IAA.** The TempEval-3 Platinum corpus has known inter-annotator agreement (IAA) limitations, particularly on `SIMULTANEOUS` and `UNKNOWN` labels. Gold labels in these categories are less reliable than `BEFORE`/`AFTER` labels. Results on SIMULTANEOUS tasks should be interpreted with this in mind.

  `TODO: verify IAA rate from TempEval paper and cite specific figures before final submission.`

- **Conservative label mapping.** The TempEval import discards relations outside {BEFORE, AFTER, SIMULTANEOUS, UNKNOWN}, so tasks involving interval relations are excluded. The remaining dataset skews toward simpler, directional event-event relations.

**Mitigation:** Clearly distinguish synthetic-dataset results from TempEval results in the dissertation. Treat synthetic results as controlled ablations and TempEval results as the external validity test. Flag SIMULTANEOUS category results with the IAA caveat.
