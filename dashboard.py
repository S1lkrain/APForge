from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import streamlit as st

# Ensure local `src` package imports work without editable install.
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ap_skill_generator.engine import APGenerationEngine
from ap_skill_generator.schema import GenerateRequest, QuestionType, Subject


def inject_styles() -> None:
    """Inject College Board inspired UI styles."""
    st.markdown(
        """
        <style>
            .stApp {
                background: linear-gradient(180deg, #fffdf5 0%, #fff9e8 100%);
                color: #4d3b14;
            }

            .block-container {
                max-width: 1120px;
                padding-top: 1.2rem;
                padding-bottom: 2rem;
            }

            .cb-shell {
                background: #fffdf8;
                border: 1px solid #f2dca4;
                border-radius: 14px;
                box-shadow: 0 4px 18px rgba(179, 129, 27, 0.08);
                padding: 1rem 1.2rem;
                margin-bottom: 1rem;
            }

            .cb-question-title {
                font-size: 1.2rem;
                font-weight: 700;
                margin-bottom: 0.4rem;
                color: #7a5711;
            }

            .cb-question-prompt {
                color: #5f4818;
                line-height: 1.6;
                margin-bottom: 0.9rem;
            }

            .cb-choice {
                border: 1px solid #ecd49a;
                border-radius: 10px;
                background: #fffdf6;
                margin: 0.5rem 0;
                padding: 0.7rem 0.9rem;
            }

            .cb-choice-selected {
                border-color: #d7aa43;
                background: #fff5cc;
            }

            .cb-choice-correct {
                border-color: #b98f34;
                background: #fff1bc;
            }

            .cb-choice-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 0.8rem;
            }

            .cb-choice-left {
                display: flex;
                align-items: center;
                gap: 0.7rem;
                color: #5f4818;
                line-height: 1.45;
            }

            .cb-badge {
                width: 28px;
                height: 28px;
                border-radius: 50%;
                border: 1px solid #cf9d30;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                color: #7a5711;
                flex-shrink: 0;
                background: #fff8db;
            }

            .cb-check {
                color: #9b741f;
                font-size: 1rem;
                font-weight: 700;
                flex-shrink: 0;
            }

            .cb-meta {
                color: #8a6a24;
                font-size: 0.9rem;
                margin-bottom: 0.75rem;
            }

            .stTextInput input,
            .stSelectbox [data-baseweb="select"] > div,
            .stNumberInput input {
                background-color: #fffef9;
                border: 1px solid #e8cb85;
                color: #4d3b14;
                border-radius: 10px;
            }

            .stTextInput input:focus,
            .stNumberInput input:focus {
                border-color: #d4a63b;
                box-shadow: 0 0 0 1px #d4a63b;
            }

            .stSlider [data-baseweb="slider"] [role="slider"] {
                background-color: #cf9d30;
                border-color: #cf9d30;
            }

            .stSlider [data-baseweb="slider"] > div > div > div {
                background-color: #ecd49a;
            }

            .stButton > button[kind="primary"] {
                background: linear-gradient(90deg, #f5bf43 0%, #e7aa2f 100%);
                border: 1px solid #d39b2c;
                color: #fffdf7;
                font-weight: 600;
                justify-content: flex-start;
                text-align: left;
            }

            .stButton > button[kind="primary"]:hover {
                background: linear-gradient(90deg, #eeb331 0%, #dd9d22 100%);
                border-color: #bf8718;
                color: #ffffff;
            }

            .stButton > button[kind="secondary"] {
                background: #fffdf6;
                border: 1px solid #ecd49a;
                color: #5f4818;
                font-weight: 500;
                justify-content: flex-start;
                text-align: left;
                padding: 0.65rem 1rem;
                border-radius: 10px;
                min-height: 2.75rem;
            }

            .stButton > button[kind="secondary"]:hover {
                border-color: #d7aa43;
                color: #4d3b14;
                background: #fff9e6;
            }

            .stAlert {
                background: #fff9e6;
                border: 1px solid #f0d48d;
                color: #5f4818;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_math_text(text: str) -> None:
    """Render text with common LaTeX delimiters in Streamlit markdown."""
    normalized = text
    normalized = re.sub(r"\\\((.*?)\\\)", r"$\1$", normalized, flags=re.DOTALL)
    normalized = re.sub(r"\\\[(.*?)\\\]", r"$$\1$$", normalized, flags=re.DOTALL)
    st.markdown(normalized)


def normalize_text(value: str) -> str:
    """Normalize text for robust answer-option matching."""
    return re.sub(r"\s+", " ", value.strip().lower())


def infer_correct_choice_idx(item: dict) -> int | None:
    """Infer the correct choice index from `answer` and `choices`."""
    choices = item.get("choices") or []
    if not choices:
        return None

    answer = str(item.get("answer", "")).strip()
    if not answer:
        return None

    letter_match = re.match(r"^\s*([A-Da-d])(?:[\).\s:-].*)?$", answer)
    if letter_match:
        idx = ord(letter_match.group(1).upper()) - ord("A")
        if 0 <= idx < len(choices):
            return idx

    normalized_answer = normalize_text(answer)
    for idx, choice in enumerate(choices):
        if normalize_text(str(choice)) == normalized_answer:
            return idx
    return None


def _mcq_state_key(item: dict, run_id: str | None) -> str:
    """Stable session_state key for the current MCQ (new run clears selection via new key)."""
    rid = (run_id or "").strip() or str(item.get("id") or "")
    if rid:
        return re.sub(r"[^a-zA-Z0-9_-]+", "_", rid)[:120]
    q = str(item.get("question") or "")[:200]
    return f"h_{abs(hash(q))}"


def render_choices(item: dict, *, run_id: str | None = None) -> None:
    """Render choices as clickable buttons (full-width option rows)."""
    choices = item.get("choices") or []
    if not choices:
        return

    letters = [chr(ord("A") + i) for i in range(len(choices))]
    state_key = f"mcq_sel_{_mcq_state_key(item, run_id)}"
    if state_key not in st.session_state:
        st.session_state[state_key] = None

    reveal = st.toggle("Reveal correct answer", value=True)
    correct_idx = infer_correct_choice_idx(item) if reveal else None

    st.caption("Click an option below to select your answer.")

    for idx, choice in enumerate(choices):
        letter = letters[idx]
        label = f"{letter}.  {choice}"
        if reveal and correct_idx == idx:
            label = f"{label}   ✓"
        is_selected = st.session_state[state_key] == idx
        if st.button(
            label,
            key=f"{state_key}_opt_{idx}",
            use_container_width=True,
            type="primary" if is_selected else "secondary",
        ):
            st.session_state[state_key] = idx
            st.rerun()


st.set_page_config(page_title="AP Skill Generator", layout="wide")
inject_styles()
st.title("AP Practice")
st.caption("College Board style practice interface")

if "engine" not in st.session_state:
    st.session_state.engine = APGenerationEngine()
engine: APGenerationEngine = st.session_state.engine

with st.container(border=False):
    st.markdown('<div class="cb-shell">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        subject = st.selectbox("Subject", [s.value for s in Subject], index=0)
    with col2:
        skill = st.text_input("Skill", value="limits")
    with col3:
        difficulty = st.slider("Difficulty", min_value=1, max_value=5, value=3)
    with col4:
        q_type = st.selectbox("Type", [t.value for t in QuestionType], index=0)

    if st.button("Generate New Question", type="primary", use_container_width=True):
        req = GenerateRequest(
            subject=Subject(subject),
            skill=skill,
            difficulty=difficulty,
            type=QuestionType(q_type),
        )
        try:
            result = engine.generate(req)
            st.session_state.last_result = result
            st.success("Question generated successfully.")
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))
    st.markdown("</div>", unsafe_allow_html=True)

result = st.session_state.get("last_result")
if result:
    item = result["item"]
    item_meta = item.get("metadata", {})
    meta_subject = item_meta.get("subject", "unknown")
    meta_difficulty = item_meta.get("difficulty", "unknown")
    st.markdown('<div class="cb-shell">', unsafe_allow_html=True)
    st.markdown('<div class="cb-question-title">Question</div>', unsafe_allow_html=True)
    st.caption(
        f"Run ID: {result.get('run_id', 'n/a')} · Subject: {meta_subject} · Difficulty: {meta_difficulty}"
    )
    st.markdown('<div class="cb-question-prompt">', unsafe_allow_html=True)
    render_math_text(item["question"])
    st.markdown("</div>", unsafe_allow_html=True)

    if item.get("choices"):
        render_choices(item, run_id=result.get("run_id"))
    else:
        st.info("This generated item has no multiple-choice options.")

    with st.expander("Explanation", expanded=False):
        render_math_text(item["explanation"])
        st.markdown("**Answer:**")
        render_math_text(item["answer"])

    with st.expander("Raw JSON", expanded=False):
        st.json(result)
    st.download_button(
        label="Export JSON",
        data=json.dumps(result, indent=2),
        file_name=f"{result['run_id']}.json",
        mime="application/json",
        type="tertiary",
    )
    st.markdown("</div>", unsafe_allow_html=True)

with st.expander("Run History", expanded=False):
    history = engine.query_items()
    st.dataframe(
        [
            {
                "run_id": h["run_id"],
                "subject": h["subject"],
                "skill": h["skill"],
                "difficulty": h["difficulty"],
                "type": h["type"],
                "status": h.get("final_status", "accepted"),
                "failure_reason": h.get("failure_reason_code", "NONE"),
                "question": h["question"][:120],
            }
            for h in history
        ],
        use_container_width=True,
    )
