import stripe
from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def handle_stripe_webhook(request: Request) -> JSONResponse:
    """Handle Stripe webhook events for subscription lifecycle."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    settings = request.app.state.shared_settings

    try:
        # DEVIATION: construct_event is untyped in the Stripe SDK stubs; the
        # ignore is scoped to this call only and does not suppress other errors.
        event = stripe.Webhook.construct_event(  # type: ignore[no-untyped-call]
            payload, sig_header, settings.stripe_webhook_secret
        )
    except (ValueError, stripe.SignatureVerificationError):
        return JSONResponse(status_code=400, content={"error": "Invalid webhook signature"})

    event_type: str = event["type"]

    if event_type == "customer.subscription.updated":
        # Plan change — invalidate API key cache so new limits take effect
        pass
    elif event_type == "customer.subscription.deleted":
        # Cancellation — deactivate keys or downgrade to free
        pass
    elif event_type == "invoice.payment_failed":
        # Payment failure — could send alert or grace period
        pass

    return JSONResponse(content={"status": "ok"})
