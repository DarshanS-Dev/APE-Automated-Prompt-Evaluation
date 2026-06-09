# APE — Automated Prompt Evaluation
 
You changed your prompt. Did it break anything? APE tells you.
 
Register any HTTP endpoint, define golden input/output pairs and plain English rubric rules. APE hits your endpoint concurrently, LLM-grades every output, and returns a structured regression report showing exactly what broke between prompt versions.
 
**Zero SDK instrumentation. Zero changes to your app. Talks to any endpoint over HTTP.**
 
→ [Live API](https://ape-automated-prompt-evaluation.onrender.com/docs) · [Demo Video](https://youtu.be/IBNIV15B6XY) · [GitHub](https://github.com/DarshanS-Dev/APE-Automated-Prompt-Evaluation)
 
---
 
## The Problem
 
When teams update LLM prompts — rewording, model switch, context change — they have no reliable way to know if output behaviour regressed. Manual testing is slow and error-prone.
 
LangSmith and Braintrust require SDK instrumentation inside your production codebase. You rewrite imports, wrap calls, redeploy. APE skips all of that.
 
APE talks to your endpoint over HTTP. Your app stays untouched.
 
---
 
## How It Works
 
1. Register a project with your endpoint URL
2. Add golden pairs — JSON input payloads + expected behaviour in plain English
3. Add rubric rules — plain English constraints the output must satisfy
4. Trigger an eval run with a version tag (e.g. `v1.2` or `gpt-4o-switch`)
5. APE hits your endpoint for every golden pair concurrently via `httpx`
6. Each output is graded by an LLM judge against your rubric rules
7. Poll the results endpoint for a full regression report with a diff against the previous run
---
 
## Regression Diff
 
Every eval run is automatically compared against the previous run for the same project. Results are bucketed into four categories:
 
| Bucket | Meaning |
|---|---|
| `newly_failing` | Passed before, fails now — **regressions** |
| `newly_passing` | Failed before, passes now — fixes |
| `unchanged_failing` | Failed in both runs |
| `unchanged_passing` | Passed in both runs |
 
The diff is computed at read time using `golden_pair_id` as the stable match key across runs.
 
---
 
## API Endpoints
 
**Auth**
 
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user, returns JWT |
| POST | `/auth/login` | Login, returns JWT |
| POST | `/auth/key` | Exchange JWT for an API key (one-time reveal) |
 
**Projects & Evals** — all require `X-API-Key` header
 
| Method | Endpoint | Description |
|---|---|---|
| POST | `/projects` | Create a project with an endpoint URL |
| POST | `/projects/goldenpairs` | Add a golden input/output pair |
| POST | `/projects/rubric` | Add a rubric rule |
| POST | `/evals` | Trigger an eval run |
| GET | `/evals/{eval_id}/results` | Get results and regression diff |
 
Full interactive docs at [`/docs`](https://ape-automated-prompt-evaluation.onrender.com/docs).
 
---
 
## Example Usage
 
**1. Register and get an API key**
```bash
# Register
curl -X POST https://ape-automated-prompt-evaluation.onrender.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "yourpassword"}'
# → {"token": "<jwt>"}
 
# Exchange JWT for an API key (shown once, store it)
curl -X POST https://ape-automated-prompt-evaluation.onrender.com/auth/key \
  -H "Authorization: Bearer <jwt>"
# → {"key": "ape_..."}
```
 
**2. Create a project**
```bash
curl -X POST https://ape-automated-prompt-evaluation.onrender.com/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{"name": "Symptom Checker", "endpoint_url": "https://your-app.com/check"}'
```
 
**3. Add a golden pair and rubric rule**
```bash
curl -X POST https://ape-automated-prompt-evaluation.onrender.com/projects/goldenpairs \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "project_id": 1,
    "input_payload": {"symptoms": "fever and headache", "duration_days": 4},
    "expected_output": "Should recommend seeing a doctor since symptoms last more than 3 days"
  }'
 
curl -X POST https://ape-automated-prompt-evaluation.onrender.com/projects/rubric \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{"project_id": 1, "rule": "If symptoms last more than 3 days, the output must recommend seeing a doctor"}'
```
 
**4. Trigger an eval run and get results**
```bash
curl -X POST https://ape-automated-prompt-evaluation.onrender.com/evals \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{"project_id": 1, "prompt_version_tag": "v1.0-safe"}'
 
curl https://ape-automated-prompt-evaluation.onrender.com/evals/1/results \
  -H "X-API-Key: <your-api-key>"
```
 
---
 
## Tech Stack
 
| Layer | Choice | Why |
|---|---|---|
| API | FastAPI async | Native async, minimal overhead |
| ORM | SQLAlchemy 2.0 AsyncSession | Full async throughout, no sync bottlenecks |
| Migrations | Alembic | Schema version control |
| HTTP client | httpx | Concurrent endpoint hits via `asyncio.gather` |
| LLM judge | Groq (llama-3.3-70b-versatile) | OpenAI-compatible SDK, fast inference |
| Database | PostgreSQL on Neon | Serverless, zero ops |
| Auth | JWT + API keys | Human sessions via Bearer token; programmatic/CI access via hashed API keys |
| Deployment | Render | Simple, fast cold starts acceptable at MVP |
 
---
 
## Architecture Decisions
 
**LLM-as-judge over exact match** — Rubric rules and expected behaviour are plain English. Exact string matching misses semantically correct outputs that differ in wording. The LLM judge evaluates intent, not syntax.
 
**Two-phase `asyncio.gather()`** — Endpoint hits and judge calls run concurrently in separate gather phases. One timeout does not kill the whole run.
 
**`BackgroundTasks` over Celery** — Eval runs are kicked off as background tasks, keeping the MVP dependency-light. The upgrade path to Redis + Celery is clear when scale demands it.
 
**Diff at read time** — No FK stored on the run for comparison. The previous run is resolved at query time via `triggered_at`, with an optional override via query param.
 
**Dual auth model** — JWT for human sessions (30-minute expiry, stateless), API keys for programmatic and CI/CD access (hashed with SHA-256, never stored raw). Modeled after Anthropic and Stripe's key patterns. API keys are shown once on creation; only the hash lives in the database.
 
---
 
## Local Setup
 
```bash
git clone https://github.com/DarshanS-Dev/APE-Automated-Prompt-Evaluation
cd APE-Automated-Prompt-Evaluation
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
 
Create a `.env` file:
 
```env
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
GROQ_API_KEY=your_groq_api_key
GROQ_BASE_URL=https://api.groq.com/openai/v1
SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256
```
 
Run migrations and start the server:
 
```bash
alembic upgrade head
uvicorn app.main:app --reload
```
 
---
 
## Demo
 
Safe prompt → 3/3 golden pairs pass. Switch to a vague, unsafe system prompt → 2/3 fail. APE catches both regressions and buckets them as `newly_failing` in the diff report.
 
[![APE Demo](https://img.youtube.com/vi/IBNIV15B6XY/maxresdefault.jpg)](https://youtu.be/IBNIV15B6XY)
 
---
 
## Roadmap
 
- [ ] **GitHub Actions integration** — trigger an eval run automatically when a prompt file changes; fail the CI pipeline on regressions
- [ ] **Webhook support** — POST regression results to Slack or any URL on run completion
- [ ] **Self-hosted judge model** — swap Groq for any OpenAI-compatible endpoint
- [ ] **CLI wrapper** — Typer-based CLI around the HTTP API for local and CI use
---
 
## Why APE Exists
 
Promptfoo was the closest alternative — acquired by OpenAI in March 2026 and folded into OpenAI Frontier (enterprise-only, OpenAI models only). APE is the independent, multi-provider, HTTP-native alternative.