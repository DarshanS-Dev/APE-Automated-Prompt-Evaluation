# APE - Automated Prompt Evaluation

A framework-agnostic LLM evaluation platform that detects prompt regressions through HTTP-based test suites - no SDK instrumentation required.

You register an endpoint, define golden input/output pairs and plain English rubric rules. APE hits your endpoint concurrently, grades each output with an LLM judge, and returns a structured regression report showing exactly what broke between prompt versions.

**Live API:** https://ape-automated-prompt-evaluation.onrender.com/docs

---

## The Problem

When teams update LLM prompts - rewording, model switch, context change - they have no reliable way to know if output behaviour regressed. Manual testing is slow and error-prone. Existing tools like LangSmith and Braintrust require SDK instrumentation inside your production codebase.

APE talks to any endpoint over HTTP. Zero changes to your app.

---

## How It Works

1. Register a project with your endpoint URL
2. Add golden pairs - JSON input payloads + expected behaviour in plain English
3. Add rubric rules - plain English constraints the output must satisfy
4. Trigger an eval run with a version tag (e.g. `v1.2` or `gpt-4o-switch`)
5. APE hits your endpoint for every golden pair concurrently via `httpx`
6. Each output is graded by an LLM judge against your rubric rules
7. Poll the results endpoint for a full regression report with a diff against the previous run

---

## Regression Diff

Every eval run is automatically compared against the previous run for the same project. Results are bucketed into four categories:

- **newly_failing** - passed before, fails now (regressions)
- **newly_passing** - failed before, passes now (fixes)
- **unchanged_failing** - failed in both runs
- **unchanged_passing** - passed in both runs

The diff is computed at read time using `golden_pair_id` as the stable match key across runs.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/projects` | Create a project with an endpoint URL |
| `POST` | `/projects/goldenpairs` | Add a golden input/output pair |
| `POST` | `/projects/rubric` | Add a rubric rule |
| `POST` | `/evals` | Trigger an eval run |
| `GET` | `/evals/{eval_id}/results` | Get results and regression diff |

Full interactive docs at `/docs`.

---

## Example Usage

**Create a project**
```bash
curl -X POST https://ape-automated-prompt-evaluation.onrender.com/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Symptom Checker", "endpoint_url": "https://your-app.com/check"}'
```

**Add a golden pair**

```bash
curl -X POST https://ape-automated-prompt-evaluation.onrender.com/projects/goldenpairs \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "input_payload": {"symptoms": "fever and headache", "duration_days": 4},
    "expected_output": "Should recommend seeing a doctor since symptoms last more than 3 days"
  }'
```

**Add a rubric rule**

```bash
curl -X POST https://ape-automated-prompt-evaluation.onrender.com/projects/rubric \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "rule": "If symptoms last more than 3 days, the output must recommend seeing a doctor"
  }'
```

**Trigger an eval run**

```bash
curl -X POST https://ape-automated-prompt-evaluation.onrender.com/evals \
  -H "Content-Type: application/json" \
  -d '{"project_id": 1, "prompt_version_tag": "v1.0-safe"}'
```

**Get results**

```bash
curl https://ape-automated-prompt-evaluation.onrender.com/evals/1/results
```

---

## Tech Stack

* **FastAPI** - async route handlers
* **PostgreSQL** - via SQLAlchemy 2.0 async (`AsyncSession`)
* **Alembic** - migrations
* **httpx** - concurrent endpoint hits
* **Groq** - LLM judge via OpenAI-compatible SDK
* **Neon** - hosted PostgreSQL
* **Render** - deployment

---

## Architecture Decisions

**LLM-as-judge over exact match** - rubric rules and expected behaviour are plain English. Exact string matching would miss semantically correct outputs that differ in wording. The LLM judge evaluates intent, not syntax.

**Two-phase `asyncio.gather()`** - endpoint hits and judge calls run concurrently in separate gather phases. One timeout does not kill the whole run.

**FastAPI `BackgroundTasks` over Celery** - eval runs are kicked off as background tasks, keeping the MVP dependency-light. The upgrade path to Redis + Celery is clear when scale demands it.

**Diff computed at read time** - no FK stored on the run for comparison. The previous run is resolved at query time via `triggered_at`, with an optional override via query param.

---

## Local Setup

```bash
git clone https://github.com/DarshanS-Dev/APE-Automated-Prompt-Evaluation
cd APE-Automated-Prompt-Evaluation
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:

```
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
GROQ_API_KEY=your_groq_api_key
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

Run migrations and start the server:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

---

## Demo

Safe prompt -> 3/3 golden pairs pass. Switch to a vague, unsafe system prompt -> 2/3 fail. APE catches both regressions and buckets them as `newly_failing` in the diff report.

[![APE Demo](https://img.youtube.com/vi/IBNIV15B6XY/maxresdefault.jpg)](https://youtu.be/IBNIV15B6XY)

---

## Roadmap

* API key auth per project
* GitHub Actions CI webhook trigger
* Self-hosted judge model option
* CLI wrapper (Typer)