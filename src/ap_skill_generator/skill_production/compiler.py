from __future__ import annotations

from ..computation.error_models import list_error_models
from .skill_spec import SkillSpec
from ..schema import GenerateRequest, QuestionType


def compile_generation_prompt(spec: SkillSpec, req: GenerateRequest) -> str:
    lines: list[str] = [
        f"Subject: {req.subject.value}",
        f"Skill: {spec.skill_id}",
        f"Difficulty (1-5): {req.difficulty}",
        f"Type: {req.type.value}",
        f"Locale: {req.locale}",
        "",
        "## Reasoning Skill",
        spec.core_reasoning.summary.strip(),
        "",
        "### Reasoning steps the item must require",
    ]
    for step in spec.core_reasoning.reasoning_steps:
        lines.append(f"- {step}")

    if spec.core_reasoning.anti_patterns:
        lines.extend(["", "### Do NOT generate"])
        for anti in spec.core_reasoning.anti_patterns:
            lines.append(f"- {anti}")

    lines.extend(["", "## Question archetypes (AP-style stem patterns)"])
    for archetype in spec.question_archetypes:
        lines.append(f"- {archetype.id}: {archetype.description}")
        for stem in archetype.stem_patterns:
            lines.append(f'  - Example stem: "{stem}"')

    if spec.distractor_patterns:
        lines.extend(["", "## Distractor patterns (wrong options must reflect these failure modes)"])
        for pattern in spec.distractor_patterns:
            lines.append(f"- {pattern.id}: {pattern.description} ({pattern.failure_mode})")
            for hint in pattern.generation_hints:
                lines.append(f"  - Hint: {hint}")

    if spec.prompt_constraints.generation_rules:
        lines.extend(["", "## Generation rules"])
        for rule in spec.prompt_constraints.generation_rules:
            lines.append(f"- {rule}")

    if spec.prompt_constraints.forbidden_content:
        lines.extend(["", "## Forbidden content"])
        for forbidden in spec.prompt_constraints.forbidden_content:
            lines.append(f"- {forbidden}")

    visual_enabled = spec.visual is not None and spec.visual.enabled

    if req.type == QuestionType.MCQ:
        if spec.computation and spec.computation.enabled:
            error_model_ids = sorted(list_error_models())
            computation_lines = [
                "",
                "## Computation contract",
                "This skill requires deterministic calculator verification.",
                "Do NOT include computed numeric answers, MCQ choices, or answer letters.",
                f"Allowed calculation methods: {', '.join(spec.computation.allowed_methods)}",
                f"Allowed error model IDs: {', '.join(error_model_ids)}",
            ]
            required_models = spec.computation.required_distractor_models
            if required_models:
                computation_lines.append(
                    "Required error models (each must appear in distractor_specs): "
                    + ", ".join(required_models)
                )
            computation_lines.extend(
                [
                    "Each distractor_spec.error_model must be an allowed error model ID above.",
                    "Return this JSON object only:",
                    "{",
                    '"question": "...",',
                    '"calculation_required": true,',
                    '"calculation_spec": {"method": "...", "inputs": {...}, "rounding": 2},',
                    '"distractor_specs": [',
                    '  {"error_model": "...", "why_wrong": "..."},',
                    '  {"error_model": "...", "why_wrong": "..."},',
                    '  {"error_model": "...", "why_wrong": "..."}',
                    "]",
                    "}",
                ]
            )
            lines.extend(computation_lines)
            return "\n".join(lines)
        type_block = (
            "Create one MCQ with exactly 4 choices. "
            "Set answer to one of A/B/C/D, and choices in that order."
        )
    else:
        type_block = (
            "Create one FRQ item with no choices (empty list). "
            "Provide a concise expected answer."
        )

    if visual_enabled:
        allowed_types = spec.visual.allowed_chart_types if spec.visual else []
        visual_lines = [
            "",
            "## Visual contract",
            "This skill requires a structured chart visual as evidence the question must reason about.",
            "The visual is a reasoning artifact — not decorative UI.",
            "Do NOT output image URLs.",
            "Do NOT describe the graph only in prose without structured chart data.",
            "The question stem must reference the visual using words like graph, figure, table, or data.",
            "Line and scatter charts: use numeric x values that support trend or comparison reasoning.",
            "Bar charts: use string category labels for x and numeric y values.",
        ]
        if allowed_types:
            visual_lines.append(f"Allowed chart types: {', '.join(allowed_types)}")
        visual_lines.extend(
            [
                "Return this JSON object only:",
                "{",
                '"question": "...",',
                '"choices": ["A. ...","B. ...","C. ...","D. ..."],',
                '"visual": {',
                '  "type": "chart",',
                '  "chart_type": "line",',
                '  "title": "...",',
                '  "x_label": "...",',
                '  "y_label": "...",',
                '  "data": [{"x": 0, "y": 100}, {"x": 1, "y": 120}],',
                '  "caption": "optional"',
                "}",
                "}",
            ]
        )
        lines.extend(visual_lines)
        return "\n".join(lines)

    lines.extend(
        [
            "",
            type_block,
            "Return this JSON object only:",
            "{"
            '"question": "...",'
            '"choices": ["A. ...","B. ...","C. ...","D. ..."] or []'
            "}",
        ]
    )
    return "\n".join(lines)
