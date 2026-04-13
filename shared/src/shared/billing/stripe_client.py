# DEVIATION: Stripe SDK uses sync HTTP (requests) internally. Billing operations
# are infrequent (not per-request), so the thread-pool overhead is acceptable.
import stripe

from shared.billing.plans import PlanDefinition


class StripeClient:
    def __init__(self, secret_key: str) -> None:
        self._key = secret_key

    def create_customer(self, email: str) -> str:
        customer = stripe.Customer.create(email=email, api_key=self._key)
        return str(customer.id)

    def create_subscription(self, customer_id: str, plan: PlanDefinition) -> str | None:
        if plan.stripe_price_id is None:
            return None
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": plan.stripe_price_id}],
            api_key=self._key,
        )
        return str(subscription.id)

    def cancel_subscription(self, subscription_id: str) -> None:
        stripe.Subscription.cancel(subscription_id, api_key=self._key)
