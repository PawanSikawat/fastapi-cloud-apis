from dataclasses import dataclass


@dataclass(frozen=True)
class PlanDefinition:
    name: str
    display_name: str
    requests_per_month: int
    rate_limit_per_minute: int
    price_cents: int
    stripe_price_id: str | None = None


PLANS: dict[str, PlanDefinition] = {
    "free": PlanDefinition(
        name="free",
        display_name="Free",
        requests_per_month=100,
        rate_limit_per_minute=10,
        price_cents=0,
    ),
    "basic": PlanDefinition(
        name="basic",
        display_name="Basic",
        requests_per_month=10_000,
        rate_limit_per_minute=60,
        price_cents=900,
    ),
    "pro": PlanDefinition(
        name="pro",
        display_name="Pro",
        requests_per_month=100_000,
        rate_limit_per_minute=300,
        price_cents=2900,
    ),
    "enterprise": PlanDefinition(
        name="enterprise",
        display_name="Enterprise",
        requests_per_month=1_000_000,
        rate_limit_per_minute=1000,
        price_cents=0,
    ),
}


def get_plan(name: str) -> PlanDefinition:
    return PLANS.get(name, PLANS["free"])
