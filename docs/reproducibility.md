# Reproducibility Note

Each baseline run records:

- dataset path and derived dataset version
- model tag and provider metadata
- seed and decoding temperature
- prediction source (`llm`, `gold`, `empty`, `noisy`)
- code revision from `git rev-parse HEAD` when available

Outputs are written to a UTC-stamped directory under `outputs/runs/`.

## Recommended Workflow

1. Create and activate a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Validate the dataset before running experiments.
4. Keep model tag, seed, and temperature fixed for comparisons.
5. Preserve `config.json`, `predictions.jsonl`, and `report.json` for dissertation artefacts and supervisor demos.

## Determinism

The synthetic and non-LLM modes are deterministic with a fixed seed.

LLM mode depends on:

- the server-side model implementation
- sampling settings
- local model availability

The run report therefore stores model metadata and an Ollama tag snapshot when available.
