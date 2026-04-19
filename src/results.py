from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.schemas import Edge


@dataclass(frozen=True)
class Counterexample:
    relation_edges: List[Edge] = field(default_factory=list)
    step_ids: List[int] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class Violation:
    type: str
    message: str
    layer: str
    constraint: str
    spec_source: str = "invariant"
    details: Dict[str, Any] = field(default_factory=dict)
    counterexample: Optional[Counterexample] = None


@dataclass(frozen=True)
class VerificationResult:
    is_valid: bool
    graph_valid: bool
    trace_grounded: bool
    violations: List[Violation]
    formula_violations: List[Violation]
    violation_counts: Dict[str, int]
    layer_counts: Dict[str, int]
    formula_violation_counts: Dict[str, int]
    first_violation_step: Optional[int]
    spec_sources: Dict[str, int]


@dataclass(frozen=True)
class PRFResult:
    precision: float
    recall: float
    f1: float
    correct: int
    pred_total: int
    gold_total: int


@dataclass(frozen=True)
class TaskScore:
    direct: PRFResult
    closure: PRFResult
    missing_direct_edges: List[Edge]
    spurious_direct_edges: List[Edge]
    missing_closure_pairs: List[List[str]]
    spurious_closure_pairs: List[List[str]]
    preserves_ordering_closure: bool
    has_overcommitment: bool
    abstained: bool


@dataclass(frozen=True)
class DatasetMetadata:
    path: str
    dataset_version: str
    num_tasks: int
    expected_valid_tasks: int
    expected_invalid_tasks: int


@dataclass(frozen=True)
class RunReport:
    run_id: str
    predictions_file: str
    pred_source: str
    dataset: DatasetMetadata
    code_version: str
    model_metadata: Dict[str, Any]
    run_config: Dict[str, Any]
    num_tasks: int
    num_failures: int
    failures: List[Dict[str, Any]]
    repair_hit_count: int
    repair_hit_rate: float
    parse_success_rate: float
    conditional_validity_rate: Optional[float]
    conditional_trace_grounding_rate: Optional[float]
    transport_failure_counts: Dict[str, int]
    parse_failure_counts: Dict[str, int]
    valid_count: int
    invalid_count: int
    trace_grounded_count: int
    trace_ungrounded_count: int
    validity_rate: float
    violation_counts: Dict[str, int]
    formula_violation_counts: Dict[str, int]
    first_violation_step_histogram: Dict[str, int]
    taxonomy_counts: Dict[str, int]
    overcommitment: Dict[str, Any]
    metrics_expected_valid_only: Dict[str, Any]
    report_path: Optional[str] = None


@dataclass(frozen=True)
class RunArtifacts:
    run_id: str
    run_dir: Path
    predictions_path: Path
    report_path: Path
    report: RunReport
