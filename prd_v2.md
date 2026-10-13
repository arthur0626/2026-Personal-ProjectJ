# PRD --- Personal DevOS v2

## Coding Activity → AI Analysis → Native Django Blog

**Document status:** v2.0\
**Primary implementation agent:** Codex\
**Primary human owner:** Project owner\
**Target environment:** Linux\
**Primary stack:** Python, Django, PostgreSQL, Redis, Celery\
**Scope:** Phase 1 foundation + coding-submission automation + native
Django blog + complete baseline authentication architecture.\
**Future direction:** Public portfolio, daily intelligence, personal
knowledge/RAG, controlled coding agents, personal archive.

------------------------------------------------------------------------

# 0. Instructions to Codex --- READ FIRST

## 0.1 Source of truth

Treat this PRD as the source of truth unless an explicit later
instruction from the human owner overrides it.

Before implementing anything:

1.  Inspect the repository and current Linux development environment.
2.  Read all existing documentation and configuration.
3.  Summarize the current architecture and repository structure.
4.  Identify conflicts between the existing project and this PRD.
5.  Propose a milestone-by-milestone implementation plan.
6.  Create or update `AGENTS.md` with concise repository-specific
    instructions.
7.  **Do not begin implementation until Milestone 0 has been reported to
    the owner.**
8.  After approval, implement only the requested milestone.
9.  Run relevant tests after every milestone.
10. Keep the application runnable after every milestone.

Do not silently invent: - OAuth credentials; - Kakao application
settings; - production domains; - GitHub repository structure; - GitHub
webhook secrets; - LLM provider/API keys; - deployment infrastructure; -
owner identity; - publication policy.

## 0.2 Mandatory stop-and-ask protocol

When implementation reaches information that only the human owner can
supply, stop and output:

``` text
BLOCKED_USER_INPUT

Why I am blocked:
...

Please provide:
1. ...
2. ...

What is already complete:
...

What I will do after you answer:
...
```

Do not work around the checkpoint with fake production values.

Mock values are allowed **only in automated tests**.

## 0.3 Required human checkpoints

Codex MUST stop before live configuration of:

### CHECKPOINT A --- Kakao OAuth

Request: - Kakao REST API key/client ID as required by the chosen
integration; - registered redirect URI; - any required client secret; -
confirmation of local callback URL; - confirmation of production
callback URL only when deployment begins.

Before this checkpoint, OAuth behavior must be developed/tested with
mocks where practical.

### CHECKPOINT B --- GitHub ingestion

Request: - actual coding-solutions repository; - representative
directory/file examples produced by BaekjoonHub or the owner's current
uploader; - which branches should be processed; - webhook secret or
instructions for the owner to create one; - public callback URL only
when live webhook testing begins.

**Never guess BaekjoonHub's repository layout.**

### CHECKPOINT C --- LLM

Request: - desired provider; - model; - API key; - optional budget/cost
preference.

The LLM integration must be abstracted so a provider can be replaced
later.

### CHECKPOINT D --- Deployment

Request: - deployment target; - domain/subdomain preference; -
HTTPS/reverse proxy preference if relevant; - production secrets.

Do not deploy automatically.

## 0.4 Security rules

-   Never commit `.env`.
-   Never commit passwords, OAuth secrets, access tokens, refresh
    tokens, API keys, webhook secrets, cookies, or session values.
-   Provide `.env.example` with variable names only.
-   Never log full credentials/tokens.
-   Use Django's password hashing; never implement custom password
    cryptography.
-   Use Django's CSRF/session security features.
-   Verify GitHub webhook signatures.
-   Prevent duplicate webhook processing.
-   Do not automatically link accounts merely because email strings
    match.
-   Require proof of control of the existing account before linking a
    new social identity to it.
-   Do not allow removal of the user's last usable authentication
    method.
-   Public/private access must be enforced server-side, not merely
    hidden in templates.
-   AI-generated technical claims are untrusted until reviewed.
-   Never republish full copyrighted coding-problem statements.
-   Never allow an AI coding agent to modify production/main directly in
    this phase.

------------------------------------------------------------------------

# 1. Product identity

## 1.1 Working name

**Personal DevOS**

## 1.2 Phase 1 value proposition

> Turn daily coding-test activity into structured personal knowledge and
> a reviewable public proof-of-work automatically.

## 1.3 Long-term value proposition

> Capture personal developer activity, turn it into knowledge and
> actions, and selectively compile it into public career evidence.

Long-term conceptual flow:

``` text
Activity
   ↓
Knowledge
   ↓
Action
   ↓
Public Evidence
```

Phase 1 implements the first complete vertical slice of this concept.

------------------------------------------------------------------------

# 2. Major v2 changes from v1

v2 intentionally changes two major architectural decisions.

## 2.1 WordPress removed from the core

Do NOT implement WordPress in Phase 1.

The application itself is the blog platform.

Old:

``` text
Django → AI → WordPress API → WordPress
```

New:

``` text
Django → AI → BlogPost(draft) → Owner Review → BlogPost(published)
```

Reasons: - removes unnecessary external dependency; - eliminates
WordPress hosting/API/authentication requirements; - keeps public
portfolio/blog and private Personal DevOS in one product; - allows the
owner to design the complete publishing workflow; - still leaves room
for external publishers later.

Future external publication should be an optional adapter:

``` text
BlogPost
   ├─ NativeDjangoPublisher
   ├─ WordPressPublisher      [future]
   ├─ MediumPublisher         [future]
   └─ OtherPublisher          [future]
```

Do not implement those future publishers now.

## 2.2 Authentication expanded

Phase 1 must support a proper account foundation:

1.  native ID/password authentication;
2.  Kakao OAuth login;
3.  linking Kakao to an existing native account;
4.  adding a password login method to an account originally created
    through Kakao;
5.  unlinking a social account when another authentication method
    remains;
6.  one canonical Django user regardless of authentication method;
7.  Django session-based logged-in state;
8.  server-side authorization for private resources.

GitHub OAuth login is NOT required in Phase 1.

GitHub is initially an **activity integration**, not an identity
provider.

------------------------------------------------------------------------

# 3. System overview

``` text
                         ┌────────────────────────────┐
                         │       PUBLIC WEB           │
                         │  Blog / Portfolio shell    │
                         └─────────────▲──────────────┘
                                       │
                                  published data
                                       │
┌─────────────┐                 ┌──────┴─────────┐
│ ID/Password │────────────────►│                │
└─────────────┘                 │     Django     │
                                │ Personal DevOS │
┌─────────────┐   OAuth         │                │
│    Kakao    │────────────────►│                │
└─────────────┘                 └──────┬─────────┘
                                       │
                        ┌──────────────┼──────────────┐
                        ▼              ▼              ▼
                   PostgreSQL        Redis        Django UI
                                         │
                                         ▼
                                      Celery
                                         │
                                         ▼
                                      LLM API

Programmers / SWEA
        │
        ▼
BaekjoonHub / current uploader
        │
        ▼
      GitHub
        │ signed push webhook
        ▼
      Django
        │
        ▼
  ActivityEvent
        │
        ▼
 CodingSubmission
        │
        ▼
    Celery task
        │
        ▼
    CodeAnalysis
        │
        ▼
 BlogPost(draft)
        │
        ▼
  Human review
        │
        ▼
 BlogPost(published)
```

------------------------------------------------------------------------

# 4. Technology decisions

## 4.1 Linux

Continue development on Linux.

Linux is not used merely as a portfolio label. The project should
gradually expose the owner to: - processes; - environment variables; -
ports; - file permissions; - logs; - services; - Docker; - networking; -
SSH and deployment later.

Do not introduce complexity solely to demonstrate Linux knowledge.

## 4.2 Django

Use Django as a modular monolith.

Do NOT split into microservices.

Suggested Django apps:

``` text
apps/
    accounts/
    activity/
    coding/
    blog/
    integrations/
    common/
```

Future apps may include:

``` text
briefing/
knowledge/
agents/
archive/
portfolio/
```

Do not implement future apps now unless a tiny shared interface is
explicitly required.

## 4.3 PostgreSQL

Use PostgreSQL as the primary relational database.

Reasons: - production-grade relational DB; - strong Django support; -
robust JSON capabilities; - suitable for future event/metadata-heavy
features; - future `pgvector` option for semantic search/RAG; - avoids
introducing a separate vector database early.

Do NOT add pgvector in Phase 1.

## 4.4 Redis + Celery

Use Redis as the Celery broker.

Use Celery for slow/retriable work such as: - fetching or resolving
code/metadata after webhook receipt; - LLM calls; - blog draft
generation; - later scheduled briefing tasks.

The GitHub webhook HTTP request must not wait for an LLM call.

Do not use Celery where a simple synchronous DB operation is sufficient.

## 4.5 Templates first

Use Django templates for the Phase 1 UI unless the repository already
has a justified frontend architecture.

Do NOT introduce React merely for portfolio appearance.

The architecture may expose APIs later for mobile/other clients.

------------------------------------------------------------------------

# 5. Core domain model

## 5.1 User

There must be one canonical user identity.

Prefer a custom Django user model based on `AbstractUser` from the
beginning unless the repository is already migrated in a way that makes
this unsafe.

Example conceptual fields:

``` text
User
- id
- username
- email
- password (Django-managed hash)
- is_active
- is_staff
- is_superuser
- created_at / date_joined
```

Do not store plaintext passwords.

## 5.2 SocialAccount

A social identity is NOT a separate user.

``` text
User 1 ─────── N SocialAccount
```

Conceptual model:

``` text
SocialAccount
- id
- user_id
- provider
- provider_user_id
- display_name [optional]
- metadata [minimal JSON, optional]
- created_at
- updated_at
```

Constraints: - `(provider, provider_user_id)` must be unique. - One
social identity cannot belong to two users. - Do not store unnecessary
provider profile data. - Do not store long-lived OAuth tokens unless a
later feature actually requires provider API access. - Login-only Kakao
OAuth should request the minimum scopes needed.

Phase 1 provider: - `kakao`

Future providers may be added without changing the User table.

## 5.3 ActivityEvent

`ActivityEvent` is a Django model / database table representing the
common fact:

> "A meaningful user activity happened at a particular time."

It is NOT a function and NOT a Python built-in.

Conceptual fields:

``` text
ActivityEvent
- id
- user_id
- event_type
- source
- occurred_at
- visibility
- processing_status
- metadata (small JSON only when useful)
- created_at
- updated_at
```

Phase 1 example:

``` text
event_type = "coding_submission"
source = "github"
```

Future examples:

``` text
article_read
project_commit
agent_run
browser_activity
knowledge_created
```

Do not put all domain-specific fields into `ActivityEvent`.

Detailed coding data belongs in `CodingSubmission`.

## 5.4 CodingSubmission

Conceptual fields:

``` text
CodingSubmission
- id
- user_id
- activity_event_id
- platform
- problem_external_id [nullable]
- problem_title
- problem_url [nullable]
- language
- source_code
- repository
- branch
- commit_sha
- file_path
- submitted_at / occurred_at
- ingestion_status
- created_at
- updated_at
```

Important: - preserve the owner's source code verbatim; - do not let the
LLM rewrite the canonical source; - prevent duplicate ingestion with
appropriate uniqueness constraints; - parser behavior must be based on
real repository examples supplied at CHECKPOINT B.

## 5.5 CodeAnalysis

Conceptual fields:

``` text
CodeAnalysis
- id
- submission_id
- status
- summary
- approach
- time_complexity
- space_complexity
- key_concepts
- strengths
- possible_improvements
- pitfalls
- raw_structured_output
- model_provider
- model_name
- prompt_version
- created_at
- updated_at
```

AI output is analysis, not truth.

The UI must make it clear that generated analysis is reviewable.

## 5.6 BlogPost

The native Django blog is the canonical publication system.

Conceptual fields:

``` text
BlogPost
- id
- author_id
- source_submission_id [nullable]
- source_analysis_id [nullable]
- title
- slug
- excerpt
- body
- status
- visibility
- created_at
- updated_at
- published_at [nullable]
```

Status should support at minimum:

``` text
draft
published
```

Possible future states may include archived/scheduled, but do not
overbuild them now.

Rules: - AI-generated coding posts default to `draft`. - Publication
requires explicit owner action in Phase 1. - `published_at` is set only
on publication. - public routes must return only published/public
posts. - drafts must never leak through public templates, APIs, feeds,
or search.

## 5.7 BlogCategory / BlogTag

Keep taxonomy simple.

Implement tags only if they are genuinely useful for coding posts.

Possible tags: - programmers - swea - python - graph -
dynamic-programming

Avoid a complex CMS taxonomy system.

## 5.8 Integration

Create a minimal integration concept so future external services can be
added cleanly.

Conceptual fields:

``` text
Integration
- id
- user_id
- provider
- status
- display_name
- configuration_metadata [non-secret only]
- created_at
- updated_at
```

Examples: - github - kakao_identity (optional if useful) - future news
provider - future Android collector

Secrets must NOT be stored casually in `configuration_metadata`.

Environment variables are acceptable for single-owner Phase 1 secrets.

## 5.9 WebhookDelivery

Track GitHub deliveries.

``` text
WebhookDelivery
- id
- provider
- delivery_id
- event_name
- received_at
- processing_status
- error_summary
```

`(provider, delivery_id)` must be unique.

This supports idempotency.

## 5.10 BackgroundJob / ProcessingRun

Track important asynchronous processing.

Conceptual fields:

``` text
ProcessingRun
- id
- user_id
- run_type
- related_object_type
- related_object_id
- status
- attempts
- started_at
- finished_at
- error_summary
- metadata
```

Do not attempt to replace Celery's internals. This model exists for
product-level visibility and auditability.

------------------------------------------------------------------------

# 6. Authentication requirements

## 6.1 Native registration

Provide native registration with: - username; - password; - password
confirmation; - optional/required email according to the simplest
consistent product policy.

Use Django forms/validation and Django password hashing.

Do not invent custom password hashing.

## 6.2 Native login

Flow:

``` text
username + password
       ↓
Django authenticate()
       ↓
canonical User
       ↓
Django login()
       ↓
Session
```

## 6.3 Kakao social login

Flow:

``` text
Kakao OAuth
    ↓
provider identity verified
    ↓
find SocialAccount(provider="kakao", provider_user_id=...)
    ↓
canonical User
    ↓
Django Session
```

If no SocialAccount exists, present a deliberate account decision:

``` text
[Create a new account using Kakao]
or
[Link to an existing account]
```

Do not silently merge based only on matching email.

## 6.4 Link Kakao to existing account

The user must already control/authenticate the existing account.

Example:

``` text
Logged-in User
    ↓
Settings → Connected Accounts
    ↓
Connect Kakao
    ↓
Kakao OAuth
    ↓
ensure Kakao identity is not linked elsewhere
    ↓
create SocialAccount(user=current_user)
```

## 6.5 Existing-account linking from social-login flow

If a social identity has no linked User but the person claims an
existing account:

``` text
Kakao OAuth succeeds
    ↓
"Link to existing account"
    ↓
Require existing account authentication
    ↓
If successful, create SocialAccount
```

Never treat an email match alone as sufficient proof.

## 6.6 Add password to social-created account

A user created through Kakao may later add a native password.

Require an authenticated session and an appropriate confirmation flow.

Use `set_password()`.

## 6.7 Unlink social account

Allow unlinking only if at least one other usable authentication method
remains.

Examples:

``` text
Password ✓ + Kakao ✓ → Kakao may be removed
Password ✗ + Kakao ✓ → Kakao removal blocked
Password ✗ + Kakao ✓ + future GitHub ✓ → one may be removed
```

## 6.8 Session

After successful authentication, all login methods converge on Django's
session system.

Do not re-run Kakao OAuth on every private page request.

## 6.9 Authorization

Authentication answers:

> Who is this user?

Authorization answers:

> Which resources/actions may this user access?

Private views must use server-side authorization.

All personal domain models should be designed with `user` ownership so
future multi-user expansion is possible.

Phase 1 may primarily be used by the project owner, but do not hard-code
all records globally to one person.

## 6.10 Owner/admin privileges

Use Django's built-in staff/superuser/permissions where practical.

Do not invent an elaborate role engine for Phase 1.

The initial owner can be created as the administrative account.

------------------------------------------------------------------------

# 7. Public/private boundary

## 7.1 Public routes

At minimum:

``` text
/
 /blog/
 /blog/<slug>/
 /about/           [simple placeholder allowed]
 /portfolio/       [minimal shell/placeholder allowed]
```

The public portfolio itself is a later phase; do not build a large
portfolio CMS now.

## 7.2 Private routes

Examples:

``` text
/dashboard/
 /activities/
 /coding/submissions/
 /coding/submissions/<id>/
 /blog/drafts/
 /settings/account/
 /settings/connections/
 /settings/integrations/
```

## 7.3 Publication boundary

Public blog queries must explicitly filter:

``` text
status = published
visibility = public
```

Never rely on template hiding alone.

------------------------------------------------------------------------

# 8. GitHub ingestion

## 8.1 Purpose

GitHub acts as an activity source.

Phase 1 target:

``` text
Programmers / SWEA
      ↓
BaekjoonHub or current sync mechanism
      ↓
GitHub push
      ↓
signed webhook
      ↓
Django
```

## 8.2 Webhook endpoint

Create a dedicated endpoint such as:

``` text
POST /webhooks/github/
```

Exact URL naming may follow repository conventions.

## 8.3 Webhook behavior

The HTTP handler should:

1.  read raw request body;
2.  verify GitHub signature;
3.  obtain delivery ID;
4.  reject/ignore duplicate deliveries safely;
5.  identify event type;
6.  validate repository/branch policy;
7.  persist minimal receipt state;
8.  enqueue background processing;
9.  return quickly.

Do NOT call the LLM inside the webhook request.

## 8.4 Repository parser

Do not implement assumptions before CHECKPOINT B.

After receiving real examples, build a parser/adapter:

``` text
GitHub/BaekjoonHub-specific structure
             ↓
NormalizedSubmissionCandidate
             ↓
CodingSubmission
```

This isolates repository-format changes from the core domain.

## 8.5 Copyright/content rule

Do not scrape or republish full coding problem statements.

A generated post may contain: - problem title; - source link; - owner's
own summary; - owner's source code; - AI-generated explanation based on
allowed inputs; - complexity analysis; - retrospective.

------------------------------------------------------------------------

# 9. Background processing

## 9.1 Pipeline

Target flow:

``` text
Webhook accepted
    ↓
Celery job
    ↓
Resolve changed coding files
    ↓
Normalize metadata
    ↓
ActivityEvent
    ↓
CodingSubmission
    ↓
LLM analysis task
    ↓
CodeAnalysis
    ↓
Blog draft generation
    ↓
BlogPost(status="draft")
```

## 9.2 Failure behavior

External failures must not corrupt canonical submission data.

Example: - CodingSubmission stored successfully; - LLM unavailable; -
CodeAnalysis marked failed/pending; - owner can retry analysis later.

## 9.3 Retry policy

Use bounded retries with sensible backoff for transient external
failures.

Do not infinitely retry: - invalid credentials; - invalid input; -
permanent 4xx responses; - malformed structured output after a
reasonable limit.

## 9.4 Idempotency

Repeated webhook delivery or task retry must not create: - duplicate
CodingSubmission; - duplicate ActivityEvent for the same normalized
submission; - duplicate BlogPost for the same generation attempt unless
intentionally regenerated.

Use database uniqueness and application-level idempotency together.

------------------------------------------------------------------------

# 10. LLM integration

## 10.1 Provider abstraction

Do not scatter direct provider SDK calls throughout views/tasks.

Create an interface/service boundary such as:

``` text
LLMClient
    analyze_code(...)
    generate_blog_draft(...)
```

Concrete provider implementation is selected through configuration.

## 10.2 Structured output

Prefer validated structured output for analysis.

Conceptual schema:

``` json
{
  "summary": "...",
  "approach": "...",
  "time_complexity": "...",
  "space_complexity": "...",
  "key_concepts": ["..."],
  "strengths": ["..."],
  "possible_improvements": ["..."],
  "pitfalls": ["..."]
}
```

Validate before persistence.

## 10.3 Prompt safety

Treat repository content as untrusted input.

Do not allow source comments/readme text to override system/developer
instructions.

Do not give the LLM secrets.

## 10.4 Cost tracking

Record enough metadata to later understand: - provider; - model; -
feature; - latency; - token usage if available; - estimated/actual cost
if readily available.

Do not build a complex billing system.

------------------------------------------------------------------------

# 11. Native blog

## 11.1 Draft generation

A coding BlogPost should be generated from trusted structured data:

``` text
problem metadata
+
verbatim owner source code
+
validated CodeAnalysis
+
template/prompt
```

## 11.2 Suggested coding-post structure

1.  Problem/source link
2.  Short problem summary written in original words
3.  Approach
4.  Source code
5.  Complexity
6.  Key concepts
7.  What went well
8.  Possible improvements / mistakes
9.  Personal note

Do not reproduce full problem statements.

## 11.3 Owner review

Draft detail page should allow the owner to: - inspect source
submission; - inspect AI analysis; - edit title/body/excerpt/tags; -
publish; - return to draft; - regenerate AI draft deliberately.

Regeneration must not silently overwrite human edits.

Prefer version-safe behavior: - confirmation before overwrite; or -
generate a new candidate/version.

Choose the simplest maintainable approach and document it.

## 11.4 Public rendering

Public blog should provide: - list page; - detail page; - readable code
blocks; - publication date; - tags/platform when useful; - basic SEO
metadata where simple.

Do not spend Phase 1 building an elaborate design system.

------------------------------------------------------------------------

# 12. Dashboard

Create a functional private dashboard.

Useful cards: - recent activities; - recent coding submissions; -
analyses pending/failed; - blog drafts awaiting review; - latest
processing failures; - integration status.

The dashboard exists to make automation observable.

Avoid vanity charts unless they communicate useful state.

------------------------------------------------------------------------

# 13. Django Admin

Register core models in Django Admin for debugging/operations.

At minimum: - User; - SocialAccount; - ActivityEvent; -
CodingSubmission; - CodeAnalysis; - BlogPost; - Integration; -
WebhookDelivery; - ProcessingRun.

Admin is an operational tool, not the public product UI.

------------------------------------------------------------------------

# 14. Testing requirements

## 14.1 Authentication

Test: - native registration; - native login success/failure; - logout; -
private route protection; - mocked Kakao login for known social
identity; - new Kakao account flow; - linking Kakao to existing
authenticated User; - refusal to link social identity already linked
elsewhere; - no automatic merge based only on email; - add password to
social-created account; - block removal of final login method; - allow
removal when another method remains.

## 14.2 Blog

Test: - draft is not public; - published public post is visible; -
another user's/private data cannot be accessed through guessed IDs if
multi-user test fixtures are present; - publication sets expected
state/time; - slug uniqueness.

## 14.3 GitHub

Test: - valid signature accepted; - invalid signature rejected; -
duplicate delivery handled idempotently; - irrelevant event safely
ignored; - configured repository/branch rules respected; - parser
fixture based on actual supplied repository examples.

## 14.4 Pipeline

Mock external services.

Test:

``` text
webhook
→ queued processing
→ ActivityEvent
→ CodingSubmission
→ CodeAnalysis
→ BlogPost(draft)
```

Do not spend real LLM money during normal automated tests.

## 14.5 Failure paths

Test at least: - LLM timeout; - malformed LLM response; - task retry; -
missing/unsupported code file; - duplicate submission; - DB constraint
behavior.

------------------------------------------------------------------------

# 15. Observability

Use structured, useful logs.

Logs should make it possible to answer: - which webhook arrived; - which
processing run started; - which submission was created; - whether LLM
analysis succeeded; - whether a draft was generated; - why a run failed.

Never log secrets.

Expose important product-level status in the private dashboard.

------------------------------------------------------------------------

# 16. Local development environment

Target Linux development.

Provide clear commands in README.

Recommended local services:

``` text
Django
PostgreSQL
Redis
Celery Worker
```

Docker Compose may be used for PostgreSQL/Redis and later the full
stack.

Do not containerize everything merely for appearance if it makes early
debugging harder.

A reasonable staged approach is: 1. Django in local Python venv; 2.
PostgreSQL + Redis through Docker Compose; 3. Celery from the same venv;
4. containerize more later if useful.

Codex should inspect the existing environment before choosing.

------------------------------------------------------------------------

# 17. Environment variables

Provide `.env.example`.

Likely variables include:

``` text
DJANGO_SECRET_KEY=
DJANGO_DEBUG=
DJANGO_ALLOWED_HOSTS=

DATABASE_URL=
REDIS_URL=

KAKAO_CLIENT_ID=
KAKAO_CLIENT_SECRET=
KAKAO_REDIRECT_URI=

GITHUB_WEBHOOK_SECRET=
GITHUB_TARGET_REPOSITORY=
GITHUB_TARGET_BRANCH=

LLM_PROVIDER=
LLM_MODEL=
LLM_API_KEY=
```

Exact names may be adjusted to project conventions.

Never commit `.env`.

------------------------------------------------------------------------

# 18. Suggested repository structure

Adapt to the existing repository rather than forcing this exact tree.

``` text
personal-devos/
├── manage.py
├── config/
│   ├── settings/
│   ├── urls.py
│   ├── celery.py
│   └── ...
├── apps/
│   ├── accounts/
│   ├── activity/
│   ├── coding/
│   ├── blog/
│   ├── integrations/
│   └── common/
├── templates/
├── static/
├── tests/
├── docker/
├── .env.example
├── .gitignore
├── AGENTS.md
├── README.md
└── prd.md
```

A simpler structure is acceptable if cleaner for the actual repository.

------------------------------------------------------------------------

# 19. Architectural boundaries

## accounts

Owns: - User; - native auth; - SocialAccount; - account
linking/unlinking; - security/account settings.

## activity

Owns: - ActivityEvent; - generic activity timeline/querying.

## coding

Owns: - CodingSubmission; - CodeAnalysis; - coding-specific workflows.

## blog

Owns: - BlogPost; - publication state; - public blog rendering; - draft
review/editing.

## integrations

Owns: - GitHub webhook adapter; - Kakao provider adapter if not
delegated cleanly to an auth library; - LLM provider adapter; -
integration status/config abstraction.

Avoid circular imports and business logic in templates.

Keep views thin where practical.

------------------------------------------------------------------------

# 20. What NOT to build in v2 Phase 1

Do not implement: - WordPress; - Naver Blog publishing; - Medium
publishing; - GitHub OAuth login; - Google OAuth login; - Naver OAuth
login; - passkeys/WebAuthn; - TOTP/2FA; - custom cryptography; -
password reset complexity beyond what is naturally available/required
for baseline auth; - email infrastructure unless necessary for an
explicitly chosen flow; - RAG; - pgvector; - embeddings; - vector DB; -
news crawler; - browser history; - Android collector; - photo backup; -
autonomous coding agent; - multi-agent system; - Kubernetes; - Kafka; -
microservices; - GraphQL; - React rewrite; - elaborate analytics; -
automatic production deployment.

------------------------------------------------------------------------

# 21. Future expansion contract

Phase 1 should leave clean extension points, not implement future
features.

## Phase 2 --- Public portfolio/interests

Potential additions: - Project; - PublicArtifact; - Interest; -
portfolio pages; - selective publication from private activity.

## Phase 3 --- Daily Intelligence

Potential flow:

``` text
RSS / APIs
    ↓
scheduled Celery tasks
    ↓
Article
    ↓
ranking / deduplication
    ↓
DailyBrief
```

Reuse: - User; - ActivityEvent; - ProcessingRun; - LLM abstraction.

## Phase 4 --- Personal Knowledge / RAG

Potential additions: - KnowledgeItem; - Chunk; - embedding; -
PostgreSQL + pgvector.

Do not add vector infrastructure until natural-language retrieval is
actually needed.

## Phase 5 --- Controlled Coding Agent

Potential flow:

``` text
AgentRun
    ↓
isolated git worktree/container
    ↓
coding agent
    ↓
tests/static checks
    ↓
diff/risk summary
    ↓
PR
    ↓
human approval
```

Never let the future agent directly write to production/main by default.

## Phase 6 --- Personal Archive

Potential connectors: - Chrome extension; - Android companion; -
photos/files; - device/activity metadata.

Store large binary files in object storage, not PostgreSQL BLOBs.

Preserve exportability:

> My data must outlive my service.

------------------------------------------------------------------------

# 22. Milestones

Codex must work milestone-by-milestone.

## Milestone 0 --- Repository inspection only

**Do not implement product features.**

Tasks: 1. inspect repository; 2. inspect Python/Django versions; 3.
inspect current DB/config; 4. inspect Linux development setup; 5.
identify existing migrations/auth model; 6. identify whether changing to
a custom User is safe; 7. propose concrete implementation plan; 8.
create/update concise `AGENTS.md`; 9. report blockers.

STOP and wait for owner approval.

## Milestone 1 --- Foundation

Implement: - Django project/app structure as needed; - PostgreSQL
configuration; - base settings/environment handling; - custom User if
safe/appropriate; - migrations; - minimal public/private shells; -
tests; - README local setup.

Acceptance: - app runs on Linux; - PostgreSQL is used; - tests pass; -
no secrets committed.

STOP.

## Milestone 2 --- Native authentication

Implement: - registration; - ID/password login; - logout; - session; -
private route protection; - account settings shell; - tests.

Acceptance: - user can register/login/logout; - password is
Django-managed; - private dashboard cannot be accessed anonymously.

STOP.

## Milestone 3 --- Kakao OAuth + account linking

First prepare architecture/mocks.

Then hit CHECKPOINT A before live Kakao credentials/configuration are
needed.

Implement: - Kakao login; - SocialAccount; - social-created account; -
link to existing account; - connect from logged-in settings; - add
password to social-created account; - unlink safeguards; - tests.

Acceptance: - native and Kakao login can reach the same canonical
User; - duplicate social identity cannot attach to multiple users; -
email alone never causes silent merge; - last login method cannot be
removed.

STOP.

## Milestone 4 --- Native blog

Implement: - BlogPost; - draft/published state; - private draft
management; - public list/detail; - publication action; - safe public
query boundary; - code-friendly rendering; - tests.

Acceptance: - drafts are private; - published posts are public; - owner
can edit/publish a draft.

STOP.

## Milestone 5 --- Activity + coding domain

Implement: - ActivityEvent; - CodingSubmission; - CodeAnalysis schema; -
basic private coding views/admin; - tests.

No live GitHub yet.

Acceptance: - manually created coding submission can be represented by
an ActivityEvent; - activity timeline works; - domain boundaries are
documented.

STOP.

## Milestone 6 --- Celery foundation

Implement: - Redis/Celery configuration; - worker; - sample/real
internal task; - ProcessingRun where useful; - failure logging; - tests.

Acceptance: - background task can run locally; - Django request does not
need to wait for slow work.

STOP.

## Milestone 7 --- GitHub webhook ingestion

Before parser/live configuration, hit CHECKPOINT B.

Implement: - signed webhook endpoint; - delivery idempotency; -
repository/branch filtering; - repository-specific adapter based on real
examples; - changed solution detection; - enqueue pipeline; - tests.

Acceptance: - representative Programmers/SWEA push produces normalized
coding submission; - duplicate webhook does not duplicate data; -
invalid signature rejected.

STOP.

## Milestone 8 --- LLM analysis

Prepare abstraction first.

Hit CHECKPOINT C before live provider credentials.

Implement: - LLM client abstraction; - structured analysis
schema/validation; - Celery analysis task; - CodeAnalysis persistence; -
retry/failure handling; - cost/latency metadata where available; - tests
using mocks.

Acceptance: - submission can produce validated CodeAnalysis; - failed
analysis does not destroy submission; - retry is possible.

STOP.

## Milestone 9 --- Automated blog draft

Implement:

``` text
CodingSubmission
    ↓
CodeAnalysis
    ↓
BlogPost(draft)
```

Acceptance: - successful coding pipeline generates exactly one intended
draft; - owner source code remains verbatim; - full problem statement is
not copied; - owner can edit before publishing; - retry does not create
uncontrolled duplicates.

STOP.

## Milestone 10 --- Dashboard + hardening

Implement/refine: - recent activity; - pending drafts; - failed jobs; -
integration state; - basic error UX; - security review; - full test
suite; - README architecture/data-flow documentation.

Acceptance: - owner can understand system state without reading DB
tables; - all tests pass; - no known secret leakage; - public/private
boundary verified.

STOP.

## Milestone 11 --- Deployment plan only

Do not deploy until CHECKPOINT D.

Produce: - recommended production topology; - environment variables; -
PostgreSQL/Redis strategy; - Celery process strategy; - static files
strategy; - reverse proxy/HTTPS plan; - backup plan; - rough expected
cost.

Wait for owner decision.

------------------------------------------------------------------------

# 23. Definition of Done for Phase 1

Phase 1 is complete when the following user story works reliably:

``` text
1. Owner solves a Programmers or SWEA problem.
2. Existing uploader/BaekjoonHub pushes the solution to GitHub.
3. GitHub sends a signed webhook.
4. Django validates and records the delivery.
5. Background processing identifies the solution.
6. ActivityEvent is created.
7. CodingSubmission is stored in PostgreSQL.
8. LLM analyzes the solution asynchronously.
9. CodeAnalysis is stored.
10. A native Django BlogPost draft is generated.
11. Owner sees the draft in the private dashboard.
12. Owner reviews/edits it.
13. Owner publishes it.
14. The post becomes visible on the public Django blog.
```

Additionally:

``` text
15. User can log in using native ID/password.
16. User can use Kakao OAuth.
17. Kakao can be linked to an existing native account.
18. Both methods resolve to the same canonical User.
19. User cannot accidentally remove the final login method.
20. Private data cannot be viewed from public routes.
```

------------------------------------------------------------------------

# 24. Owner learning goals

Codex should not only implement. At the end of each milestone, report:

``` text
1. What changed?
2. Why was it designed this way?
3. What is the data flow?
4. What can fail?
5. How can the owner manually verify it?
6. Which files are most important?
7. What concepts should the owner understand for an interview?
```

The owner is expected to understand the architecture even if Codex
writes most implementation code.

Concepts the owner should progressively learn: - HTTP
request/response; - API; - webhook; - authentication vs authorization; -
OAuth; - session/cookie; - ORM/model/migration; - PostgreSQL; -
transaction; - idempotency; - Redis; - Celery/background jobs; -
retry; - mock/testing; - environment variables/secrets; - Linux
processes/logs/ports; - Docker; - public/private data boundaries.

------------------------------------------------------------------------

# 25. Acceptance philosophy

Prefer: - boring, understandable technology; - clear domain
boundaries; - tests; - observable failures; - explicit permissions; -
reversible actions; - human review for AI-generated public content.

Avoid: - architecture astronautics; - unnecessary frameworks; -
premature microservices; - premature RAG; - premature multi-agent
systems; - "AI generated it, therefore it must be correct."

------------------------------------------------------------------------

# 26. First prompt to Codex

Use this after placing this file in the repository as `prd.md`:

``` text
Read prd.md completely before making any changes.

Start with Milestone 0 only.

Inspect the current repository and Linux development environment.
Summarize:
1. the current project structure,
2. Django/Python/database configuration,
3. existing authentication and migrations,
4. conflicts with PRD v2,
5. whether introducing the proposed custom User model is safe at this point,
6. your proposed milestone implementation plan.

Create or update a concise AGENTS.md for this repository.

Do not implement Milestone 1 or any product feature yet.
Do not invent external credentials or repository layouts.
Stop after reporting Milestone 0 and wait for my approval.
```

------------------------------------------------------------------------

# 27. Final instruction to Codex

The goal is not to maximize the amount of generated code.

The goal is to create a Personal DevOS foundation that the human owner
can: - understand; - operate; - explain in an interview; - extend over
time; - trust with increasingly personal data.

When a simpler design satisfies the requirements and preserves the
defined extension points, choose the simpler design.
