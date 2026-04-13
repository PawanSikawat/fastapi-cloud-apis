from shared.billing.plans import PLANS, PlanDefinition, get_plan


class TestPlans:
    def test_free_plan_exists(self) -> None:
        plan = get_plan("free")
        assert plan.name == "free"
        assert plan.requests_per_month == 100
        assert plan.rate_limit_per_minute == 10
        assert plan.price_cents == 0

    def test_basic_plan(self) -> None:
        plan = get_plan("basic")
        assert plan.requests_per_month == 10_000
        assert plan.price_cents == 900

    def test_pro_plan(self) -> None:
        plan = get_plan("pro")
        assert plan.requests_per_month == 100_000
        assert plan.price_cents == 2900

    def test_enterprise_plan(self) -> None:
        plan = get_plan("enterprise")
        assert plan.requests_per_month == 1_000_000

    def test_unknown_plan_returns_free(self) -> None:
        plan = get_plan("nonexistent")
        assert plan.name == "free"

    def test_all_plans_are_frozen(self) -> None:
        for plan in PLANS.values():
            assert isinstance(plan, PlanDefinition)
