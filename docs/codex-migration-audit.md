# Codex Migration Audit

Date: 2026-04-15

## Summary

The repository is a strong fit for Codex. It has:

- Clear architectural boundaries
- Strong repository conventions
- Reusable shared infrastructure
- Product strategy encoded in docs and skills

The main migration gap was not implementation quality. It was agent-context quality:
Claude had a dedicated repository contract in `CLAUDE.md`, while Codex had no
Codex-native entrypoint file.

This is now partially addressed by adding `AGENTS.md`.

## What Works Well For Codex

- Repeatable FastAPI project structure under `projects/`
- High-value shared platform code under `shared/`
- Explicit conventions in `CLAUDE.md`
- Domain-specific guidance in `skills/`
- A repo orientation toward concrete implementation, testing, and deployment

## Migration Gaps Found

### 1. No Codex-native repository guidance file

Impact:
- Future Codex sessions may miss repo-specific context unless they manually read
  `CLAUDE.md`

Action:
- Added `AGENTS.md` to surface the same repo contract in a Codex-native way

### 2. `pdf-from-html` docs drift from current implementation

Current implementation:
- Uses `xhtml2pdf`

Older docs/spec language:
- References Chromium, Playwright, browser pooling, and in one place WeasyPrint

Impact:
- Future implementation work can be steered by stale assumptions
- Product claims may exceed current capabilities

Action:
- Updated the current-facing docs and metadata to describe the existing renderer accurately

### 3. Some planning docs are aspirational, not authoritative

Impact:
- Helpful for roadmap context, but they should not override current code behavior

Recommended operating rule:
- Treat source code and current READMEs as truth for present behavior
- Treat `docs/superpowers/` plans/specs as design intent unless explicitly revived

## Recommended Ongoing Workflow

1. Keep `CLAUDE.md` as the canonical project contract
2. Keep `AGENTS.md` short and aligned with `CLAUDE.md`
3. When implementation changes invalidate project README claims, update those docs in
   the same change
4. When a planned design is intentionally deferred, prefer documenting the chosen
   implementation rather than leaving old aspirational wording in current-facing files

## Remaining Risks

- Older design docs under `docs/superpowers/` still mention Playwright/Chromium for
  `pdf-from-html`
- Marketing-style claims such as "10x cheaper" should be treated as positioning and
  revisited before public-facing publication if pricing changes
