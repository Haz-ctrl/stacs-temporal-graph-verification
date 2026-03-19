from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Protocol, Sequence, Set, Tuple

from src.ltl import Atom, FormulaEvaluation, Globally, LTLEvaluator, Not, formula_to_dict, formula_to_string
from src.results import Counterexample, VerificationResult, Violation
from src.specs import BaseInvariant, FormulaSpec, InvariantSpec, SpecContext, TemporalSpecification
from src.temporal_graph import EdgeLike, TemporalGraph, _to_edge
from src.trace import TemporalTrace, build_temporal_trace

Edge3 = Tuple[str, str, str]


class Constraint(Protocol):
    name: str
    layer: str
    description: str

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> List[Violation]:
        ...


def _build_context(
    graph: TemporalGraph,
    *,
    allowed_events: Optional[Sequence[str]] = None,
    pred_edges: Optional[Iterable[EdgeLike]] = None,
    reasoning_steps: Optional[Sequence[Any]] = None,
    trace: Optional[TemporalTrace] = None,
) -> SpecContext:
    return SpecContext(
        graph=graph,
        allowed_events=allowed_events,
        pred_edges=tuple(_to_edge(edge) for edge in (pred_edges or [])),
        reasoning_steps=tuple(reasoning_steps or ()),
        trace=trace,
    )


@dataclass(frozen=True)
class AcyclicityConstraint(BaseInvariant):
    spec: InvariantSpec = InvariantSpec(
        name="acyclicity",
        layer="intrinsic_temporal",
        description="Ordering edges must not induce a directed cycle.",
    )

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def layer(self) -> str:
        return self.spec.layer

    @property
    def description(self) -> str:
        return self.spec.description

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> List[Violation]:
        return self.evaluate(
            SpecContext(
                graph=graph,
                allowed_events=allowed_events,
                pred_edges=tuple(_to_edge(edge) for edge in (pred_edges or [])),
                reasoning_steps=tuple(reasoning_steps or ()),
            )
        )

    def evaluate(self, context: SpecContext) -> List[Violation]:
        if context.graph.is_acyclic():
            return []
        cycles = context.graph.find_cycles()
        return [
            self.violation(
                type="cycle",
                message="Temporal graph contains at least one directed cycle.",
                details={"cycles": cycles},
                notes=["Detected cycle in normalised ordering graph."],
            )
        ]


@dataclass(frozen=True)
class NoDirectContradictionsConstraint(BaseInvariant):
    spec: InvariantSpec = InvariantSpec(
        name="antisymmetry",
        layer="intrinsic_temporal",
        description="No event pair may be asserted in both temporal directions.",
    )

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def layer(self) -> str:
        return self.spec.layer

    @property
    def description(self) -> str:
        return self.spec.description

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> List[Violation]:
        return self.evaluate(
            SpecContext(
                graph=graph,
                allowed_events=allowed_events,
                pred_edges=tuple(_to_edge(edge) for edge in (pred_edges or [])),
                reasoning_steps=tuple(reasoning_steps or ()),
            )
        )

    def evaluate(self, context: SpecContext) -> List[Violation]:
        contradictions = context.graph.direct_contradictions("BEFORE")
        if not contradictions:
            return []
        return [
            self.violation(
                type="contradiction",
                message="Temporal graph contains directly contradictory ordering relations.",
                details={"pairs": contradictions},
                notes=["Contradictory direct order pair detected after AFTER normalisation."],
            )
        ]


@dataclass(frozen=True)
class SimultaneityConsistencyConstraint(BaseInvariant):
    spec: InvariantSpec = InvariantSpec(
        name="simultaneity_consistency",
        layer="intrinsic_temporal",
        description="SIMULTANEOUS groups must not also contain ordering edges.",
    )

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def layer(self) -> str:
        return self.spec.layer

    @property
    def description(self) -> str:
        return self.spec.description

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> List[Violation]:
        return self.evaluate(
            SpecContext(
                graph=graph,
                allowed_events=allowed_events,
                pred_edges=tuple(_to_edge(edge) for edge in (pred_edges or [])),
                reasoning_steps=tuple(reasoning_steps or ()),
            )
        )

    def evaluate(self, context: SpecContext) -> List[Violation]:
        conflicts = context.graph.simultaneous_order_conflicts()
        if not conflicts:
            return []
        return [
            self.violation(
                type="simultaneous_order_conflict",
                message="A SIMULTANEOUS group also contains an ordering relation.",
                details={"pairs": conflicts},
                notes=["Ordering inside a simultaneous equivalence class is inconsistent."],
            )
        ]


@dataclass(frozen=True)
class TemporalConsistencyConstraint(BaseInvariant):
    spec: InvariantSpec = InvariantSpec(
        name="temporal_consistency",
        layer="intrinsic_temporal",
        description="Ordering closure must remain globally consistent.",
    )

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def layer(self) -> str:
        return self.spec.layer

    @property
    def description(self) -> str:
        return self.spec.description

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> List[Violation]:
        return self.evaluate(
            SpecContext(
                graph=graph,
                allowed_events=allowed_events,
                pred_edges=tuple(_to_edge(edge) for edge in (pred_edges or [])),
                reasoning_steps=tuple(reasoning_steps or ()),
            )
        )

    def evaluate(self, context: SpecContext) -> List[Violation]:
        inconsistencies = context.graph.temporal_inconsistencies("BEFORE")
        if not inconsistencies:
            return []
        return [
            self.violation(
                type="temporal_inconsistency",
                message="Temporal graph contains globally inconsistent ordering constraints.",
                details={"pairs": inconsistencies},
                notes=["Bidirectional reachability detected in the ordering closure."],
            )
        ]


@dataclass(frozen=True)
class NoHallucinatedNodesConstraint(BaseInvariant):
    spec: InvariantSpec = InvariantSpec(
        name="no_hallucinated_nodes",
        layer="grounding",
        description="Predicted events must be drawn from the task event inventory.",
    )

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def layer(self) -> str:
        return self.spec.layer

    @property
    def description(self) -> str:
        return self.spec.description

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> List[Violation]:
        return self.evaluate(
            SpecContext(
                graph=graph,
                allowed_events=allowed_events,
                pred_edges=tuple(_to_edge(edge) for edge in (pred_edges or [])),
                reasoning_steps=tuple(reasoning_steps or ()),
            )
        )

    def evaluate(self, context: SpecContext) -> List[Violation]:
        if context.allowed_events is None:
            raise ValueError("NoHallucinatedNodesConstraint requires allowed_events to be provided.")
        unknown = context.graph.unknown_nodes(context.allowed_events)
        if not unknown:
            return []
        return [
            self.violation(
                type="hallucinated_node",
                message="Graph contains node(s) not present in the allowed event list.",
                details={"unknown_nodes": unknown},
                notes=["Prediction introduced unsupported event nodes."],
            )
        ]


@dataclass(frozen=True)
class DuplicateEdgeConstraint(BaseInvariant):
    spec: InvariantSpec = InvariantSpec(
        name="duplicate_edge",
        layer="format",
        description="Predicted edge triples should not repeat.",
    )

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def layer(self) -> str:
        return self.spec.layer

    @property
    def description(self) -> str:
        return self.spec.description

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> List[Violation]:
        return self.evaluate(
            SpecContext(
                graph=graph,
                allowed_events=allowed_events,
                pred_edges=tuple(_to_edge(edge) for edge in (pred_edges or [])),
                reasoning_steps=tuple(reasoning_steps or ()),
            )
        )

    def evaluate(self, context: SpecContext) -> List[Violation]:
        pred_list = list(context.pred_edges)
        unique = set(pred_list)
        if len(pred_list) == len(unique):
            return []
        return [
            self.violation(
                type="duplicate_edge",
                message="Predicted output contains duplicate relation triples.",
                details={"num_edges": len(pred_list), "num_unique_edges": len(unique)},
                relation_edges=pred_list,
            )
        ]


@dataclass(frozen=True)
class ReasoningSupportConstraint(BaseInvariant):
    spec: InvariantSpec = InvariantSpec(
        name="reasoning_support",
        layer="trace",
        description="Reasoning supports should be grounded in final predicted relations.",
    )

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def layer(self) -> str:
        return self.spec.layer

    @property
    def description(self) -> str:
        return self.spec.description

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> List[Violation]:
        return self.evaluate(
            SpecContext(
                graph=graph,
                allowed_events=allowed_events,
                pred_edges=tuple(_to_edge(edge) for edge in (pred_edges or [])),
                reasoning_steps=tuple(reasoning_steps or ()),
            )
        )

    def evaluate(self, context: SpecContext) -> List[Violation]:
        if not context.reasoning_steps:
            return []

        pred_set = set(context.pred_edges)
        unsupported: List[dict[str, Any]] = []
        step_ids: Set[int] = set()

        for step in context.reasoning_steps:
            step_id = getattr(step, "step_id", None)
            supports = getattr(step, "supports", [])
            for edge in supports:
                canonical_edge = _to_edge(edge)
                if canonical_edge not in pred_set:
                    unsupported.append({"step_id": step_id, "edge": canonical_edge})
                    if isinstance(step_id, int):
                        step_ids.add(step_id)

        if not unsupported:
            return []

        return [
            self.violation(
                type="unsupported_reasoning_step",
                message="One or more reasoning steps cite relations not present in final predicted relations.",
                details={"unsupported_supports": unsupported},
                relation_edges=(item["edge"] for item in unsupported),
                step_ids=step_ids,
            )
        ]


@dataclass(frozen=True)
class ReasoningGroundingConstraint(BaseInvariant):
    spec: InvariantSpec = InvariantSpec(
        name="reasoning_grounding",
        layer="grounding",
        description="Reasoning supports should only reference allowed events.",
    )

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def layer(self) -> str:
        return self.spec.layer

    @property
    def description(self) -> str:
        return self.spec.description

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> List[Violation]:
        return self.evaluate(
            SpecContext(
                graph=graph,
                allowed_events=allowed_events,
                pred_edges=tuple(_to_edge(edge) for edge in (pred_edges or [])),
                reasoning_steps=tuple(reasoning_steps or ()),
            )
        )

    def evaluate(self, context: SpecContext) -> List[Violation]:
        if context.allowed_events is None or not context.reasoning_steps:
            return []

        allowed_set = set(context.allowed_events)
        unsupported_refs: List[dict[str, Any]] = []
        step_ids: Set[int] = set()

        for step in context.reasoning_steps:
            step_id = getattr(step, "step_id", None)
            supports = getattr(step, "supports", [])
            for edge in supports:
                source, target, relation = _to_edge(edge)
                if source not in allowed_set or target not in allowed_set:
                    unsupported_refs.append(
                        {"step_id": step_id, "edge": (source, target, relation)}
                    )
                    if isinstance(step_id, int):
                        step_ids.add(step_id)

        if not unsupported_refs:
            return []

        return [
            self.violation(
                type="unsupported_reasoning_reference",
                message="A reasoning step references event names outside the task event set.",
                details={"unsupported_references": unsupported_refs},
                relation_edges=(item["edge"] for item in unsupported_refs),
                step_ids=step_ids,
            )
        ]


@dataclass
class Verifier:
    constraints: List[Constraint]
    specification: TemporalSpecification

    def _state_graph(self, *, allowed_events: Optional[Sequence[str]], edges: Sequence[Edge3]) -> TemporalGraph:
        graph = TemporalGraph()
        if allowed_events is not None:
            graph.add_events(allowed_events)
        graph.add_edges(edges)
        return graph

    def _state_violation_types(
        self,
        trace: TemporalTrace,
        *,
        allowed_events: Optional[Sequence[str]],
        pred_edges: Tuple[Edge3, ...],
        reasoning_steps: Tuple[Any, ...],
    ) -> List[Set[str]]:
        violation_types_by_state: List[Set[str]] = []
        for state in trace.states:
            if state.is_final_state:
                graph = self._state_graph(allowed_events=allowed_events, edges=pred_edges)
                state_reasoning_steps = reasoning_steps
            else:
                graph = self._state_graph(allowed_events=allowed_events, edges=state.active_edges)
                state_reasoning_steps = tuple(
                    step for step in reasoning_steps if getattr(step, "step_id", None) is not None and getattr(step, "step_id") <= (state.step_id or -1)
                )

            violations: Set[str] = set()
            for constraint in self.constraints:
                result = constraint.evaluate(
                    _build_context(
                        graph,
                        allowed_events=allowed_events,
                        pred_edges=pred_edges,
                        reasoning_steps=state_reasoning_steps,
                    )
                )
                violations.update(violation.type for violation in result)
            violation_types_by_state.append(violations)
        return violation_types_by_state

    def _formula_violations(
        self,
        *,
        context: SpecContext,
    ) -> Tuple[List[Violation], Optional[int]]:
        if context.trace is None or not self.specification.formulas:
            return [], None

        evaluator = LTLEvaluator(context.trace)
        formula_violations: List[Violation] = []
        first_violation_step: Optional[int] = None

        for formula_spec in self.specification.formulas:
            evaluation: FormulaEvaluation = evaluator.evaluate(formula_spec.formula)
            if evaluation.satisfied:
                continue

            failure_step = (
                evaluation.failure.first_failure_step
                if evaluation.failure is not None
                else 0
            )
            first_violation_step = (
                failure_step
                if first_violation_step is None
                else min(first_violation_step, failure_step)
            )

            notes = [f"Formula failed: {formula_to_string(formula_spec.formula)}"]
            if evaluation.failure is not None:
                notes.append(
                    f"Failing subformula: {formula_to_string(evaluation.failure.failing_formula)}"
                )

            formula_violations.append(
                Violation(
                    type=formula_spec.violation_type,
                    message=formula_spec.message,
                    layer="ltl",
                    constraint=formula_spec.name,
                    spec_source="ltl",
                    details={
                        "formula": formula_to_dict(formula_spec.formula),
                        "formula_text": formula_to_string(formula_spec.formula),
                        "first_failure_step": failure_step,
                        "failing_subformula": (
                            formula_to_string(evaluation.failure.failing_formula)
                            if evaluation.failure is not None
                            else formula_to_string(formula_spec.formula)
                        ),
                    },
                    counterexample=None if context.trace is None else Counterexample(
                        step_ids=[failure_step],
                        notes=notes,
                    ),
                )
            )

        return formula_violations, first_violation_step

    def verify(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> VerificationResult:
        pred_edges_tuple = tuple(_to_edge(edge) for edge in (pred_edges or []))
        reasoning_steps_tuple = tuple(reasoning_steps or ())
        invariant_context = _build_context(
            graph,
            allowed_events=allowed_events,
            pred_edges=pred_edges_tuple,
            reasoning_steps=reasoning_steps_tuple,
        )
        violations: List[Violation] = []
        for constraint in self.constraints:
            violations.extend(constraint.evaluate(invariant_context))

        trace = build_temporal_trace(
            allowed_events=tuple(allowed_events or ()),
            pred_edges=pred_edges_tuple,
            reasoning_steps=reasoning_steps_tuple,
        )
        trace = trace.with_violations(
            self._state_violation_types(
                trace,
                allowed_events=allowed_events,
                pred_edges=pred_edges_tuple,
                reasoning_steps=reasoning_steps_tuple,
            )
        )
        formula_context = _build_context(
            graph,
            allowed_events=allowed_events,
            pred_edges=pred_edges_tuple,
            reasoning_steps=reasoning_steps_tuple,
            trace=trace,
        )
        formula_violations, first_formula_violation_step = self._formula_violations(
            context=formula_context
        )

        all_violations = violations + formula_violations
        violation_counts = dict(Counter(violation.type for violation in violations))
        layer_counts = dict(Counter(violation.layer for violation in all_violations))
        formula_violation_counts = dict(Counter(violation.type for violation in formula_violations))
        first_invariant_step = min(
            (
                violation.counterexample.step_ids[0]
                for violation in violations
                if violation.counterexample is not None and violation.counterexample.step_ids
            ),
            default=None,
        )
        first_violation_step = min(
            (
                step
                for step in (first_invariant_step, first_formula_violation_step)
                if step is not None
            ),
            default=None,
        )
        spec_sources = dict(Counter(violation.spec_source for violation in all_violations))
        return VerificationResult(
            is_valid=len(all_violations) == 0,
            violations=violations,
            formula_violations=formula_violations,
            violation_counts=violation_counts,
            layer_counts=layer_counts,
            formula_violation_counts=formula_violation_counts,
            first_violation_step=first_violation_step,
            spec_sources=spec_sources,
        )


def default_temporal_specification() -> TemporalSpecification:
    invariants = (
        DuplicateEdgeConstraint(),
        NoHallucinatedNodesConstraint(),
        ReasoningGroundingConstraint(),
        NoDirectContradictionsConstraint(),
        SimultaneityConsistencyConstraint(),
        AcyclicityConstraint(),
        TemporalConsistencyConstraint(),
        ReasoningSupportConstraint(),
    )
    formulas = (
        FormulaSpec(
            name="ltl_no_contradiction",
            description="Contradictions should never appear in the trace.",
            formula=Globally(Not(Atom("has_violation", ("contradiction",)))),
            violation_type="ltl_contradiction",
            message="LTL spec violated: contradiction becomes true at some trace state.",
        ),
        FormulaSpec(
            name="ltl_no_temporal_inconsistency",
            description="Temporal inconsistency should never appear in the trace.",
            formula=Globally(Not(Atom("has_violation", ("temporal_inconsistency",)))),
            violation_type="ltl_temporal_inconsistency",
            message="LTL spec violated: temporal inconsistency becomes true at some trace state.",
        ),
        FormulaSpec(
            name="ltl_no_hallucinated_nodes",
            description="Hallucinated nodes should never appear in the trace.",
            formula=Globally(Not(Atom("has_violation", ("hallucinated_node",)))),
            violation_type="ltl_hallucinated_node",
            message="LTL spec violated: hallucinated node appears at some trace state.",
        ),
    )
    return TemporalSpecification(
        name="default_temporal_spec",
        invariants=invariants,
        formulas=formulas,
    )


def default_verifier() -> Verifier:
    specification = default_temporal_specification()
    return Verifier(constraints=list(specification.invariants), specification=specification)
