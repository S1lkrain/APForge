from __future__ import annotations

from .schema import GenerateRequest, QuestionType

PROMPT_VERSION = "v1"


def system_prompt() -> str:
    return (
        "You are an AP-style educational content generator. "
        "Output only valid JSON. Do not use copyrighted or real AP exam items. "
        "Generate original content. Keep language concise and pedagogically clear."
    )


def question_skill_prompt(req: GenerateRequest) -> str:
    if req.type == QuestionType.MCQ:
        type_block = (
            "Create one MCQ with exactly 4 choices. "
            "Set answer to one of A/B/C/D, and choices in that order."
        )
    else:
        type_block = (
            "Create one FRQ item with no choices (empty list). "
            "Provide a concise expected answer."
        )
    return (
        f"Subject: {req.subject.value}\n"
        f"Skill: {req.skill}\n"
        f"Difficulty (1-5): {req.difficulty}\n"
        f"Type: {req.type.value}\n"
        f"Locale: {req.locale}\n"
        f"{type_block}\n"
        "Return this JSON object only:\n"
        "{"
        '"question": "...",'
        '"choices": ["A. ...","B. ...","C. ...","D. ..."] or []'
        "}"
    )


def answer_skill_prompt(req: GenerateRequest, question: str, choices: list[str]) -> str:
    return (
        f"Subject: {req.subject.value}\n"
        f"Skill: {req.skill}\n"
        f"Difficulty: {req.difficulty}\n"
        f"Type: {req.type.value}\n"
        f"Question: {question}\n"
        f"Choices: {choices}\n"
        "Return JSON only: {\"answer\": \"...\"}. "
        "For MCQ answer must be one of A/B/C/D."
    )


def explanation_skill_prompt(req: GenerateRequest, question: str, answer: str) -> str:
    return (
        f"Subject: {req.subject.value}\n"
        f"Skill: {req.skill}\n"
        f"Difficulty: {req.difficulty}\n"
        f"Type: {req.type.value}\n"
        f"Question: {question}\n"
        f"Expected answer: {answer}\n"
        "Return JSON only: {\"explanation\": \"...\"}. "
        "Keep explanation concise and educational."
    )


def repair_prompt(bad_payload: dict, error_message: str) -> str:
    return (
        "Repair this invalid JSON payload so it strictly follows the required shape.\n"
        f"Validation error: {error_message}\n"
        f"Bad payload: {bad_payload}\n"
        "Return corrected JSON only."
    )


def typed_repair_prompt(error_class: str, payload: dict, detail: str) -> str:
    repair_map = {
        "schema_repair": "Fix malformed structure and missing required fields.",
        "option_repair": "For MCQ, enforce exactly 4 labeled choices A/B/C/D.",
        "consistency_repair": "Fix answer so it is supported by question and choices.",
        "pedagogy_repair": "Improve explanation clarity and educational value.",
    }
    instruction = repair_map.get(error_class, "Fix payload while preserving task intent.")
    return (
        f"Repair class: {error_class}\n"
        f"Instruction: {instruction}\n"
        f"Error detail: {detail}\n"
        f"Payload: {payload}\n"
        "Return corrected JSON only."
    )
