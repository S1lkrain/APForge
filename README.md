# APForge

Harness-driven AP-style generation infrastructure.

APForge is a modular educational generation system designed for controllable, agent-ready AP content generation.

It focuses on one core problem:

> Most educational LLM outputs are inconsistent, non-structured, and fail to reproduce real AP-style reasoning.

APForge introduces:

- Skill-based generation
- Structured output contracts
- Harness policy enforcement
- Evaluation + repair loops
- AP style pattern injection
- Agent-oriented orchestration

Instead of treating generation as a single prompt,
APForge treats it as a controlled pipeline.

---

# Why APForge Exists

Most AI education projects fail in predictable ways.

## #1 Generated Questions Don't Feel Like AP

Most models produce:

- generic questions
- weak distractors
- inconsistent difficulty
- poor AP-style reasoning structure

### APForge Fix

- AP style pattern injection
- structured generation stages
- controllable prompt orchestration

---

## #2 Structured Outputs Break

Educational pipelines need machine-readable outputs.

But normal prompting often causes:

- schema drift
- malformed JSON
- missing fields
- inconsistent metadata

### APForge Fix

- strict schema contracts
- validation harness
- repair layer
- fallback policies

---

## #3 Explanations Contradict Answers

A common LLM failure mode:

- answer says B
- explanation proves C

### APForge Fix

- answer consistency validation
- evaluation stages
- repair loops
- harness rejection policies

---

## #4 Educational Generation Doesn't Scale

Most "AI education apps" are:

- single prompts
- tightly coupled
- impossible to evaluate
- impossible to orchestrate

### APForge Fix

APForge separates generation into composable skills:

- QuestionSkill
- AnswerSkill
- ExplanationSkill
- EvaluationSkill

allowing:

- agent integration
- orchestration
- pipeline validation
- future multi-model execution

---

# Architecture

```text
Question Skill
        ↓
Answer Skill
        ↓
Explanation Skill
        ↓
Harness Validation
        ↓
Repair Layer
        ↓
Evaluation Pipeline
        ↓
Persistence + Dashboard
```

---

# Core Concepts

## Skill-Based Generation

Generation is decomposed into callable skills.

Instead of:

```text
single huge prompt
```

APForge uses:

```text
modular generation pipeline
```

This improves:

- controllability
- repairability
- observability
- orchestration

---

## Harness-Driven Validation

The harness acts as a policy layer between:

```text
LLM output
→ production acceptance
```

It supports:

- shadow
- warn
- enforce

rollout modes.

---

## Style Pattern Injection

APForge introduces AP-style pattern guidance.

Instead of training a custom model,
the system injects structured AP-style reasoning patterns into generation.

This allows:

- AP-style alignment
- lightweight controllability
- easier experimentation
- rapid iteration

---

# Features

- Skill-based architecture
- Structured schema outputs
- Evaluation + repair pipeline
- Harness policy enforcement
- OpenAI-compatible provider adapter
- React dashboard
- Offline evaluation support
- Traceable persistence layer

---

# Quickstart

```bash
python -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"

cp .env.example .env
```

Set:

```env
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

Run:

```bash
python -m ap_skill_generator
```

---

# Roadmap

- Multi-subject support
- Better pedagogical evaluation
- Agent memory integration
- Skill registry system
- Multi-provider orchestration
- Advanced style corpus injection
- Distributed evaluation pipeline

---

# Philosophy

APForge is not designed as:

```text
"just another AI study app"
```

It is an experiment in:

- controllable educational generation
- agent-oriented workflows
- AI evaluation infrastructure
- harness engineering

---

# License

MIT
