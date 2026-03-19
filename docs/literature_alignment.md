# Literature Alignment Note

This note maps the current repository to the dissertation survey and adjacent temporal reasoning literature.

## What the Project Aligns With

### Structured temporal reasoning evaluation

The project converts model outputs into typed temporal relations and scores them at both direct-edge and closure levels. This aligns with the broader literature theme that temporal reasoning should not be assessed only through surface-form answers.

### Temporal graph representation

The implementation now makes temporal commitments explicit in a graph-like structure, including ordering normalisation and simultaneity groups. This is consistent with the dissertation survey's emphasis on interpretable temporal structure.

### Verifiable failure analysis

The verifier returns explicit violation objects and counterexample metadata. This supports research questions around localising where inconsistency enters the reasoning process.

## What the Project Does Not Yet Fully Implement

### Full formal verification

The survey frames the project in terms of LTL and model-checking style verification. The repo currently implements a constraint library plus lightweight formal-spec direction, not a full general LTL parser and evaluator.

### External benchmark adapters

The survey mentions TempEval-style extraction and TORQUE-style temporal QA. The repo is currently strongest on a controlled synthetic dataset and structured prediction pipeline.

### Confidence and calibration analysis

The survey discusses comparing confidence against verification signals. That analysis layer is not yet present.

## Relation to Temporal Reasoning Literature

This project is best positioned as:

- a structured evaluation and failure-analysis framework for temporal reasoning outputs
- a temporal-graph-based verification scaffold for LLM reasoning traces
- a research software artefact that can support later benchmark and formal-spec expansion

For papers such as Time-R1 and other temporal reasoning evaluation work, the clearest overlap is:

- evaluating temporal reasoning beyond final answer accuracy
- isolating different temporal failure modes
- making temporal structure explicit for analysis

The clearest current gap is that this project revision is stronger on verification and scoring structure than on large-scale benchmark breadth or full formal temporal logic support.
