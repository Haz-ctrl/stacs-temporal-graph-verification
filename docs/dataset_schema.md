# Dataset Schema Note

## Canonical Task Schema

Each JSONL row must be a single object with the following fields:

```json
{
  "id": "lc_001",
  "category": "linear_chain",
  "question": "A happened before B.",
  "events": ["A", "B"],
  "gold_relations": [["A", "B", "BEFORE"]],
  "expected_valid": true,
  "expected_consistent": true
}
```

## Field Semantics

- `id`: unique task identifier
- `category`: dataset/task family label
- `question`: natural-language temporal reasoning prompt
- `events`: canonical event names used for grounding
- `gold_relations`: gold temporal relation triples
- `expected_valid`: whether the gold structure is expected to be valid
- `expected_consistent`: whether the gold structure is expected to be temporally consistent

## Current Dataset Scope

The canonical synthetic dataset currently uses `BEFORE` relations for gold annotations and category-specific validation rules such as:

- `linear_chain`
- `transitive_reasoning`
- `ambiguous`
- `contradiction`
- `long_chain`

The graph and scoring code supports additional relation labels (`AFTER`, `SIMULTANEOUS`, `UNKNOWN`), but the canonical synthetic generator has not yet expanded gold dataset coverage to those labels.

## Legacy Files

Some files under `data/` predate the canonical schema or use older category names. They are retained for exploratory work and fixtures, but the recommended runnable dataset is:

`data/temporal_reasoning_eval.jsonl`
