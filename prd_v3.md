# PRD — Personal DevOS v3

## Versioned implementation policy

This document keeps the product scope, domain model, security rules, human
checkpoints, and acceptance philosophy of `prd_v2.md`. It changes the local
development and deployment order so Docker is deferred until the application
is functionally complete enough to package and deploy.

`prd_v3.md` is the active implementation source of truth. `prd_v2.md` is the
historical v2 baseline. Where this document differs from v2, this document
wins.

The requested filename `PRD_v3.mrd` is treated as a typo; this repository uses
the conventional Markdown filename `prd_v3.md`.

## Product scope retained from v2

Phase 1 still includes native ID/password authentication, Kakao OAuth and
explicit account linking, a native Django blog with owner review, GitHub
coding-activity ingestion, asynchronous LLM analysis, and draft publication.

Do not implement WordPress, other external publishers, RAG/pgvector, news
crawling, browser/Android/photo collectors, autonomous coding agents,
microservices, React rewrites, or automatic production deployment.

All v2 requirements for security, privacy, canonical users, signed GitHub
webhooks, idempotency, source-code preservation, public/private boundaries,
LLM reviewability, and owner checkpoints remain in force.

## Development environment policy

Docker is not a prerequisite for early development. The goal is to reduce
setup friction and complete the product milestones first.

For early milestones use the repository Python virtual environment, native
PostgreSQL on the Linux development machine, and Redis only when Celery work
begins. Use mocks and test fixtures before live Kakao, GitHub, or LLM setup.

PostgreSQL is required from Milestone 1 because it is the target relational
database and migrations/tests must be verified against it. SQLite may be used
only for a temporary non-acceptance smoke check; it is not valid evidence for
Foundation acceptance.

Redis is not required for the authentication and blog milestones. It becomes
required when the Celery milestone begins. A native Redis installation or a
managed Redis-compatible service may be used during development.

## Deployment packaging policy

Before deployment, introduce and verify:

- a production-oriented `Dockerfile`;
- Docker Compose for Django, PostgreSQL, Redis, and Celery worker processes
  where appropriate;
- environment-variable-only secret configuration;
- migration and static-file commands;
- health checks and process start commands;
- deployment documentation.

Docker should be exercised before the final deployment milestone, but it does
not need to be the daily development workflow.

## Revised working procedure

For every milestone:

1. inspect the existing implementation and relevant requirements;
2. implement only that milestone;
3. run `venv/bin/python manage.py check`;
4. run relevant tests against PostgreSQL;
5. document decisions, verification commands, and known failures;
6. stop and request owner confirmation before the next milestone.

Do not use live credentials or production resources before the relevant
human checkpoint.

## Milestones

The product milestones remain in the v2 order, with these clarifications.

### Milestone 0 — Repository inspection only

Inspect the repository, environment, database configuration, migrations,
authentication model, and documentation. Update `AGENTS.md`, report the plan
and blockers, and stop for owner approval.

### Milestone 1 — Foundation

Implement the Django modular-monolith foundation, PostgreSQL configuration,
environment handling, safe custom User, migrations, public/private shells,
tests, and local setup documentation.

Docker is not required. PostgreSQL must be available as a native local
service or an explicitly temporary managed development database.

Acceptance:

- `manage.py check` passes;
- migrations apply successfully;
- tests pass against PostgreSQL;
- the app runs on Linux;
- no secrets are committed.

Stop for owner confirmation.

### Milestone 2 — Native authentication

Implement and test registration, ID/password login, logout, sessions,
private-route protection, and account settings. Stop for owner confirmation
after the authentication suite passes.

### Milestone 3 — Kakao OAuth and account linking

Prepare mocks and architecture first. Stop at Checkpoint A before live Kakao
configuration. Implement social-created accounts, explicit linking, password
addition, unlink safeguards, and tests. Stop for owner confirmation.

### Milestone 4 — Native blog

Implement BlogPost, draft/public states, private draft management, public
rendering, publication action, and tests. No Docker requirement. Stop for
owner confirmation.

### Milestone 5 — Activity and coding domain

Implement ActivityEvent, CodingSubmission, CodeAnalysis schema, private
coding views/admin, and tests. No live GitHub integration. Stop for owner
confirmation.

### Milestone 6 — Celery foundation

Introduce Redis and Celery. Use native Redis or a managed Redis-compatible
service during development. Implement a representative task, ProcessingRun
where useful, failure logging, and tests.

Acceptance requires that a background task can run locally and a Django
request does not wait for slow work. Stop for owner confirmation.

### Milestone 7 — GitHub webhook ingestion

Stop at Checkpoint B before using the real repository, webhook, or secret.
Implement signed delivery handling, idempotency, repository/branch filtering,
repository-specific parsing from supplied examples, changed-solution
detection, enqueueing, and tests. Stop for owner confirmation.

### Milestone 8 — LLM analysis

Prepare the provider abstraction and mocks first. Stop at Checkpoint C before
using a live provider or API key. Implement structured validation,
persistence, retry/failure behavior, metadata, and tests. Stop for owner
confirmation.

### Milestone 9 — Automated blog draft

Connect `CodingSubmission → CodeAnalysis → BlogPost(draft)`. Ensure source
code remains verbatim, problem statements are not copied, and retries are
idempotent. Test owner editing and publication boundaries. Stop for owner
confirmation.

### Milestone 10 — Dashboard and hardening

Implement recent activity, pending drafts, failed jobs, integration state,
error UX, security review, full tests, and architecture/data-flow
documentation.

At this milestone create and validate the deployment Dockerfile and Compose
configuration without changing the daily development workflow. Verify the
containerized app with PostgreSQL, Redis, and Celery in a disposable local
environment when possible. Stop for owner confirmation.

### Milestone 11 — Deployment plan and deployment

Stop at Checkpoint D before deployment secrets or production configuration.
Produce the deployment topology, environment variables, PostgreSQL and Redis
strategy, Celery process strategy, static-file strategy, HTTPS plan, backup
plan, and rough cost.

After owner approval, deploy the verified Docker-based package to the chosen
host. Do not treat a free host as durable production storage without
explicitly accepting its persistence, sleep, backup, and expiration limits.

## Phase 1 definition of done

The v2 end-to-end story remains unchanged:

1. coding activity enters through a signed GitHub webhook;
2. Django records the delivery and normalizes the submission;
3. background processing stores ActivityEvent and CodingSubmission;
4. asynchronous analysis stores CodeAnalysis;
5. a reviewable BlogPost draft is generated;
6. the owner edits and publishes it;
7. the public blog shows only published/public posts;
8. native and Kakao authentication resolve to one canonical User;
9. private data cannot be accessed through public routes.

Deployment is complete only after the Docker-based package is verified on the
chosen host and the owner has reviewed the operational limitations.
