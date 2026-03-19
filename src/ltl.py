from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Tuple

from src.trace import TemporalTrace


class Formula:
    pass


@dataclass(frozen=True)
class Atom(Formula):
    predicate: str
    args: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Not(Formula):
    operand: Formula


@dataclass(frozen=True)
class And(Formula):
    left: Formula
    right: Formula


@dataclass(frozen=True)
class Or(Formula):
    left: Formula
    right: Formula


@dataclass(frozen=True)
class Next(Formula):
    operand: Formula


@dataclass(frozen=True)
class Eventually(Formula):
    operand: Formula


@dataclass(frozen=True)
class Globally(Formula):
    operand: Formula


@dataclass(frozen=True)
class Until(Formula):
    left: Formula
    right: Formula


@dataclass(frozen=True)
class FormulaFailure:
    failing_formula: Formula
    first_failure_step: int


@dataclass(frozen=True)
class FormulaEvaluation:
    satisfied: bool
    failure: FormulaFailure | None = None


def formula_to_dict(formula: Formula) -> Dict[str, object]:
    if isinstance(formula, Atom):
        return {"op": "atom", "predicate": formula.predicate, "args": list(formula.args)}
    if isinstance(formula, Not):
        return {"op": "not", "arg": formula_to_dict(formula.operand)}
    if isinstance(formula, And):
        return {"op": "and", "left": formula_to_dict(formula.left), "right": formula_to_dict(formula.right)}
    if isinstance(formula, Or):
        return {"op": "or", "left": formula_to_dict(formula.left), "right": formula_to_dict(formula.right)}
    if isinstance(formula, Next):
        return {"op": "x", "arg": formula_to_dict(formula.operand)}
    if isinstance(formula, Eventually):
        return {"op": "f", "arg": formula_to_dict(formula.operand)}
    if isinstance(formula, Globally):
        return {"op": "g", "arg": formula_to_dict(formula.operand)}
    if isinstance(formula, Until):
        return {"op": "u", "left": formula_to_dict(formula.left), "right": formula_to_dict(formula.right)}
    raise TypeError(f"Unsupported formula type: {type(formula).__name__}")


def formula_to_string(formula: Formula) -> str:
    if isinstance(formula, Atom):
        if not formula.args:
            return formula.predicate
        return f"{formula.predicate}({', '.join(formula.args)})"
    if isinstance(formula, Not):
        return f"!({formula_to_string(formula.operand)})"
    if isinstance(formula, And):
        return f"({formula_to_string(formula.left)} & {formula_to_string(formula.right)})"
    if isinstance(formula, Or):
        return f"({formula_to_string(formula.left)} | {formula_to_string(formula.right)})"
    if isinstance(formula, Next):
        return f"X({formula_to_string(formula.operand)})"
    if isinstance(formula, Eventually):
        return f"F({formula_to_string(formula.operand)})"
    if isinstance(formula, Globally):
        return f"G({formula_to_string(formula.operand)})"
    if isinstance(formula, Until):
        return f"({formula_to_string(formula.left)} U {formula_to_string(formula.right)})"
    raise TypeError(f"Unsupported formula type: {type(formula).__name__}")


class LTLEvaluator:
    def __init__(self, trace: TemporalTrace) -> None:
        self.trace = trace

    def evaluate(self, formula: Formula, *, start_index: int = 0) -> FormulaEvaluation:
        @lru_cache(maxsize=None)
        def holds(node: Formula, index: int) -> bool:
            if index >= len(self.trace):
                return False
            if isinstance(node, Atom):
                return self.trace.predicate_holds(index, node.predicate, node.args)
            if isinstance(node, Not):
                return not holds(node.operand, index)
            if isinstance(node, And):
                return holds(node.left, index) and holds(node.right, index)
            if isinstance(node, Or):
                return holds(node.left, index) or holds(node.right, index)
            if isinstance(node, Next):
                return index + 1 < len(self.trace) and holds(node.operand, index + 1)
            if isinstance(node, Eventually):
                return any(holds(node.operand, later) for later in range(index, len(self.trace)))
            if isinstance(node, Globally):
                return all(holds(node.operand, later) for later in range(index, len(self.trace)))
            if isinstance(node, Until):
                for later in range(index, len(self.trace)):
                    if holds(node.right, later):
                        if all(holds(node.left, middle) for middle in range(index, later)):
                            return True
                return False
            raise TypeError(f"Unsupported formula type: {type(node).__name__}")

        def explain(node: Formula, index: int) -> FormulaFailure | None:
            if holds(node, index):
                return None

            if isinstance(node, Atom):
                return FormulaFailure(failing_formula=node, first_failure_step=index)

            if isinstance(node, Not):
                return FormulaFailure(failing_formula=node.operand, first_failure_step=index)

            if isinstance(node, And):
                failures = [
                    failure
                    for failure in (explain(node.left, index), explain(node.right, index))
                    if failure is not None
                ]
                return min(failures, key=lambda failure: failure.first_failure_step)

            if isinstance(node, Or):
                failures = [
                    failure
                    for failure in (explain(node.left, index), explain(node.right, index))
                    if failure is not None
                ]
                return min(failures, key=lambda failure: failure.first_failure_step)

            if isinstance(node, Next):
                if index + 1 >= len(self.trace):
                    return FormulaFailure(failing_formula=node, first_failure_step=index)
                return explain(node.operand, index + 1)

            if isinstance(node, Eventually):
                last_index = max(0, len(self.trace) - 1)
                return explain(node.operand, last_index) or FormulaFailure(
                    failing_formula=node,
                    first_failure_step=last_index,
                )

            if isinstance(node, Globally):
                for later in range(index, len(self.trace)):
                    failure = explain(node.operand, later)
                    if failure is not None:
                        return failure
                return FormulaFailure(failing_formula=node, first_failure_step=index)

            if isinstance(node, Until):
                for later in range(index, len(self.trace)):
                    if holds(node.right, later):
                        if all(holds(node.left, middle) for middle in range(index, later)):
                            return None
                    if later < len(self.trace) and not holds(node.left, later):
                        return explain(node.left, later)
                last_index = max(0, len(self.trace) - 1)
                return explain(node.right, last_index) or FormulaFailure(
                    failing_formula=node.right,
                    first_failure_step=last_index,
                )

            raise TypeError(f"Unsupported formula type: {type(node).__name__}")

        satisfied = holds(formula, start_index)
        if satisfied:
            return FormulaEvaluation(satisfied=True, failure=None)
        return FormulaEvaluation(satisfied=False, failure=explain(formula, start_index))
