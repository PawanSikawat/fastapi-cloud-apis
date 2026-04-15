# New API Playbook

This playbook is the fastest path for adding a new API product to this repo
without re-discovering the conventions from scratch.

## Use This With

- [templates/api-starter/README.md](/Users/c-sikawats/Documents/GitHub/Personal/fastapi-cloud-apis/templates/api-starter/README.md)
- [CLAUDE.md](/Users/c-sikawats/Documents/GitHub/Personal/fastapi-cloud-apis/CLAUDE.md)
- Relevant domain notes under `skills/`

## What "Done" Looks Like

A new project should be:

- independently deployable on FastAPI Cloud
- wired into `shared/` for auth, rate limiting, metering, and billing
- testable locally with `uv run pytest`
- documented with a project README
- consistent with the route/service/schema/config patterns used elsewhere

## Default Workflow

1. Choose the API opportunity.
   Use `skills/api-catalog/`, `skills/api-patterns/`, and `skills/api-business/`
   to confirm the shape, pricing posture, and distribution angle.

2. Copy the starter.
   Start from `templates/api-starter/` and copy it into `projects/<project-name>/`.

3. Rename the placeholders.
   Replace:
   - `api-starter` -> your project slug
   - `template_api` -> your Python package name
   - starter copy in titles, descriptions, and README text

4. Define the API surface first.
   Before adding deep implementation, lock down:
   - endpoint paths
   - request/response schemas
   - auth expectations
   - product constraints such as limits, timeouts, and output formats

5. Implement the service layer.
   Keep route handlers thin and put business logic in `services/`.

6. Keep the UI secondary.
   The browser UI should exercise the real API; it should not duplicate the
   business logic.

7. Finish the quality loop.
   Run:

   ```bash
   uv run pytest
   uv run ruff check . --fix
   uv run ruff format .
   uv run mypy <package_name>/
   ```

8. Make it deployment-ready.
   Confirm:
   - `tool.fastapi.entrypoint = "<package_name>.main:app"`
   - root redirects to `/ui/login`
   - `DATABASE_URL` and `REDIS_URL` are consumed without an env prefix
   - `COOKIE_SECRET_KEY` and `ADMIN_API_KEY` expectations are documented

## Starter File Map

The starter gives you the common baseline:

- `pyproject.toml`
- `<package_name>/main.py`
- `<package_name>/config.py`
- `<package_name>/exceptions.py`
- `<package_name>/routes/api.py`
- `<package_name>/routes/ui.py`
- `<package_name>/services/`
- `<package_name>/schemas/`
- `<package_name>/middleware/cookie_auth.py`
- `templates/` for login and a basic dashboard
- `tests/` with app fixtures and smoke tests

## Customization Order

This order tends to create the least churn:

1. `pyproject.toml`
2. `README.md`
3. `config.py`
4. `schemas/`
5. `services/`
6. `routes/api.py`
7. `routes/ui.py`
8. tests

## Common Choices

Use the starter as a baseline, then simplify or extend based on the API type:

- Generator APIs: return files or structured output from one request
- Validation APIs: score/classify input and return structured checks
- Wrapper/proxy APIs: normalize upstream behavior behind stable schemas
- Document processors: expect timeouts, size limits, and error handling to be
  more important than UI polish

## Things Not To Forget

- Update the root `README.md` when a new project is added
- Update `CLAUDE.md` if a new repo-level convention is introduced
- Keep current-facing docs aligned with the shipped implementation
- Treat `shared/` changes as platform changes
