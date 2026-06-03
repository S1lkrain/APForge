import pytest

from ap_skill_generator.computation.calculator import assemble_computation_mcq, calculate, list_methods
from ap_skill_generator.computation.error_models import apply_error_model, list_error_models
from ap_skill_generator.computation.formulas import evaluate_method
from ap_skill_generator.computation.schemas import CalculationSpec, DistractorSpec
from ap_skill_generator.computation.verifier import extract_choice_value, verify_answer
from ap_skill_generator.schema import GeneratedItem, Metadata, QuestionType, Subject
from ap_skill_generator.skill_production.evaluators import run_basic_evaluators
from ap_skill_generator.skill_production.registry import get
from ap_skill_generator.skills import QuestionSkill, compose_item
from ap_skill_generator.schema import GenerateRequest


class FakeProvider:
    def __init__(self, payloads):
        self.payloads = payloads
        self.i = 0

    def complete_json(self, *, system_prompt: str, user_prompt: str):
        payload = self.payloads[self.i]
        self.i += 1
        return payload, "fake-model"


@pytest.mark.parametrize(
    ("method", "inputs", "expected"),
    [
        ("compound_interest", {"principal": 1200, "rate": 0.035, "time": 4}, 1377.03),
        ("simple_interest", {"principal": 1200, "rate": 0.035, "time": 4}, 168.0),
        ("percent_change", {"initial": 100, "final": 125}, 25.0),
        ("exponential_growth", {"initial": 500, "base": 1.2, "time": 3}, 864.0),
        ("linear_function", {"slope": 3, "x": 4, "intercept": 1}, 13.0),
        ("slope", {"x1": 1, "y1": 2, "x2": 5, "y2": 10}, 2.0),
        ("mean", {"values": [2, 4, 6, 8]}, 5.0),
        ("standard_deviation", {"values": [2, 4, 4, 4, 5, 5, 7, 9], "sample": True}, pytest.approx(2.138, rel=1e-3)),
        ("z_score", {"value": 85, "mean": 70, "sd": 5}, 3.0),
        ("probability_complement", {"p": 0.35}, 0.65),
        ("molarity", {"moles": 2, "volume_L": 0.5}, 4.0),
        ("dilution", {"C1": 2, "V1": 50, "V2": 100}, 1.0),
        ("stoichiometric_ratio", {"moles_a": 4, "coeff_a": 2, "coeff_b": 3}, 6.0),
        ("function_substitution", {"expression": "x**2 + 2*x", "variable": "x", "value": 3}, 15.0),
        ("derivative_evaluation", {"expression": "x**2", "variable": "x", "at": 3}, 6.0),
    ],
)
def test_formula_registry(method, inputs, expected):
    result = evaluate_method(method, inputs, rounding=2)
    assert result == pytest.approx(expected, rel=1e-3, abs=1e-2)


def test_calculate_unknown_method():
    spec = CalculationSpec(method="unknown_method", inputs={"a": 1})
    result = calculate(spec)
    assert result.success is False
    assert result.verified_answer is None


def test_calculate_compound_interest():
    spec = CalculationSpec(
        method="compound_interest",
        inputs={"principal": 1200, "rate": 0.035, "time": 4},
        rounding=2,
    )
    result = calculate(spec)
    assert result.success is True
    assert result.verified_answer == 1377.03


def test_simple_interest_instead_of_compound_error_model():
    spec = CalculationSpec(
        method="compound_interest",
        inputs={"principal": 1200, "rate": 0.035, "time": 4},
        rounding=2,
    )
    verified = calculate(spec).verified_answer
    wrong = apply_error_model("simple_interest_instead_of_compound", spec, verified)
    assert wrong == 1368.0


def test_assemble_computation_mcq():
    spec = CalculationSpec(
        method="compound_interest",
        inputs={"principal": 1200, "rate": 0.035, "time": 4},
        rounding=2,
    )
    distractor_specs = [
        DistractorSpec(
            error_model="simple_interest_instead_of_compound",
            why_wrong="Uses simple interest instead of compound growth.",
        ),
        DistractorSpec(
            error_model="early_rounding",
            why_wrong="Rounds too early in the calculation.",
        ),
        DistractorSpec(
            error_model="arithmetic_slip",
            why_wrong="Adds a small arithmetic error.",
        ),
    ]
    choices, answer, metadata, calc_result = assemble_computation_mcq(spec, distractor_specs)
    assert calc_result.success is True
    assert len(choices) == 4
    assert answer == "A"
    assert extract_choice_value(choices[0]) == calc_result.verified_answer
    assert len(metadata) == 3
    assert all(entry.error_model for entry in metadata)


def test_verify_answer_passes_for_consistent_item():
    spec = CalculationSpec(
        method="compound_interest",
        inputs={"principal": 1200, "rate": 0.035, "time": 4},
        rounding=2,
    )
    distractor_specs = [
        DistractorSpec(error_model="simple_interest_instead_of_compound", why_wrong="Simple interest mistake."),
        DistractorSpec(error_model="early_rounding", why_wrong="Early rounding mistake."),
        DistractorSpec(error_model="arithmetic_slip", why_wrong="Arithmetic slip."),
    ]
    choices, answer, metadata, calc_result = assemble_computation_mcq(spec, distractor_specs)
    item = GeneratedItem(
        question="An account earns 3.5% interest compounded annually. What is the balance after 4 years on $1200?",
        choices=choices,
        answer=answer,
        explanation="Use compound interest to find the balance after 4 years, so the correct answer is A.",
        metadata=Metadata(
            subject=Subject.AP_PRECALCULUS,
            skill="ap_precalculus.exponential_growth",
            difficulty=3,
            type=QuestionType.MCQ,
        ),
        calculation_required=True,
        calculation_spec=spec,
        verified=True,
        verified_answer=calc_result.verified_answer,
        distractor_metadata=metadata,
    )
    result = verify_answer(item)
    assert result.verified is True
    assert result.failure_tags == []


def test_verify_answer_computation_mismatch():
    spec = CalculationSpec(
        method="compound_interest",
        inputs={"principal": 1200, "rate": 0.035, "time": 4},
        rounding=2,
    )
    item = GeneratedItem(
        question="What is the balance after 4 years on $1200 at 3.5% compounded annually?",
        choices=["A. 1000.00", "B. 1100.00", "C. 1200.00", "D. 1300.00"],
        answer="A",
        explanation="The balance grows with compound interest, so answer A is correct.",
        metadata=Metadata(
            subject=Subject.AP_PRECALCULUS,
            skill="ap_precalculus.exponential_growth",
            difficulty=3,
            type=QuestionType.MCQ,
        ),
        calculation_required=True,
        calculation_spec=spec,
        verified_answer=1377.03,
    )
    result = verify_answer(item)
    assert result.verified is False
    assert "computation_mismatch" in result.failure_tags


def test_verify_answer_unverifiable_without_spec():
    item = GeneratedItem(
        question="What is the balance after 4 years on $1200 at 3.5% compounded annually?",
        choices=["A. 1377.63", "B. 1368.00", "C. 1370.00", "D. 1380.00"],
        answer="A",
        explanation="Compound interest gives answer A.",
        metadata=Metadata(
            subject=Subject.AP_PRECALCULUS,
            skill="ap_precalculus.exponential_growth",
            difficulty=3,
            type=QuestionType.MCQ,
        ),
        calculation_required=True,
    )
    result = verify_answer(item)
    assert result.verified is False
    assert "unverifiable_calculation" in result.failure_tags


def test_evaluator_computation_mismatch():
    spec = get("ap_precalculus.exponential_growth")
    item = GeneratedItem(
        question="What is the balance after 4 years on $1200 at 3.5% compounded annually?",
        choices=["A. 1000.00", "B. 1100.00", "C. 1200.00", "D. 1300.00"],
        answer="A",
        explanation="Compound interest gives answer A.",
        metadata=Metadata(
            subject=Subject.AP_PRECALCULUS,
            skill="ap_precalculus.exponential_growth",
            difficulty=3,
            type=QuestionType.MCQ,
        ),
        calculation_required=True,
        calculation_spec=CalculationSpec(
            method="compound_interest",
            inputs={"principal": 1200, "rate": 0.035, "time": 4},
            rounding=2,
        ),
        verified_answer=1377.03,
    )
    result = run_basic_evaluators(item, spec)
    assert "computation_mismatch" in result.failure_tags


def test_exponential_growth_skill_spec_has_computation_enabled():
    spec = get("ap_precalculus.exponential_growth")
    assert spec is not None
    assert spec.computation is not None
    assert spec.computation.enabled is True
    assert "compound_interest" in spec.computation.allowed_methods


def test_question_skill_parses_computation_draft():
    provider = FakeProvider(
        [
            {
                "question": "A savings account starts with $1200 and earns 3.5% interest compounded annually for 4 years.",
                "calculation_required": True,
                "calculation_spec": {
                    "method": "compound_interest",
                    "inputs": {"principal": 1200, "rate": 0.035, "time": 4},
                    "rounding": 2,
                },
                "distractor_specs": [
                    {
                        "error_model": "simple_interest_instead_of_compound",
                        "why_wrong": "Uses simple interest instead of compound growth.",
                    },
                    {"error_model": "sign_error", "why_wrong": "Uses the wrong sign."},
                    {"error_model": "early_rounding", "why_wrong": "Rounds too early."},
                ],
            }
        ]
    )
    skill = QuestionSkill(provider)
    req = GenerateRequest(
        subject=Subject.AP_PRECALCULUS,
        skill="ap_precalculus.exponential_growth",
        difficulty=3,
        type=QuestionType.MCQ,
    )
    draft, _, repaired, attempts, _ = skill.run(req)
    assert draft["calculation_required"] is True
    assert draft["calculation_spec"].method == "compound_interest"
    assert len(draft["distractor_specs"]) == 3
    assert repaired is False
    assert attempts == 1


def test_compose_item_computation_integration():
    spec = CalculationSpec(
        method="compound_interest",
        inputs={"principal": 1200, "rate": 0.035, "time": 4},
        rounding=2,
    )
    distractor_specs = [
        DistractorSpec(error_model="simple_interest_instead_of_compound", why_wrong="Simple interest mistake."),
        DistractorSpec(error_model="early_rounding", why_wrong="Early rounding mistake."),
        DistractorSpec(error_model="arithmetic_slip", why_wrong="Arithmetic slip."),
    ]
    choices, answer, metadata, calc_result = assemble_computation_mcq(spec, distractor_specs)
    req = GenerateRequest(
        subject=Subject.AP_PRECALCULUS,
        skill="ap_precalculus.exponential_growth",
        difficulty=3,
        type=QuestionType.MCQ,
    )
    item = compose_item(
        req=req,
        question="What is the balance after 4 years on $1200 at 3.5% compounded annually?",
        choices=choices,
        answer=answer,
        explanation="Compound interest gives the balance shown in choice A.",
        model_id="fake-model",
        calculation_required=True,
        calculation_spec=spec,
        verified=True,
        verification_notes="computation verified",
        distractor_metadata=metadata,
        verified_answer=calc_result.verified_answer,
    )
    assert item.verified_answer == 1377.03
    assert verify_answer(item).verified is True


def test_list_methods_and_error_models():
    assert "compound_interest" in list_methods()
    assert "simple_interest_instead_of_compound" in list_error_models()


def _build_verified_compound_interest_item() -> GeneratedItem:
    spec = CalculationSpec(
        method="compound_interest",
        inputs={"principal": 1200, "rate": 0.035, "time": 4},
        rounding=2,
    )
    distractor_specs = [
        DistractorSpec(error_model="simple_interest_instead_of_compound", why_wrong="Simple interest mistake."),
        DistractorSpec(error_model="early_rounding", why_wrong="Early rounding mistake."),
        DistractorSpec(error_model="arithmetic_slip", why_wrong="Arithmetic slip."),
    ]
    choices, answer, metadata, calc_result = assemble_computation_mcq(spec, distractor_specs)
    return GeneratedItem(
        question="An account earns 3.5% interest compounded annually. What is the balance after 4 years on $1200?",
        choices=choices,
        answer=answer,
        explanation="Use compound interest to find the balance after 4 years, so the correct answer is A.",
        metadata=Metadata(
            subject=Subject.AP_PRECALCULUS,
            skill="ap_precalculus.exponential_growth",
            difficulty=3,
            type=QuestionType.MCQ,
        ),
        calculation_required=True,
        calculation_spec=spec,
        verified=True,
        verified_answer=calc_result.verified_answer,
        distractor_metadata=metadata,
    )


def test_computation_item_passes_basic_evaluators():
    item = _build_verified_compound_interest_item()
    spec = get("ap_precalculus.exponential_growth")
    result = run_basic_evaluators(item, spec)
    assert result.passed is True
    assert result.failure_tags == []


def test_verify_answer_unrealistic_distractor_duplicate_choices():
    spec = CalculationSpec(
        method="compound_interest",
        inputs={"principal": 1200, "rate": 0.035, "time": 4},
        rounding=2,
    )
    item = GeneratedItem(
        question="What is the balance after 4 years on $1200 at 3.5% compounded annually?",
        choices=["A. 1377.03", "B. 1368.00", "C. 1377.03", "D. 1380.00"],
        answer="A",
        explanation="Compound interest gives answer A.",
        metadata=Metadata(
            subject=Subject.AP_PRECALCULUS,
            skill="ap_precalculus.exponential_growth",
            difficulty=3,
            type=QuestionType.MCQ,
        ),
        calculation_required=True,
        calculation_spec=spec,
        verified_answer=1377.03,
    )
    result = verify_answer(item)
    assert result.verified is False
    assert "unrealistic_distractor" in result.failure_tags


def test_question_skill_rejects_unknown_error_model():
    provider = FakeProvider(
        [
            {
                "question": "A savings account starts with $1200 and earns 3.5% interest compounded annually for 4 years.",
                "calculation_required": True,
                "calculation_spec": {
                    "method": "compound_interest",
                    "inputs": {"principal": 1200, "rate": 0.035, "time": 4},
                    "rounding": 2,
                },
                "distractor_specs": [
                    {"error_model": "not_a_real_model", "why_wrong": "Bad model."},
                    {"error_model": "sign_error", "why_wrong": "Wrong sign."},
                    {"error_model": "early_rounding", "why_wrong": "Early rounding."},
                ],
            }
        ]
    )
    skill = QuestionSkill(provider)
    req = GenerateRequest(
        subject=Subject.AP_PRECALCULUS,
        skill="ap_precalculus.exponential_growth",
        difficulty=3,
        type=QuestionType.MCQ,
    )
    with pytest.raises(Exception, match="Unknown error_model"):
        skill.run(req, max_repair_attempts=0)


def test_question_skill_rejects_missing_required_error_models():
    provider = FakeProvider(
        [
            {
                "question": "A savings account starts with $1200 and earns 3.5% interest compounded annually for 4 years.",
                "calculation_required": True,
                "calculation_spec": {
                    "method": "compound_interest",
                    "inputs": {"principal": 1200, "rate": 0.035, "time": 4},
                    "rounding": 2,
                },
                "distractor_specs": [
                    {
                        "error_model": "simple_interest_instead_of_compound",
                        "why_wrong": "Simple interest mistake.",
                    },
                    {"error_model": "early_rounding", "why_wrong": "Early rounding mistake."},
                    {"error_model": "arithmetic_slip", "why_wrong": "Arithmetic slip."},
                ],
            }
        ]
    )
    skill = QuestionSkill(provider)
    req = GenerateRequest(
        subject=Subject.AP_PRECALCULUS,
        skill="ap_precalculus.exponential_growth",
        difficulty=3,
        type=QuestionType.MCQ,
    )
    with pytest.raises(Exception, match="required error models"):
        skill.run(req, max_repair_attempts=0)
