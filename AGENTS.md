# AGENTS.md

## Purpose

This repository is an API-product monorepo for shipping independent, production-grade
FastAPI services on FastAPI Cloud.

The key operating model is:

- Each API under `projects/` is independently deployable
- Shared commercial/runtime infrastructure lives in `shared/`
- Product strategy and domain heuristics live in `skills/`
- New work should preserve the repeatable "ship another API product" pattern

## Primary References

Read these before making non-trivial changes:

1. `CLAUDE.md` — the main project contract, coding conventions, deployment rules,
   and workspace patterns
2. `README.md` — current repo overview and project inventory
3. Relevant files under `skills/` — product, infra, marketplace, and FastAPI Cloud guidance

`CLAUDE.md` remains the canonical repository guidance file. This `AGENTS.md` exists so
Codex-native workflows pick up the same context reliably.

## What This Repo Is For

This is not a generic FastAPI playground. It is a factory for API businesses:

- Build narrowly scoped APIs with a clear monetizable use case
- Reuse shared auth, billing, rate limiting, metering, and channel routing
- Deploy each API as its own FastAPI Cloud app
- Support both direct usage and marketplace distribution such as RapidAPI

Representative products currently in the repo:

- `projects/qr-code-generator`
- `projects/email-validation`
- `projects/pdf-from-html`

## Non-Negotiable Conventions

- Keep each project self-contained with its own `pyproject.toml`, package, and tests
- Do not import one project from another project
- Put cross-project code in `shared/` only when it is truly reusable infrastructure
- Keep route modules thin; business logic belongs in `services/`
- Use Pydantic v2 schemas for request/response boundaries
- Use strict typing and preserve the repo's Ruff + mypy discipline
- Default to async for I/O paths
- Do not hardcode credentials or deployment secrets

## FastAPI Cloud Rules

- App projects use flat layout, not `src/`
- `tool.fastapi.entrypoint` must point to `<package>.main:app`
- `DATABASE_URL` and `REDIS_URL` are consumed without an env prefix
- `GET /` should redirect to `/ui/login`
- `/health`, docs routes, Stripe webhook, and login/logout routes must remain correctly
  exempted from auth as described in `CLAUDE.md`

## Shared Infrastructure Expectations

`shared/` is the control plane for all APIs. Changes here can affect every project.
Be especially careful with:

- Auth behavior and API key validation
- Rate limiting and quota enforcement
- Usage metering
- Billing and Stripe webhooks
- FastAPI Cloud database/Redis initialization

Treat shared changes as platform changes, not local refactors.

## Skills And Product Context

The `skills/` directory is part of the working system, not just reference material.
Consult relevant skill docs before making product or architecture decisions:

- `skills/api-patterns/`
- `skills/shared-infra/`
- `skills/fastapi-cloud/`
- `skills/marketplace/`
- `skills/api-business/`
- `skills/api-catalog/`

## Migration Note

Some older planning/spec docs describe intended designs that are slightly ahead of the
current implementation. When there is a mismatch, prefer current source code over older
design prose unless the user explicitly asks to restore the planned architecture.
