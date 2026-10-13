# PRD — Personal DevOS: Coding Submission → AI Analysis → WordPress Pipeline

**Document status:** v1.0  
**Primary implementation agent:** Codex  
**Primary human owner:** Project owner  
**Scope of this PRD:** Phase 1 only — automatically ingest Programmers/SWEA solution commits from GitHub, analyze and store them in this Django service, generate a blog draft, and send the draft to WordPress.  
**Design constraint:** The architecture must remain extensible for later Personal DevOS phases (public portfolio, daily intelligence/news, personal knowledge/RAG, background coding agents, and personal archive), but **those later features MUST NOT be implemented in this phase**.

---

## 0. Instructions to Codex — read this first

### 0.1 Operating mode

Treat this PRD as the source of truth for Phase 1.

Before editing code:

1. Inspect the repository.
2. Summarize the current state.
3. Create a short implementation plan broken into small milestones.
4. Identify any conflict between this PRD and the existing repository.
5. If no blocking conflict exists, proceed milestone by milestone.
6. Run tests after every meaningful milestone.
7. Keep the application runnable at the end of every milestone.
8. Do not silently invent credentials, URLs, repository layout, API endpoints, or user preferences.

For any ambiguous implementation detail that does **not** affect external credentials, security, irreversible behavior, or the product contract, choose the simplest maintainable option and document the choice.

### 0.2 Mandatory stop-and-ask rule

When live integration requires information that only the human owner can provide, **STOP the current task** and return a clearly labeled block:

```text
BLOCKED_USER_INPUT

Why I am blocked:
...

Please provide:
1. ...
2. ...
3. ...

What is already complete:
...

What I will do after you answer:
...
```

Do not fabricate missing values.  
Do not use guessed production URLs.  
Do not use placeholder secrets as though they were real.  
Do not publish a live WordPress post before the owner explicitly selects the publication mode.

The required human checkpoints are defined in Section 15.

### 0.3 Security rules

- Never commit passwords, API keys, GitHub tokens, WordPress Application Passwords, webhook secrets, `.env`, or cookies.
- Secrets must come from environment variables or a secret store.
- Provide `.env.example` containing names and explanations only.
- Never print full secrets to logs.
- Redact authorization headers and credentials from error logs.
- Verify GitHub webhook signatures before processing payloads.
- Do not send more personal/private data to an LLM than is necessary.
- Do not automatically deploy or merge code to production as part of this PRD.
- WordPress publication defaults to `draft`.
- Never scrape or republish the full text of a coding problem.

### 0.4 Agent-friendly repository

If it does not already exist, create an `AGENTS.md` based on this PRD containing:

- how to run the project;
- how to run tests;
- architecture boundaries;
- coding conventions;
- commands Codex should use before finishing a task;
- the mandatory stop-and-ask rules;
- a note that later Personal DevOS phases are out of scope.

Do not duplicate the whole PRD into `AGENTS.md`; keep it concise.

---

# 1. Product summary

## 1.1 Working name

**Personal DevOS — Coding Pipeline**

## 1.2 One-sentence description

A self-hosted Django service that converts the owner's coding-test activity into structured personal knowledge and reviewable blog assets:

```text
Programmers / SWEA
        ↓
BaekjoonHub or equivalent GitHub sync
        ↓
GitHub repository push
        ↓
Signed GitHub webhook
        ↓
Django ingestion
        ↓
Database ActivityEvent + CodingSubmission
        ↓
Background AI analysis
        ↓
Blog draft generation
        ↓
WordPress draft
        ↓
Django status/history
```

## 1.3 Primary user

For Phase 1, there is one owner/user.

Multi-user SaaS is explicitly out of scope, but models and service boundaries should avoid assumptions that would make a future owner/user foreign key impossible.

## 1.4 Main user problem

The owner solves coding problems, but the resulting learning evidence is fragmented:

- source code exists in a coding platform or GitHub;
- the reasoning behind the solution is not consistently documented;
- writing a technical blog post manually is repetitive;
- later it is difficult to review what was learned;
- portfolio evidence is not produced automatically.

The product should turn one coding submission into durable structured data and an editable blog artifact.

---

# 2. Goals and non-goals

## 2.1 Phase 1 goals

The system must:

1. receive GitHub `push` webhooks for a configured coding-solutions repository;
2. verify that deliveries really came from GitHub;
3. prevent duplicate webhook processing;
4. find newly added/modified coding solution files in the push;
5. identify whether a solution is from `programmers` or `swea`;
6. store the original solution and normalized metadata in the application's own database;
7. create a generic `ActivityEvent` representing the coding activity;
8. perform slow work outside the HTTP request using a background job queue;
9. call an LLM through a provider abstraction to generate structured analysis;
10. build a blog draft from:
    - trusted metadata;
    - verbatim user code;
    - structured AI analysis;
11. store the generated blog draft locally;
12. send the blog draft to WordPress through the WordPress REST API;
13. default the WordPress post to `draft`;
14. record WordPress post ID, URL, current sync status, errors, and timestamps;
15. provide an owner-only Django UI to inspect submissions, analyses, drafts, job state, and WordPress links;
16. provide Django admin support for core models;
17. include automated tests and local development documentation.

## 2.2 Future extensibility goals

The architecture should make it possible later to add:

- **Phase 2:** public portfolio / interests;
- **Phase 3:** daily intelligence/news and serendipity recommendations;
- **Phase 4:** personal knowledge search / embeddings / RAG;
- **Phase 5:** controlled background coding agents;
- **Phase 6:** browser/Android/photo/archive connectors.

Do not implement these now.

## 2.3 Non-goals

Do **not** implement in this phase:

- a custom replacement for BaekjoonHub;
- automatic login to Programmers or SWEA;
- browser automation against coding-test websites;
- scraping full problem statements;
- automatic WordPress production publishing without explicit owner opt-in;
- a vector database or RAG;
- autonomous coding agents;
- Chrome history collection;
- Android usage collection;
- photo/file archive;
- Kakao login;
- a multi-user SaaS;
- Kubernetes, Kafka, or microservices;
- custom model training/fine-tuning;
- a mobile app.

---

# 3. Product principles

## 3.1 Activity first

The long-term platform is event-oriented.

All meaningful personal actions should eventually be representable as an `ActivityEvent`.

For this phase:

```text
coding submission
        ↓
ActivityEvent(event_type="coding_submission")
```

Later sources such as articles, browser activity, projects, workouts, notes, and agent runs can reuse the same core concept.

## 3.2 Private by default

All newly ingested data is private by default.

A future public portfolio must use a separate publish boundary rather than simply exposing private objects.

For Phase 1, no public portfolio pages are required.

## 3.3 AI is a worker, not the source of truth

The source of truth is:

- GitHub metadata;
- repository path;
- commit SHA;
- original user code;
- owner-provided configuration.

AI-generated text must be stored separately and labeled as generated analysis.

The LLM must never rewrite the code that is inserted into the blog post. The exact stored source code must be inserted programmatically.

## 3.4 Human review before public publication

The default flow is:

```text
AI generates
→ Django stores
→ WordPress draft is created
→ human reviews
→ human publishes in WordPress
```

A future configurable auto-publish option may exist, but only if the owner explicitly enables it.

## 3.5 Simple modular monolith

Use one Django project with clearly separated Django apps/modules.

Do not create microservices.

---

# 4. Recommended technical architecture

Use the existing repository setup if compatible. If the repository is empty or new, prefer:

- Python 3.12+ unless the local environment requires another currently supported version;
- Django 5.2 LTS or a newer compatible supported Django version;
- Django REST Framework for future API extensibility;
- PostgreSQL;
- Redis as the Celery broker;
- Celery for background jobs;
- `requests` or `httpx` for external HTTP APIs;
- server-rendered Django templates for the owner dashboard;
- Django built-in authentication for Phase 1;
- pytest + pytest-django for tests;
- Ruff for formatting/linting;
- Docker Compose for local PostgreSQL + Redis;
- environment-variable based configuration.

Do not add a frontend framework unless an existing project already depends on one.

## 4.1 High-level diagram

```text
                         ┌──────────────────────┐
                         │ Programmers / SWEA   │
                         └──────────┬───────────┘
                                    │
                         existing sync extension
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ GitHub Repository    │
                         └──────────┬───────────┘
                                    │ push webhook
                                    ▼
┌────────────────────────────────────────────────────────┐
│ Django                                                 │
│                                                        │
│ integrations/github                                    │
│  - webhook verification                                │
│  - delivery idempotency                                │
│                                                        │
│ activity                                               │
│  - ActivityEvent                                       │
│                                                        │
│ coding                                                 │
│  - CodingSubmission                                    │
│  - platform parsers                                    │
│                                                        │
│ ai                                                     │
│  - provider abstraction                                │
│  - CodeAnalysis                                        │
│                                                        │
│ publishing                                             │
│  - BlogArtifact                                        │
│  - WordPress client                                    │
│                                                        │
│ dashboard                                              │
│  - owner UI                                            │
└───────────────┬────────────────────────────────────────┘
                │ enqueue
                ▼
        ┌──────────────────┐
        │ Redis + Celery   │
        └────────┬─────────┘
                 │
                 ├── fetch changed source
                 ├── parse metadata
                 ├── AI analyze
                 ├── generate blog artifact
                 └── sync WordPress
                            │
                            ▼
                  ┌───────────────────┐
                  │ WordPress REST API│
                  └───────────────────┘

PostgreSQL stores application state throughout the pipeline.
```

---

# 5. Django application boundaries

Prefer this logical structure:

```text
config/                 # Django project settings/urls/celery
apps/
    accounts/           # minimal owner auth helpers
    activity/           # generic activity event core
    integrations/       # GitHub / WordPress integration primitives
    coding/             # coding-specific domain
    ai/                 # provider abstraction + analysis
    publishing/         # blog artifact + WordPress synchronization
    dashboard/          # owner-facing pages
templates/
static/
tests/
```

If the repository already uses a different but coherent Django layout, preserve it and map these boundaries into the existing structure.

Do not create circular dependencies between apps.

Suggested dependency direction:

```text
activity  ← coding
coding    ← ai
coding    ← publishing
integrations used by coding/publishing services
dashboard may read all domains
```

---

# 6. Core data model

Exact field names may change to match project conventions, but the following information must be represented.

## 6.1 ActivityEvent

Purpose: generic long-term event stream for future Personal DevOS extensions.

Fields:

- `id`
- `owner` — FK to Django user
- `source` — enum/string, e.g. `github`
- `event_type` — e.g. `coding_submission`
- `external_id` — nullable provider-specific id
- `title`
- `occurred_at`
- `recorded_at`
- `visibility` — default `private`
- `metadata` — JSONField for non-critical extensible metadata
- `processing_status`
- `created_at`
- `updated_at`

Constraints:

- events are private by default;
- avoid storing secrets in `metadata`;
- indexing should support owner + occurred_at and event_type queries.

## 6.2 GitHubWebhookDelivery

Purpose: signature verification record, troubleshooting, idempotency.

Fields:

- `delivery_id` — unique; value from `X-GitHub-Delivery`
- `event_name`
- `repository_full_name`
- `received_at`
- `signature_valid`
- `processing_status`
- `processed_at`
- `error_code`
- `error_message`
- optional sanitized/minimized payload JSON if useful for debugging

Do not retain credentials or authorization headers.

Unique constraint:

```text
delivery_id
```

Duplicate deliveries must return an idempotent success response without creating duplicate submissions.

## 6.3 CodingSubmission

Fields:

- `id`
- `owner`
- `activity_event` — OneToOne/FK
- `platform` — `programmers` or `swea`
- `repository_full_name`
- `branch`
- `commit_sha`
- `file_path`
- `problem_id` — nullable until parsed
- `problem_title`
- `problem_url` — nullable
- `language`
- `source_code`
- `source_code_sha256`
- `submitted_at`
- `raw_metadata` — sanitized JSON
- `parse_status`
- `created_at`
- `updated_at`

Uniqueness:

```text
(repository_full_name, commit_sha, file_path)
```

The stored source code is immutable for that submission record.

## 6.4 CodeAnalysis

One analysis per submission for the active prompt/model version, with room for later versioning.

Fields:

- `id`
- `submission`
- `status`
- `summary`
- `approach`
- `algorithm_tags` — JSON list
- `time_complexity`
- `space_complexity`
- `key_insights` — JSON list or text
- `possible_mistakes` — JSON list
- `alternative_approaches` — JSON list
- `study_notes`
- `provider`
- `model`
- `prompt_version`
- `input_tokens` — nullable
- `output_tokens` — nullable
- `estimated_cost` — nullable decimal
- `latency_ms` — nullable
- `raw_response` — sanitized, optional
- `error_message`
- `created_at`
- `updated_at`

The LLM must be asked for machine-parseable structured output.

Validation must occur before a successful analysis is stored.

## 6.5 BlogArtifact

Purpose: local canonical record of what is intended for publication.

Fields:

- `id`
- `submission`
- `analysis`
- `title`
- `slug`
- `content_markdown` or canonical structured content
- `content_html`
- `publication_status`
- `wordpress_post_id` — nullable
- `wordpress_url` — nullable
- `wordpress_status` — nullable
- `last_sync_at`
- `last_error`
- `created_at`
- `updated_at`

Statuses should distinguish at least:

```text
generated
wordpress_pending
wordpress_draft_created
wordpress_published
sync_failed
```

## 6.6 TaskRun or PipelineRun

Purpose: minimal observability for background jobs.

Fields:

- `id`
- `submission` nullable
- `task_type`
- `status`
- `attempt`
- `started_at`
- `finished_at`
- `duration_ms`
- `error_code`
- `error_message`
- `metadata` sanitized JSON

Do not rely only on console logs to understand failures.

---

# 7. GitHub ingestion requirements

## 7.1 Webhook endpoint

Provide an endpoint such as:

```text
POST /webhooks/github/
```

Requirements:

1. accept raw request body;
2. verify `X-Hub-Signature-256` using `GITHUB_WEBHOOK_SECRET`;
3. read `X-GitHub-Delivery`;
4. read `X-GitHub-Event`;
5. support `ping`;
6. process `push`;
7. ignore unsupported events safely;
8. store delivery state;
9. return quickly;
10. queue slow work only after the relevant database transaction commits.

The webhook endpoint is public but must not trust unauthenticated payload data.

Use constant-time comparison for signatures.

## 7.2 Repository allowlist

Only process configured repositories.

Environment/configuration should support:

```text
GITHUB_ALLOWED_REPOSITORIES=owner/repo1,owner/repo2
GITHUB_ALLOWED_BRANCHES=main
```

Unexpected repositories or branches should be ignored and logged safely.

## 7.3 Fetching changed source

Do not assume the webhook body contains every file's source text.

The asynchronous worker may use the GitHub API/raw content at the exact commit SHA.

If a repository is private, a token is required.

Never fetch `main` when the event refers to a specific commit; use the push's commit SHA to preserve historical correctness.

## 7.4 GitHub token

Support:

```text
GITHUB_TOKEN=
```

Rules:

- optional for public repo development if the GitHub API path works without it;
- required for private repositories;
- never persist the token in database fields;
- use least privilege;
- do not log the token.

## 7.5 File filtering

Only consider likely solution files, for example:

```text
.py .java .cpp .cc .c .js .ts .kt .swift .go .rs
```

Ignore:

- README-only changes unless used as supplementary metadata;
- images;
- generated files;
- unrelated repo files.

Do not hardcode one BaekjoonHub path format before inspecting the owner's real repository.

---

# 8. Platform parser architecture

Create a small parser interface rather than embedding platform-specific path parsing throughout the application.

Example conceptual interface:

```python
class SubmissionParser(Protocol):
    def can_parse(self, file_path: str, context: dict) -> bool: ...
    def parse(self, file_path: str, source: str, context: dict) -> ParsedSubmission: ...
```

Implement:

```text
ProgrammersSubmissionParser
SWEASubmissionParser
```

The normalized output should contain:

```text
platform
problem_id
problem_title
problem_url
language
source_code
submitted_at
metadata
```

### Critical rule

Do not invent BaekjoonHub directory conventions.

At Human Checkpoint A, inspect representative commits/paths from the real repository.

If the path/README format cannot be reliably inferred, stop and ask the owner for 2–5 representative solution paths or commits.

Keep parsing rules isolated and fixture-tested so future platform support can be added without editing the rest of the pipeline.

---

# 9. AI analysis requirements

## 9.1 Provider abstraction

Create a provider-neutral interface.

Conceptual API:

```python
class LLMProvider(Protocol):
    def analyze_code(self, request: CodeAnalysisRequest) -> CodeAnalysisResult: ...
```

Provide:

- a deterministic/mock provider for tests;
- one live provider only after Human Checkpoint B.

Do not hardcode a transient model name across business logic.

Use configuration:

```text
LLM_PROVIDER=
LLM_MODEL=
LLM_API_KEY=
LLM_TIMEOUT_SECONDS=
```

## 9.2 Analysis input

The LLM may receive:

- platform;
- problem title;
- problem URL;
- available short metadata;
- programming language;
- owner's source code.

Avoid sending:

- secrets;
- unrelated repository files;
- full private GitHub repository contents;
- full scraped problem statements.

## 9.3 Analysis output schema

Require structured output equivalent to:

```json
{
  "summary": "...",
  "approach": "...",
  "algorithm_tags": ["..."],
  "time_complexity": "...",
  "space_complexity": "...",
  "key_insights": ["..."],
  "possible_mistakes": ["..."],
  "alternative_approaches": ["..."],
  "study_notes": "..."
}
```

Validate the response.

If validation fails:

- mark the attempt failed;
- retry only according to bounded retry rules;
- never generate a WordPress draft from invalid analysis.

## 9.4 Prompt rules

The system prompt must explicitly say:

- do not claim certainty when problem context is insufficient;
- infer algorithm properties only from available evidence;
- do not fabricate problem constraints;
- do not rewrite the solution code;
- do not reproduce a missing full problem statement;
- write Korean explanatory prose unless configuration says otherwise;
- output only the expected structured schema.

Store a `prompt_version`.

---

# 10. Blog generation requirements

## 10.1 Canonical template

Generate a draft with a predictable structure:

```text
# [Platform] Problem title

문제 링크

## 풀이 요약

## 사용한 알고리즘 / 자료구조

## 풀이 과정

## 시간 복잡도

## 공간 복잡도

## 핵심 포인트 / 실수하기 쉬운 부분

## 다른 접근 방법

## 코드

## 공부 메모
```

The exact source code section must be inserted from `CodingSubmission.source_code`, not regenerated by the LLM.

## 10.2 Copyright/scraping constraint

Do not copy the entire coding problem statement into the blog.

At most use:

- problem title;
- official problem URL;
- owner-authored concise summary if available;
- AI's high-level explanation derived from code/metadata.

If a repository README contains a copied problem statement, do not automatically republish it.

## 10.3 HTML safety

- HTML-escape code;
- sanitize or generate trusted HTML from controlled templates;
- never render arbitrary LLM HTML without sanitization;
- preserve line breaks and code formatting.

## 10.4 Draft reproducibility

The local `BlogArtifact` is the canonical generated artifact.

If WordPress synchronization fails, the artifact must remain available locally and retryable.

---

# 11. WordPress integration

Use the official WordPress REST API.

Expected post endpoint shape:

```text
POST {WORDPRESS_BASE_URL}/wp-json/wp/v2/posts
```

Use WordPress Application Password authentication over HTTPS unless the owner's WordPress environment requires another supported mechanism.

Configuration:

```text
WORDPRESS_BASE_URL=
WORDPRESS_USERNAME=
WORDPRESS_APPLICATION_PASSWORD=
WORDPRESS_DEFAULT_STATUS=draft
WORDPRESS_CATEGORY_IDS=
WORDPRESS_TAG_IDS=
WORDPRESS_TIMEOUT_SECONDS=
```

## 11.1 Default behavior

Initial default:

```text
WORDPRESS_DEFAULT_STATUS=draft
```

Never choose `publish` without explicit owner confirmation.

## 11.2 Sync behavior

On successful creation, store:

- WordPress post ID;
- WordPress link;
- returned status;
- last sync timestamp.

On failure:

- retain the local artifact;
- store sanitized error details;
- apply bounded retries for transient failures;
- show a retry action in the dashboard or admin;
- never create multiple WordPress posts because of a blind retry.

### Idempotency strategy

Before retrying creation, determine whether a post has already been created.

Prefer a stable local-to-WordPress mapping through `wordpress_post_id`.

If the remote response is ambiguous after a network timeout, do not blindly create a duplicate. Mark the sync as requiring reconciliation and expose the state to the owner.

---

# 12. Background jobs and Celery

The GitHub webhook request must not wait for:

- GitHub file download;
- LLM call;
- blog generation;
- WordPress API call.

Recommended pipeline:

```text
GitHub POST
   ↓
verify + persist delivery
   ↓
HTTP 2xx
   ↓
Celery: ingest_push
   ↓
create CodingSubmission(s)
   ↓
Celery: analyze_submission
   ↓
create CodeAnalysis
   ↓
Celery: generate_blog_artifact
   ↓
create BlogArtifact
   ↓
Celery: sync_wordpress
   ↓
WordPress draft
```

Tasks must be:

- retry-safe;
- idempotent where possible;
- bounded in retry count;
- explicit about transient vs permanent failures.

Suggested retry cases:

Transient:
- connection timeout;
- 429;
- selected 5xx;
- temporary Redis/network issues.

Permanent/user-action:
- invalid WordPress credentials;
- invalid GitHub permissions;
- parser cannot identify platform;
- LLM output repeatedly fails schema validation.

Do not create infinite retry loops.

---

# 13. Owner dashboard

Use server-rendered Django pages.

Minimum pages:

## 13.1 Login

Django built-in owner authentication is sufficient.

## 13.2 Dashboard

Show:

- recent coding submissions;
- platform;
- problem title/id;
- commit SHA shortened;
- ingestion status;
- analysis status;
- WordPress status;
- timestamp;
- failed task count/attention indicator.

## 13.3 Submission detail

Show:

- normalized metadata;
- original source code;
- AI analysis;
- generated blog content;
- WordPress link if present;
- processing timeline;
- sanitized error state;
- manual retry controls for appropriate failed steps.

## 13.4 Integration status

Show configured/not-configured status without exposing secrets:

```text
GitHub webhook secret: configured / missing
GitHub token: configured / missing
LLM provider: configured / missing
WordPress: configured / missing
Redis/Celery: healthy / unhealthy
```

Never display actual secret values.

---

# 14. API / service contracts for future phases

Even though only the dashboard is required now, keep business logic out of views.

Prefer service methods such as:

```text
GithubIngestionService.handle_push(...)
SubmissionService.create_from_parsed(...)
AnalysisService.analyze(...)
BlogService.generate(...)
WordPressService.create_draft(...)
```

This makes it possible later for:

- REST endpoints;
- a mobile app;
- a Chrome extension;
- background agents;
- MCP/tools;
- scheduled jobs

to call the same domain logic.

Do not make templates or HTTP views the only place where business logic exists.

---

# 15. Mandatory human checkpoints

Codex must stop at the following points if the values are not already securely available.

## Checkpoint A — real GitHub/BaekjoonHub repository

**When:** after the Django scaffold, core models, webhook signature verification, mocked pipeline, and tests are working.

Ask the owner for:

1. GitHub repository URL/full name containing the auto-uploaded Programmers/SWEA solutions.
2. Whether the repository is public or private.
3. Which branch should be monitored.
4. 2–5 representative Programmers/SWEA commit/file paths if Codex cannot inspect them itself.
5. Whether BaekjoonHub is the exact uploader or a different extension/tool.
6. If the repository is private, a safe method for supplying a GitHub token.
7. The externally reachable Django base URL **or** whether the owner wants local webhook testing first.

Do not guess path conventions.

## Checkpoint B — live LLM provider

**When:** the provider interface, mock implementation, schema validation, and unit tests are complete.

Ask:

1. Which LLM provider should be used for Phase 1.
2. API key supply method.
3. Preferred model, if the owner has one.
4. Whether minimizing cost or maximizing analysis quality is the priority.
5. Desired blog language (default Korean if owner does not care).

Do not hardcode the API key.

## Checkpoint C — WordPress

**When:** WordPress client interface and mocked tests are complete.

Ask:

1. WordPress base URL, e.g. `https://example.com`.
2. WordPress username.
3. WordPress Application Password supply method.
4. Whether WordPress REST API is reachable over HTTPS.
5. Desired default status:
   - recommended: `draft`;
   - `publish` only after explicit confirmation.
6. Optional category/tag IDs if the owner wants them.

Do not proceed to a live POST until these are provided.

Before the first live POST, show the owner:

```text
Target WordPress site:
Target endpoint:
Post status:
Example title:
No secret values:
```

Then perform a single test draft creation.

## Checkpoint D — deployment/webhook exposure

**When:** local pipeline passes and a real GitHub webhook must reach Django.

Ask:

1. preferred deployment/tunnel option if none exists;
2. production hostname;
3. whether HTTPS is configured;
4. environment variable/secret configuration method.

Do not expose a local development server directly to the Internet without an appropriate tunnel/deployment.

---

# 16. Configuration contract

Create `.env.example` with explanatory comments and at least:

```text
DJANGO_SECRET_KEY=
DJANGO_DEBUG=
DJANGO_ALLOWED_HOSTS=
DATABASE_URL=

REDIS_URL=
CELERY_BROKER_URL=

OWNER_USERNAME=                  # optional bootstrap mechanism; do not store password here if unsafe

GITHUB_WEBHOOK_SECRET=
GITHUB_TOKEN=
GITHUB_ALLOWED_REPOSITORIES=
GITHUB_ALLOWED_BRANCHES=main

LLM_PROVIDER=
LLM_MODEL=
LLM_API_KEY=
LLM_TIMEOUT_SECONDS=60

WORDPRESS_BASE_URL=
WORDPRESS_USERNAME=
WORDPRESS_APPLICATION_PASSWORD=
WORDPRESS_DEFAULT_STATUS=draft
WORDPRESS_CATEGORY_IDS=
WORDPRESS_TAG_IDS=
WORDPRESS_TIMEOUT_SECONDS=30
```

If a library uses a different standard variable, document it.

Validate required settings on startup or in a dedicated health/config check, but allow mocked/local development without live external integrations.

---

# 17. Testing requirements

A feature is not complete unless relevant tests exist.

## 17.1 Unit tests

At minimum:

- GitHub HMAC signature validation success;
- invalid signature rejection;
- `ping` handling;
- duplicate delivery idempotency;
- repository allowlist;
- branch filtering;
- Programmers parser fixtures;
- SWEA parser fixtures;
- unsupported file ignored;
- submission uniqueness;
- LLM structured output validation;
- invalid LLM result does not publish;
- blog template preserves source code exactly;
- dangerous HTML is escaped/sanitized;
- WordPress response parsing;
- WordPress transient failure handling;
- WordPress auth failure classified as user action;
- secret redaction.

## 17.2 Integration tests

Using mocks/fakes:

```text
GitHub push fixture
→ webhook
→ queued pipeline/eager task mode
→ CodingSubmission
→ ActivityEvent
→ CodeAnalysis
→ BlogArtifact
→ mocked WordPress draft
```

Assert that a duplicate webhook produces only one submission and one remote create request.

## 17.3 Manual end-to-end test

After all human checkpoints:

1. submit one simple test solution through the owner's normal workflow;
2. confirm GitHub commit arrives;
3. confirm GitHub webhook delivery is accepted;
4. confirm Django records the submission;
5. confirm AI analysis exists;
6. confirm local blog artifact exists;
7. confirm one WordPress draft exists;
8. confirm the source code matches the GitHub version exactly;
9. confirm dashboard links to it;
10. repeat the same webhook delivery and confirm no duplicate post is created.

---

# 18. Observability and failure handling

Use structured logging where practical.

Log identifiers:

- webhook delivery ID;
- repository;
- commit SHA;
- submission ID;
- task run ID;
- WordPress post ID.

Do not log:

- webhook secret;
- GitHub token;
- WordPress Application Password;
- LLM API key;
- Authorization headers.

Provide enough state in DB/admin/dashboard that the owner can answer:

- What did the system receive?
- Which step is running?
- Which step failed?
- Can it be retried?
- Did WordPress already receive the post?
- How many LLM tokens/cost were used when available?

---

# 19. Security requirements

1. `DEBUG=False` in production.
2. Secrets from environment only.
3. GitHub webhook HMAC-SHA256 verification.
4. Constant-time signature comparison.
5. Allowlist repository and branch.
6. HTTPS for live WordPress authentication.
7. Owner-only dashboard.
8. CSRF protection for normal owner forms.
9. Webhook endpoint may be CSRF-exempt only because it uses GitHub signature verification.
10. Validate/sanitize all external payloads.
11. Escape code and generated HTML.
12. Configure sensible HTTP timeouts.
13. No unbounded input sizes.
14. No arbitrary repository URL fetching based solely on untrusted webhook values.
15. No shell execution from webhook or LLM content.
16. No external publication from unvalidated AI output.
17. No full problem-statement scraping/republication.
18. Keep dependency versions pinned/reproducible.

---

# 20. Suggested implementation milestones

Codex should work in this order.

## Milestone 0 — repository audit

Deliverables:

- current-state summary;
- implementation plan;
- architectural conflicts;
- `AGENTS.md` if missing.

No external credentials needed.

## Milestone 1 — local foundation

Deliverables:

- Django project/app boundaries;
- PostgreSQL configuration;
- Redis/Celery configuration;
- Docker Compose for dependencies;
- owner authentication;
- `.env.example`;
- health page/command;
- pytest/ruff setup.

Acceptance:

- application starts locally;
- test suite passes;
- Celery test task works.

## Milestone 2 — core domain

Deliverables:

- ActivityEvent;
- GitHubWebhookDelivery;
- CodingSubmission;
- CodeAnalysis;
- BlogArtifact;
- TaskRun/PipelineRun;
- admin integration;
- migrations.

Acceptance:

- models/migrations/tests pass;
- no external integration required.

## Milestone 3 — GitHub webhook shell

Deliverables:

- webhook endpoint;
- signature verification;
- delivery idempotency;
- repository/branch filtering;
- mocked push fixtures;
- enqueue logic.

Acceptance:

- signed fixture accepted;
- invalid signature rejected;
- duplicate delivery idempotent.

Then invoke **Checkpoint A** before hardcoding real repository parsing assumptions.

## Milestone 4 — platform parsing

Deliverables:

- parser interface;
- Programmers parser;
- SWEA parser;
- fixtures from owner's actual repository;
- source fetching at exact commit SHA.

Acceptance:

- representative real paths parse correctly;
- unsupported paths are safely skipped.

## Milestone 5 — AI abstraction

Deliverables:

- provider interface;
- mock provider;
- structured result schema;
- validation;
- prompt versioning;
- tests.

Then invoke **Checkpoint B** before live provider setup.

## Milestone 6 — blog artifact

Deliverables:

- deterministic article template;
- exact code insertion;
- HTML escaping/sanitization;
- local BlogArtifact;
- preview in dashboard.

Acceptance:

- article renders without WordPress;
- no full problem statement copied;
- code is byte/line equivalent to stored source.

## Milestone 7 — WordPress abstraction

Deliverables:

- WordPress client;
- mock tests;
- idempotency/reconciliation state;
- bounded retry behavior.

Then invoke **Checkpoint C** before live WordPress request.

## Milestone 8 — background pipeline

Deliverables:

- Celery orchestration;
- TaskRun/PipelineRun tracking;
- retries;
- transaction-safe enqueue;
- failure states.

Acceptance:

- end-to-end mocked pipeline passes;
- webhook response is not blocked by LLM/WordPress latency.

## Milestone 9 — owner dashboard

Deliverables:

- dashboard list;
- submission detail;
- integration health;
- retry UI/actions where safe;
- clear processing state.

## Milestone 10 — live end-to-end

Invoke **Checkpoint D** if public reachability is missing.

Run the manual end-to-end test from Section 17.3.

---

# 21. Acceptance criteria / Definition of Done

Phase 1 is done only when all of the following are true:

- [ ] A valid GitHub push from the configured coding repository is accepted.
- [ ] Invalid webhook signatures are rejected.
- [ ] Replayed deliveries do not duplicate data.
- [ ] Programmers and SWEA submissions are normalized from the owner's real repository layout.
- [ ] Original source code is stored in PostgreSQL.
- [ ] An ActivityEvent is created.
- [ ] Long-running processing happens in Celery, not inside the webhook request.
- [ ] AI analysis uses a provider abstraction and validated structured output.
- [ ] A local blog artifact is generated.
- [ ] The blog post never contains a scraped full problem statement.
- [ ] The code block uses the exact stored source, not AI-rewritten code.
- [ ] WordPress receives one post as a draft by default.
- [ ] Remote post ID and URL are stored.
- [ ] Transient failures can be retried without obvious duplication.
- [ ] Permanent integration failures are surfaced to the owner.
- [ ] Owner can view submissions/status/errors in the dashboard.
- [ ] Secrets are not committed or logged.
- [ ] Unit and integration tests pass.
- [ ] Local setup is documented.
- [ ] A fresh clone can be started from documentation.
- [ ] Later Personal DevOS features can add connectors/events without rewriting the Phase 1 core.

---

# 22. Future extension map — design for it, do not build it

## 22.1 Phase 2 — public portfolio / interests

Reuse:

- `ActivityEvent`;
- owner identity;
- `BlogArtifact`.

Add later:

```text
PublicArtifact
PublishCandidate
PortfolioProject
InterestSnapshot
```

Important boundary:

```text
private domain
→ explicit publication transform
→ public domain
```

Do not make public pages query arbitrary private `ActivityEvent` records.

## 22.2 Phase 3 — daily intelligence/news

Add a new connector:

```text
NewsConnector
→ ActivityEvent / KnowledgeItem
→ ranking
→ DailyBrief
```

Reuse Celery, TaskRun, integration health, and dashboard patterns.

## 22.3 Phase 4 — personal knowledge / RAG

Add:

```text
KnowledgeItem
Embedding
Retrieval
```

Prefer PostgreSQL + pgvector first rather than introducing a separate vector database prematurely.

Structured fields remain in SQL; embeddings are for semantic retrieval, not a replacement for relational data.

## 22.4 Phase 5 — background coding agent

Add:

```text
AgentRun
AgentStep
PermissionTier
Approval
Sandbox
```

Reuse:

- task/job observability;
- audit patterns;
- human approval concepts.

The agent must not be allowed to modify production directly.

## 22.5 Phase 6 — personal archive

New connectors may create ActivityEvents and KnowledgeItems:

```text
ChromeConnector
AndroidConnector
PhotoConnector
FileConnector
```

Large binary files belong in object storage, not PostgreSQL blobs.

---

# 23. Coding standards for this project

- Favor boring, explicit code over clever abstractions.
- Use type hints for service interfaces and external API payload/result objects where practical.
- Keep external provider code behind clients/adapters.
- Keep Django views thin.
- Keep Celery tasks thin; call service-layer functions.
- Use transactions deliberately.
- Use `transaction.on_commit(...)` or equivalent when enqueueing work that depends on newly committed rows.
- Add unique constraints to enforce idempotency at the database level where possible.
- Validate external JSON before domain use.
- Prefer enums/choices for important states.
- Store timestamps timezone-aware.
- Add indexes based on actual query patterns.
- Avoid generic JSON blobs for fields that are core to business logic.
- JSONField is acceptable for flexible provider metadata.
- Keep migrations small and reversible where practical.

---

# 24. Documentation Codex must leave behind

Create/update:

```text
README.md
AGENTS.md
docs/
    architecture.md
    local-development.md
    github-webhook-setup.md
    wordpress-setup.md
    operations.md
```

`architecture.md` should contain:

- system diagram;
- app responsibilities;
- pipeline sequence;
- data model summary;
- retry/idempotency strategy;
- future extension boundaries.

`local-development.md` should contain copy-paste commands for Windows-friendly development where possible.

`github-webhook-setup.md` must explain:

- endpoint;
- `application/json`;
- webhook secret;
- push event;
- how to inspect deliveries;
- never to commit the secret.

`wordpress-setup.md` must explain:

- Application Password creation;
- HTTPS;
- environment variables;
- draft default;
- how to run a safe test.

`operations.md` must explain:

- how to inspect Celery;
- how to retry failed items;
- where logs are;
- how to diagnose GitHub/LLM/WordPress failures;
- how to rotate credentials.

---

# 25. Expected owner-visible workflow

After configuration, the owner should experience:

1. Solve a Programmers or SWEA problem normally.
2. Existing browser extension/tool pushes the solution to GitHub.
3. No additional manual action is required for ingestion.
4. Django dashboard soon shows:
   - submission detected;
   - analysis queued;
   - analysis complete;
   - WordPress draft created.
5. Owner opens the generated draft.
6. Owner edits if needed.
7. Owner manually publishes it in WordPress.
8. Django retains the coding submission, analysis, and publication link as durable personal history.

The system should feel like an automation layer around the owner's existing workflow rather than a replacement for the coding platforms.

---

# 26. First Codex prompt after adding this PRD

Use this exact intent, adjusting only repository-specific context:

```text
Read prd.md completely before making changes.

Start with Milestone 0 only:
1. inspect the repository,
2. summarize the current architecture and files,
3. identify conflicts with the PRD,
4. propose a milestone-by-milestone implementation plan,
5. create or update a concise AGENTS.md that makes this repository agent-friendly.

Do not implement external live integrations yet.
Do not invent any secrets, URLs, GitHub repository layouts, WordPress credentials, or LLM credentials.
If you discover that human input is already required, stop using the BLOCKED_USER_INPUT format from the PRD.
```

After approving the plan, assign Milestone 1 separately rather than asking Codex to implement the entire PRD in one giant task.

---

# 27. Final constraint to Codex

The success condition is **not** "many features exist."

The success condition is one reliable, observable pipeline:

```text
real coding activity
→ authenticated event
→ durable database record
→ background processing
→ validated AI analysis
→ reproducible blog artifact
→ reviewable WordPress draft
```

Make this path robust before adding anything else.
