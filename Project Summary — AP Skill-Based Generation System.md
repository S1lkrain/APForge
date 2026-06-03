# Project Summary — APForge (Constraint-Oriented AP Generation Harness)

## Overview

APForge is a **constraint-oriented AP generation harness**—the quality-control layer for AI-generated AP content. AI models produce **candidate** questions; APForge applies **SkillSpecs**, **schema contracts**, **deterministic validators**, **LLM evaluators**, and **repair loops** to decide what is acceptable.

It is built as modular infrastructure (callable skills, SkillSpecs, validation pipeline) rather than a chatbot. The harness is agent-ready: generation is programmable, observable, and policy-driven.

**Positioning:** APForge helps models produce structured, answer-consistent, AP-style questions; it does not position itself as “the model that writes your exam.”

## Problem & Motivation

### AI models need constraints, not just prompts

A single prompt cannot reliably enforce schema validity, answer consistency, AP style alignment, or repair policy. Most educational LLM output remains inconsistent, non-structured, and weak on real AP-style reasoning.

### Persistent failure modes

- Generated questions often do not feel like AP (generic stems, weak distractors).
- Structured outputs break (schema drift, malformed JSON).
- Explanations contradict answers.
- Single-prompt “AI study apps” do not scale for evaluation or orchestration.

APForge addresses these with a **constrained pipeline**: candidate generation → contracts → validators → evaluators → repair → accept/reject + validation report.

## Usage modes (product direction)

| Mode | Summary |
|------|---------|
| **APForge Core** | No API key; free 5-question sample; APForge Core Model; basic validation report; limited repair |
| **BYOK** | User provider key via backend (not frontend); more generations; full reports; more repair |
| **Future Pro** | Stronger hosted model; batch worksheets; question bank; PDF/Forms export; teacher dashboard; full evaluation history |

## Architecture (harness flow)

```text
User Request → Mode Selection → Model Router / Provider Adapter
→ SkillSpec + AP Style Patterns → Candidate Generation
→ Schema Contracts → Deterministic Validators → LLM Evaluators
→ Repair Loop → Accepted / Rejected → Validation Report
```

## Key contributions

### 1) SkillSpec- and skill-centric control

Generation paths are controlled through **SkillSpecs** and composable skills (question, answer, explanation, evaluation stages), invokable programmatically with explicit parameters (subject, skill, difficulty, type).

### 2) Structured schema contracts

Outputs target a consistent, machine-usable schema (question, choices, answer, explanation, metadata) for storage, analytics, and downstream agents.

### 3) Validation, evaluation, and repair

- **Deterministic validators** for schema and consistency checks.
- **LLM-based evaluators** where judgment is required.
- **Repair loops** and harness **enforce / warn / shadow** policies.
- **Validation reports** for transparency and future dashboard history.

### 4) Model Router / Provider Adapter

Routing to APForge Core, BYOK providers, or (planned) Pro-hosted models behind one adapter—keys for BYOK stay on the backend.

## Demo / interface

A React practice UI demonstrates consuming harness output: subject/skill selection, generation, structured display. The UI is a consumption layer; the harness and validation pipeline are the core system.

## Philosophy

- Models generate candidates; APForge applies constraints.
- Only validated outputs are accepted.
- APForge does not try to replace AI models—it wraps them with infrastructure suitable for open-source extension and honest limits of prompt-only generation.

## Compliance / ethics

- Content is **AI-generated and original**
- No official AP questions or rubrics are used
- Not affiliated with College Board
