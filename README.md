# AP Skill-Based Generation System

A modular, callable AP-style content generation engine designed for agent and pipeline integration.

## Features

- Skill-centric architecture: question, answer, and explanation as separate callable modules.
- Structured output schema with versioning (`schema_version`).
- Harness policy layer with machine-readable rollout modes: `shadow` / `warn` / `enforce`.
- OpenAI-compatible provider adapter via config.
- Persistence for runs/items/evals with trace metadata.
- React dashboard (`frontend/`) for parameterized generation, stats, and history.
- API endpoint (`/generate`) and SDK-style interface (`APGenerationEngine.generate`).

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Set environment variables in `.env`:

```bash
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
API_KEY=your_api_secret   # optional; leave empty for local dev without auth
CORS_ORIGINS=http://localhost:5173
```

## Run API

```bash
python -m ap_skill_generator
```

Defaults: `API_HOST=127.0.0.1`, `API_PORT=8000`.

Endpoints:

- `POST /generate` — generate one item (optional header `X-API-Key` when `API_KEY` is set)
- `GET /items?subject=ap_precalculus&skill=limits&difficulty=3`
- `GET /stats` — dashboard aggregates (totals, success rate, quality, week deltas)
- `GET /health`

Example payload:

```json
{
  "subject": "ap_precalculus",
  "skill": "limits",
  "difficulty": 3,
  "type": "mcq",
  "locale": "en-US"
}
```

Example response (abbreviated):

```json
{
  "run_id": "...",
  "request_id": "...",
  "item": { "question": "...", "choices": [], "answer": "...", "explanation": "...", "metadata": {} },
  "metrics": { "schema_valid": true, "answer_consistent": true },
  "harness": {
    "mode": "warn",
    "status": "accepted",
    "policy_status": "accepted",
    "used_fallback": false,
    "failure_reason_code": "NONE",
    "reasons": [],
    "attempt_count_by_skill": {},
    "repair_classes": []
  }
}
```

## Production checklist

- Set `API_KEY` and pass it on every request.
- Keep `API_HOST=127.0.0.1` behind a reverse proxy for public traffic.
- Tune `RATE_LIMIT_GENERATE` / `RATE_LIMIT_ITEMS`.
- Never commit `.env` (see `.gitignore`).
- Rotate keys if `.env` was ever committed.

## Run Dashboard (React)

Start the API, then the frontend dev server:

```bash
python -m ap_skill_generator

cd frontend
cp .env.example .env
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Vite proxies `/api` to the backend on port 8000.

If `API_KEY` is set, add it to `frontend/.env` as `VITE_API_KEY`.

## Run Tests

```bash
pytest -q
```

## Offline Evaluation

```bash
python scripts/run_eval.py
```

Acceptance threshold target: schema-valid rate >= 98%.

## Harness Configuration

Harness policy lives in `config/policy.json`:

- `mode`: rollout behavior (`shadow`, `warn`, `enforce`)
- `retry_budgets`: bounded retries per skill/repair stage
- `thresholds`: judge thresholds for schema/compliance/consistency/pedagogy
- `hard_fail_rules` / `soft_fail_rules`: enable/disable specific gate reasons
- `allow_one_soft_retry`: allow one extra recovery attempt on soft failures

Run output includes:

- `harness.status`: `accepted`, `accepted_with_warning`, `fallback`, or policy-level `rejected` (before fallback)
- `harness.policy_status`: decision before fallback substitution
- `harness.used_fallback`: whether a placeholder item was returned
- `harness.failure_reason_code`
- `harness.attempt_count_by_skill`
