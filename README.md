# APForge

**APForge is a constraint-oriented AP generation harness that helps AI models produce structured, answer-consistent, AP-style questions through SkillSpecs, schema contracts, validators, evaluators, and repair loops.**

APForge is the quality-control layer for AI-generated AP content. AI models generate candidate questions; APForge constrains, validates, repairs, and decides whether those questions are acceptable.

It is not positioned as “another AI AP question generator.” It is infrastructure that sits around models: candidates in, validated outputs out.

---

## Conceptual model

| Old framing | New framing |
|-------------|-------------|
| APForge generates AP-style questions. | AI models generate candidate questions. APForge constrains, validates, repairs, and accepts or rejects them. |

---

# Why APForge Exists

Most AI education projects fail in predictable ways.

## #1 AI Models Need Constraints, Not Just Prompts

A single prompt can ask a model to generate AP-style questions, but it cannot reliably enforce:

- schema validity
- answer consistency
- AP style alignment
- repair and rejection policies

APForge treats generation as a **constrained pipeline**, not a one-shot prompt. Models propose; the harness enforces contracts and policy.

---

## #2 Generated Questions Don't Feel Like AP

Most models produce:

- generic questions
- weak distractors
- inconsistent difficulty
- poor AP-style reasoning structure

### APForge approach

- SkillSpec-based AP style control
- AP style pattern injection
- structured generation stages
- harness policy enforcement

---

## #3 Structured Outputs Break

Educational pipelines need machine-readable outputs.

Normal prompting often causes:

- schema drift
- malformed JSON
- missing fields
- inconsistent metadata

### APForge approach

- structured schema contracts
- deterministic validators
- repair loops
- harness rejection policies

---

## #4 Explanations Contradict Answers

A common LLM failure mode:

- answer says B
- explanation proves C

### APForge approach

- answer-consistency checks
- LLM-based educational evaluators
- evaluation + repair pipeline
- harness rejection policies

---

## #5 Educational Generation Doesn't Scale

Most “AI education apps” are:

- single prompts
- tightly coupled
- hard to evaluate
- hard to orchestrate

### APForge approach

Generation is decomposed into controllable stages (skills, SkillSpecs, validation, repair) so pipelines can be observed, retried, and integrated with agents or products—without treating the LLM as the only source of truth.

---

# Usage modes

APForge supports multiple ways to run the harness. Capabilities differ by mode; not all modes are fully implemented yet.

## 1. APForge Core Mode

- No API key required
- One free **5-question AP sample set** per user (planned)
- Uses the **APForge Core Model** (hosted, constrained generation path)
- Basic **validation report**
- Limited **repair** attempts

## 2. BYOK Mode (Bring Your Own Key)

- Connect your own AI provider / API key
- Model calls go through the **backend**; keys are not exposed to the frontend
- More generations than Core
- Full **validation reports**
- More **repair** attempts

## 3. Future Pro Mode (planned)

- Hosted stronger model
- Batch worksheet generation
- Saved question bank
- PDF / Google Forms export
- Teacher dashboard
- Full evaluation history

---

# Architecture

The harness is a pipeline from user request to accepted or rejected output:

```text
User Request
        ↓
Mode Selection
  - APForge Core
  - BYOK
  - Future Pro
        ↓
Model Router / Provider Adapter
        ↓
SkillSpec + AP Style Patterns
        ↓
Candidate Generation
        ↓
Schema Contracts
        ↓
Deterministic Validators
        ↓
LLM Evaluators
        ↓
Repair Loop
        ↓
Accepted / Rejected Output
        ↓
Validation Report
```

**Model Router / Provider Adapter** — routes generation to APForge Core, BYOK providers, or (future) Pro-hosted models behind a single adapter surface.

**SkillSpecs** — declarative control over subject, skill, difficulty, and AP-style constraints for each generation path.

**Validators & evaluators** — deterministic checks first; LLM-based evaluators where judgment is required.

**Repair loop** — failed items can be revised within harness policy instead of silently shipping bad content.

---

# Core concepts

## Constraint-oriented generation

Generation is not “prompt and hope.” Candidates pass through contracts, validators, evaluators, and repair until they meet policy—or are rejected with a **validation report**.

## SkillSpec-based control

AP style and pedagogical constraints are expressed through **SkillSpecs** (and related style patterns), not only free-form prompts.

## Harness policy enforcement

The harness sits between raw model output and acceptance. It supports rollout modes (e.g. shadow, warn, enforce) so validation can be observed before hard rejection.

## Validation reports

Every run can surface what passed, what failed, and what was repaired—supporting debugging, teacher review, and future dashboard history.

---

# Features

- Constraint-oriented AP generation harness
- APForge Core Model mode (no key; sample generation)
- Bring Your Own Key (BYOK) provider mode
- Model Router / Provider Adapter
- SkillSpec-based AP style control
- Structured schema contracts
- Deterministic validation checks
- LLM-based educational evaluators
- Evaluation + repair pipeline
- Validation reports
- Harness policy enforcement
- React practice UI (demo / consumption layer)
- Traceable persistence layer
- Future dashboard and export workflow (roadmap)

---

# Quickstart

For local development with your own provider (BYOK-style):

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

APForge Core Mode (no key, limited sample set) and Pro features are described above; wiring in-repo may still be partial—see roadmap.

---

# Roadmap

- [ ] Free 5-question AP sample generation (Core)
- [ ] APForge Core Model support
- [ ] Model Router and provider abstraction
- [ ] BYOK provider support (keys on backend only)
- [ ] Validate / Repair mode for user-pasted AI questions
- [ ] Stronger validation reports
- [ ] Multi-subject SkillSpec registry
- [ ] Batch worksheet generation
- [ ] PDF / Google Forms export
- [ ] Teacher dashboard
- [ ] Full evaluation history
- [ ] Advanced AP style corpus injection

---

# Philosophy

APForge is **not** trying to replace AI models. It is designed to **sit around them**.

- Models generate **candidates**.
- APForge applies **constraints**.
- Only **validated** outputs are accepted.

The goal is open-source infrastructure for reliable AP-style generation: technical, observable, and honest about what prompts alone cannot guarantee—not hype about replacing teachers or models.

---

# License

MIT
