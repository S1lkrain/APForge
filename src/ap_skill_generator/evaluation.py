from __future__ import annotations

from pydantic import BaseModel, Field, ValidationError

from .schema import GeneratedItem, QuestionType


class JudgeResult(BaseModel):
    schema_score: int = Field(ge=0, le=100)
    consistency_score: int = Field(ge=0, le=100)
    pedagogy_score: int = Field(ge=0, le=100)
    compliance_score: int = Field(ge=0, le=100)
    overall_decision: str
    rationale: str


def item_passes_schema(item: GeneratedItem) -> bool:
    try:
        GeneratedItem.model_validate(item.model_dump())
        return True
    except ValidationError:
        return False


def judge_item(item: GeneratedItem) -> JudgeResult:
    schema_score = 100 if item_passes_schema(item) else 0
    consistency_score = 100
    if item.metadata.type == QuestionType.MCQ and item.answer.strip().upper() not in {"A", "B", "C", "D"}:
        consistency_score = 40

    explanation_word_count = len(item.explanation.split())
    pedagogy_score = min(100, max(40, explanation_word_count * 4))
    compliance_score = 100
    if "college board" in item.question.lower():
        compliance_score = 40

    decision = "pass"
    if schema_score < 100 or compliance_score < 98 or consistency_score < 95:
        decision = "fail"
    rationale = (
        f"schema={schema_score}, consistency={consistency_score}, "
        f"pedagogy={pedagogy_score}, compliance={compliance_score}"
    )
    return JudgeResult(
        schema_score=schema_score,
        consistency_score=consistency_score,
        pedagogy_score=pedagogy_score,
        compliance_score=compliance_score,
        overall_decision=decision,
        rationale=rationale,
    )


def evaluate_item(item: GeneratedItem, judge_result: JudgeResult | None = None) -> dict:
    judge = judge_result or judge_item(item)
    schema_valid = judge.schema_score >= 100
    answer_consistent = judge.consistency_score >= 95
    explanation_score = min(5, max(1, len(item.explanation.split()) // 12 or 1))
    difficulty_score = min(5, max(1, item.metadata.difficulty))
    return {
        "schema_valid": schema_valid,
        "answer_consistent": answer_consistent,
        "explanation_score": explanation_score,
        "difficulty_score": difficulty_score,
        "notes": judge.rationale,
        "judge_scores": judge.model_dump(),
    }


def aggregate_metrics(evals: list[dict]) -> dict:
    if not evals:
        return {
            "schema_valid_rate": 0.0,
            "answer_consistency_rate": 0.0,
            "avg_explanation_score": 0.0,
        }
    total = len(evals)
    schema_valid_count = sum(1 for e in evals if e["schema_valid"])
    answer_consistent_count = sum(1 for e in evals if e["answer_consistent"])
    return {
        "schema_valid_rate": schema_valid_count / total,
        "answer_consistency_rate": answer_consistent_count / total,
        "avg_explanation_score": sum(e["explanation_score"] for e in evals) / total,
    }
