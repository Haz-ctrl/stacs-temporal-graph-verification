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

## TempEval Slice

`data/tempeval_eval.jsonl` is an external evaluation slice derived from TempEval-3 Platinum TimeML annotations.

It is intentionally a coarse event-event subset:

- source corpus: TempEval-3 Platinum test documents
- unit of evaluation: one event-event TLINK per task
- retained relations: `BEFORE`, `IBEFORE`, `AFTER`, `IAFTER`, `SIMULTANEOUS`, `IDENTITY`
- coarse mapping:
  - `BEFORE`, `IBEFORE` -> `BEFORE`
  - `AFTER`, `IAFTER` -> `AFTER`
  - `SIMULTANEOUS`, `IDENTITY` -> `SIMULTANEOUS`
- excluded relations: interval-specific labels such as `INCLUDES`, `IS_INCLUDED`, `BEGINS`, `ENDS`

This keeps the benchmark slice aligned with the current graph semantics without overstating support for the full TimeML relation algebra.

## MATRES Slice

`data/matres_balanced_small.jsonl` is an external evaluation slice derived from MATRES TimeBank and AQUAINT relations, joined against the matching TempEval-3 TimeML documents by `eiid`.

It is intentionally a balanced event-event subset:

- source relation files: MATRES `timebank.txt` and `aquaint.txt`
- source documents: TempEval-3 TimeBank/AQUAINT TimeML files
- unit of evaluation: one MATRES event-event relation per task
- retained relations: `BEFORE`, `AFTER`, `EQUAL`, `VAGUE`
- coarse mapping:
  - `BEFORE` -> `BEFORE`
  - `AFTER` -> `AFTER`
  - `EQUAL` -> `SIMULTANEOUS`
  - `VAGUE` -> `UNKNOWN`

The `UNKNOWN` labels originate from MATRES `VAGUE`. They should be reported through direct/pairwise label metrics and abstention behaviour, not ordering-closure F1, because `UNKNOWN` intentionally contributes no ordering edge to the temporal graph.

## Legacy Files

Some files under `data/` predate the canonical schema or use older category names. They are retained for exploratory work and fixtures, but the recommended runnable dataset is:

`data/temporal_reasoning_eval.jsonl`
