# Personal DevOS — Repository Guide

## Source of truth

`prd_v3.md` is the implementation source of truth. It preserves the product
requirements in `prd_v2.md` and updates the development/deployment order.
Work one milestone at a time and stop for owner confirmation at each
milestone boundary.

## Current project commands

Use the project virtual environment:

```bash
venv/bin/python manage.py check
venv/bin/python manage.py test
venv/bin/python manage.py migrate
venv/bin/python manage.py runserver
```

The current repository uses Django with a custom `accounts.User` model and
PostgreSQL configuration. Early development may use native host services
instead of Docker. The target remains Linux, PostgreSQL, Redis, Celery,
Django templates, and a modular monolith. Docker is introduced and verified
before deployment, not required for every earlier milestone.

## Target application boundaries

```text
config/                  Django settings, URLs, Celery
accounts/                User, native auth, Kakao SocialAccount
activity/                ActivityEvent
coding/                  CodingSubmission and platform parsers
blog/                    Native BlogPost, draft/public rendering
integrations/            GitHub and future external-service adapters
common/                  Small shared utilities only
templates/               Server-rendered UI
tests/                   Cross-domain tests
```

Keep domain logic out of views and avoid circular app dependencies.

## v2 scope

Phase 1 includes native ID/password authentication, Kakao OAuth, account
linking, a native Django blog, GitHub coding-activity ingestion, asynchronous
LLM analysis, and owner review before publication.

Do not implement WordPress, other external publishers, RAG/pgvector, news
crawling, browser/Android/photo collectors, autonomous coding agents,
microservices, React rewrites, or automatic production deployment in Phase 1.

## Human checkpoints

Stop and request owner input before using live Kakao credentials, the real
GitHub repository/webhook, an LLM provider/API key, or deployment secrets.
Never invent credentials, URLs, repository layouts, or production settings.

## Security

- Never commit `.env`, credentials, tokens, cookies, or webhook secrets.
- Use Django password hashing, CSRF protection, and sessions.
- Verify GitHub webhook signatures and make delivery handling idempotent.
- Do not silently merge accounts by email alone.
- Enforce public/private access server-side.
- Treat AI output as reviewable generated content, not source-of-truth data.
- Preserve source code verbatim and never republish full problem statements.

## Before finishing a milestone

Run relevant tests and `manage.py check`, confirm the app remains runnable,
document important design choices, and report what changed, how to verify it,
failure cases, and the next milestone. Remove obsolete files only after
checking references and preserving anything that is still needed for migration
or history.
