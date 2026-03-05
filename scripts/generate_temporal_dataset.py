from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Literal, Optional, Sequence, Tuple, TypedDict

Relation = Literal["BEFORE"]
Category = Literal[
    "linear_chain",
    "transitive_reasoning",
    "ambiguous",
    "contradiction",
    "long_chain",
]

Edge = Tuple[str, str, Relation]


class Task(TypedDict):
    id: str
    category: Category
    question: str
    events: List[str]
    gold_relations: List[List[str]]  # JSON-friendly: [a,b,"BEFORE"]
    expected_consistent: bool
    expected_valid: bool


@dataclass(frozen=True)
class Config:
    seed: int
    n_linear: int
    n_transitive: int
    n_ambiguous: int
    n_contradiction: int
    n_long: int
    out_path: Path


VERBS: List[str] = [
    "opened the door",
    "closed the window",
    "sent an email",
    "packed a bag",
    "started the car",
    "made tea",
    "read the note",
    "locked the bike",
    "washed the dishes",
    "turned on the kettle",
    "paid the bill",
    "set an alarm",
    "called a friend",
    "printed the handouts",
    "started the meeting",
    "uploaded the file",
    "downloaded the update",
    "installed the update",
    "watered the plants",
    "fed the cat",
    "charged the phone",
    "checked the battery",
    "wrote the code",
    "ran the tests",
    "approved the release",
    "boarded the train",
    "left the station",
    "finished the lecture",
    "submitted the form",
    "received a confirmation email",
]

NAMES: List[str] = [
    "Ava", "Mia", "Sam", "Priya", "Leo", "Nora", "Kai", "Lina", "Omar", "Zara",
    "Noah", "Ivy", "Ethan", "Sofia", "Hana", "Ben", "Amir", "Ruby", "Jon", "Sara",
]

PLACES: List[str] = [
    "at home", "at the office", "at the station", "in the kitchen", "in the library",
    "in the lab", "at the café", "in the garden", "in the hallway", "in the classroom",
]

# Natural language connectors to vary surface forms a bit
CONNECTORS: List[str] = [
    "Before that,", "After that,", "Then,", "Next,", "Later,", "Afterwards,", "Immediately after,",
]


def _json_edge(e: Edge) -> List[str]:
    a, b, r = e
    return [a, b, r]


def _write_jsonl(path: Path, items: Iterable[Task]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for obj in items:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _unique_events(rng: random.Random, k: int) -> List[str]:
    """
    Produce k distinct event strings of the form "<Name> <verb> <place>".
    """
    # sample without replacement where possible
    verbs = rng.sample(VERBS, k=k) if k <= len(VERBS) else [rng.choice(VERBS) for _ in range(k)]
    names = [rng.choice(NAMES) for _ in range(k)]
    places = [rng.choice(PLACES) for _ in range(k)]

    events: List[str] = []
    seen: set[str] = set()
    for i in range(k):
        e = f"{names[i]} {verbs[i]} {places[i]}"
        # ensure uniqueness even if random collisions happen
        if e in seen:
            e = f"{names[i]} {verbs[i]} {places[i]} (step {i+1})"
        seen.add(e)
        events.append(e)
    return events


def _make_chain_edges(events: Sequence[str]) -> List[Edge]:
    edges: List[Edge] = []
    for i in range(len(events) - 1):
        edges.append((events[i], events[i + 1], "BEFORE"))
    return edges


def _transitive_closure_from_chain(chain_edges: Sequence[Edge]) -> List[Edge]:
    """
    Given edges A->B, B->C, C->D ...
    return closure edges (including the original), e.g. A->C, A->D, B->D, etc.
    Only supports BEFORE.
    """
    # reconstruct ordered list from chain edges
    if not chain_edges:
        return []

    # chain_edges are consecutive; gather nodes in order
    nodes: List[str] = [chain_edges[0][0], chain_edges[0][1]]
    for a, b, _ in chain_edges[1:]:
        # assume valid chain; append b
        nodes.append(b)

    out: List[Edge] = []
    n = len(nodes)
    for i in range(n):
        for j in range(i + 1, n):
            out.append((nodes[i], nodes[j], "BEFORE"))
    return out


def _linear_chain_task(rng: random.Random, idx: int) -> Task:
    n_events = rng.choice([3, 3, 4])  # mostly 3
    events = _unique_events(rng, n_events)
    edges = _make_chain_edges(events)

    # Build a simple narrative using connectors
    parts: List[str] = []
    parts.append(f"{events[0]}.")
    for i in range(1, len(events)):
        cue = rng.choice(CONNECTORS)
        parts.append(f"{cue} {events[i]}.")
    question = " ".join(parts)

    return {
        "id": f"lc_{idx:03d}",
        "category": "linear_chain",
        "question": question,
        "events": events,
        "gold_relations": [_json_edge(e) for e in edges],
        "expected_consistent": True,
        "expected_valid": True
    }


def _transitive_reasoning_task(rng: random.Random, idx: int) -> Task:
    # 3 events is enough to require A->C inference
    n_events = rng.choice([3, 3, 4])
    events = _unique_events(rng, n_events)
    chain_edges = _make_chain_edges(events)
    closure_edges = _transitive_closure_from_chain(chain_edges)

    # Narrative: explicitly state only consecutive steps, not the implied ones
    parts: List[str] = []
    for i in range(len(events) - 1):
        parts.append(f"{events[i]} happened before {events[i+1]}.")
    question = " ".join(parts)

    return {
        "id": f"tr_{idx:03d}",
        "category": "transitive_reasoning",
        "question": question,
        "events": events,
        "gold_relations": [_json_edge(e) for e in closure_edges],
        "expected_consistent": True,
        "expected_valid": True,
    }


def _ambiguous_task(rng: random.Random, idx: int) -> Task:
    n_events = rng.choice([2, 2, 3])
    events = _unique_events(rng, n_events)

    # Narrative without any ordering cues
    sentences = [f"{e}." for e in events]
    question = " ".join(sentences)

    return {
        "id": f"amb_{idx:03d}",
        "category": "ambiguous",
        "question": question,
        "events": events,
        "gold_relations": [],
        "expected_consistent": True,
        "expected_valid": True
    }


def _contradiction_task(rng: random.Random, idx: int) -> Task:
    # minimal contradiction with 2 events: A before B AND B before A
    events = _unique_events(rng, 2)
    a, b = events[0], events[1]
    edges: List[Edge] = [(a, b, "BEFORE"), (b, a, "BEFORE")]

    # Explicit contradiction in text
    question = f"{a} happened before {b}, but {b} happened before {a}."

    return {
        "id": f"con_{idx:03d}",
        "category": "contradiction",
        "question": question,
        "events": list(events),
        "gold_relations": [_json_edge(e) for e in edges],
        "expected_consistent": False,
        "expected_valid": False
    }


def _long_chain_task(rng: random.Random, idx: int) -> Task:
    n_events = rng.choice([5, 6, 7])
    events = _unique_events(rng, n_events)
    edges = _make_chain_edges(events)

    # More verbose but still a straightforward chain
    parts: List[str] = []
    parts.append(f"First, {events[0]}.")
    for i in range(1, len(events)):
        cue = rng.choice(["Then", "Next", "After that", "Later"])
        parts.append(f"{cue}, {events[i]}.")
    question = " ".join(parts)

    return {
        "id": f"long_{idx:03d}",
        "category": "long_chain",
        "question": question,
        "events": events,
        "gold_relations": [_json_edge(e) for e in edges],
        "expected_consistent": True,
        "expected_valid": True,
    }


def generate_dataset(cfg: Config) -> List[Task]:
    rng = random.Random(cfg.seed)
    tasks: List[Task] = []

    for i in range(1, cfg.n_linear + 1):
        tasks.append(_linear_chain_task(rng, i))

    for i in range(1, cfg.n_transitive + 1):
        tasks.append(_transitive_reasoning_task(rng, i))

    for i in range(1, cfg.n_ambiguous + 1):
        tasks.append(_ambiguous_task(rng, i))

    for i in range(1, cfg.n_contradiction + 1):
        tasks.append(_contradiction_task(rng, i))

    for i in range(1, cfg.n_long + 1):
        tasks.append(_long_chain_task(rng, i))

    # Shuffle to avoid category blocks
    rng.shuffle(tasks)
    return tasks


def parse_args() -> Config:
    ap = argparse.ArgumentParser(description="Generate a temporal reasoning JSONL dataset (150-200 tasks).")
    ap.add_argument("--out", default="data/temporal_reasoning_eval.jsonl", help="Output JSONL path.")
    ap.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    ap.add_argument("--n-linear", type=int, default=40, help="Number of linear chain tasks.")
    ap.add_argument("--n-transitive", type=int, default=40, help="Number of transitive reasoning tasks.")
    ap.add_argument("--n-ambiguous", type=int, default=30, help="Number of ambiguous/underspecified tasks.")
    ap.add_argument("--n-contradiction", type=int, default=20, help="Number of contradiction tasks.")
    ap.add_argument("--n-long", type=int, default=20, help="Number of long chain tasks (5-7 events).")
    args = ap.parse_args()

    return Config(
        seed=args.seed,
        n_linear=args.n_linear,
        n_transitive=args.n_transitive,
        n_ambiguous=args.n_ambiguous,
        n_contradiction=args.n_contradiction,
        n_long=args.n_long,
        out_path=Path(args.out),
    )


def main() -> None:
    cfg = parse_args()
    tasks = generate_dataset(cfg)

    total = len(tasks)
    if total < 150 or total > 200:
        raise ValueError(
            f"Expected total tasks in [150, 200], got {total}. "
            f"Adjust n_* flags to reach target."
        )

    _write_jsonl(cfg.out_path, tasks)

    # Print summary
    counts: Dict[str, int] = {}
    for t in tasks:
        cat = t["category"]
        counts[cat] = counts.get(cat, 0) + 1

    print(f"✅ Wrote {total} tasks to {cfg.out_path}")
    for k in sorted(counts):
        print(f"  - {k}: {counts[k]}")


if __name__ == "__main__":
    main()