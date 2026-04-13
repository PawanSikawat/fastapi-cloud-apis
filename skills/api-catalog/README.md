# API Catalog

The catalog is the strategic core of this project. It maintains a scored, prioritized list of API opportunities and drives the decision of what to build next.

## How It Works

1. **Identify** an API opportunity (market research, user requests, competitor gaps)
2. **Score** it using the criteria in `evaluation-criteria.md`
3. **Add** it to `catalog.md` in the appropriate tier
4. **Track** it as a GitHub issue with the `API idea` label
5. **Build** from highest score down

## Files

- `evaluation-criteria.md` — scoring methodology (demand, margin, competition, complexity)
- `catalog.md` — the master list of all API opportunities, scored and tiered

## Keeping the Catalog Current

Update `catalog.md` when:
- A new API idea is identified — add with scores to the appropriate tier
- An API ships — move to the "Shipped" section with launch date
- Market conditions change — re-score affected entries
- An API is abandoned — move to "Archived" with reason

## GitHub Issue Convention

Every catalog entry has a corresponding GitHub issue labeled `API idea`. The issue body contains the full evaluation (scores, angle, pattern). The catalog is the summary view; the issue is the detailed view.
