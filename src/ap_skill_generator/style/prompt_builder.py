from __future__ import annotations

from .schema import StylePattern


def _humanize_token(token: str) -> str:
    return token.replace("_", " ")


def build_style_prompt(pattern: StylePattern) -> str:
    lines = [
        "AP-style MCQ guidance (follow when drafting the item):",
        "",
        pattern.style_summary,
        "",
    ]

    if pattern.wording_patterns:
        lines.append("Use AP-style wording such as:")
        for phrase in pattern.wording_patterns:
            lines.append(f"- {phrase}")
        lines.append("")

    focus_parts = list(pattern.cognitive_action) + list(pattern.representation)
    if focus_parts:
        lines.append("Focus on:")
        for item in focus_parts:
            lines.append(f"- {_humanize_token(item)}")
        lines.append("")

    if pattern.distractor_patterns:
        lines.append("Distractors should reflect:")
        for item in pattern.distractor_patterns:
            lines.append(f"- {_humanize_token(item)}")
        lines.append("")

    if pattern.notes:
        lines.append(f"Notes: {pattern.notes}")

    return "\n".join(lines).strip()
