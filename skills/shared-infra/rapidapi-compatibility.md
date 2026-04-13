# RapidAPI Compatibility

## When to Consult
When adding RapidAPI support to a new API, debugging RapidAPI-specific issues, or handling dual-channel logic.

## Principles

1. **RapidAPI is a proxy.** Requests come from RapidAPI's servers, not the end user. The real user identity is in `X-RapidAPI-User`.
2. **Validate the proxy secret on every request.** `X-RapidAPI-Proxy-Secret` must match your configured secret. Without this check, anyone can spoof RapidAPI headers.
3. **RapidAPI handles billing for its channel.** Don't charge RapidAPI users via Stripe. Meter their usage for analytics only.
4. **The API must behave identically regardless of channel.** Same endpoints, same response format, same rate limits. The only difference is how auth works.
5. **RapidAPI adds latency.** One extra network hop. Don't add more by doing redundant auth checks.

## Patterns

### Channel Detection

```python
from starlette.requests import Request

def detect_channel(request: Request) -> str:
    if request.headers.get("X-RapidAPI-Proxy-Secret"):
        return "rapidapi"
    return "direct"
```

Store the channel in `request.state.channel` via middleware. Downstream code checks `request.state.channel` when behavior differs.

### RapidAPI Headers

| Header | Purpose |
|--------|---------|
| `X-RapidAPI-Proxy-Secret` | Authenticates that the request came from RapidAPI (not spoofed) |
| `X-RapidAPI-User` | The RapidAPI subscriber's username |
| `X-RapidAPI-Subscription` | The subscriber's plan tier on RapidAPI |

### Dual-Channel Auth Dependency

```python
from typing import Annotated
from fastapi import Depends, Header, HTTPException, Request

async def require_api_key(
    request: Request,
    x_api_key: str | None = Header(None),
    x_rapidapi_proxy_secret: str | None = Header(None),
) -> AuthContext:
    if x_rapidapi_proxy_secret:
        # RapidAPI channel
        if x_rapidapi_proxy_secret != settings.rapidapi_proxy_secret:
            raise HTTPException(status_code=401, detail="Invalid proxy secret")
        return AuthContext(
            channel="rapidapi",
            user_id=request.headers.get("X-RapidAPI-User", "unknown"),
            plan=request.headers.get("X-RapidAPI-Subscription", "free"),
        )
    elif x_api_key:
        # Direct channel — validate API key against database
        key_record = await validate_api_key(x_api_key)
        return AuthContext(
            channel="direct",
            user_id=key_record.user_id,
            plan=key_record.plan_id,
        )
    else:
        raise HTTPException(status_code=401, detail="API key required")
```

### Testing RapidAPI Locally

Include the RapidAPI headers in test requests:

```bash
curl -H "X-RapidAPI-Proxy-Secret: test-secret" \
     -H "X-RapidAPI-User: test-user" \
     -H "X-RapidAPI-Subscription: BASIC" \
     http://localhost:8000/validate?email=test@example.com
```

## Anti-Patterns

- **Skipping proxy secret validation.** Anyone can send `X-RapidAPI-User: premium-user` headers. Without proxy secret validation, your API is open to abuse.
- **Different response formats per channel.** The consumer's code shouldn't need to know which channel it came through.
- **Billing RapidAPI users via Stripe.** Double billing. RapidAPI already charged them.
- **Ignoring `X-RapidAPI-Subscription` for rate limiting.** Use it to apply plan-appropriate rate limits, even though RapidAPI has its own limits.

## Checklist

- [ ] `X-RapidAPI-Proxy-Secret` validated on every RapidAPI request
- [ ] `X-RapidAPI-User` extracted and stored in request state
- [ ] Channel detection sets `request.state.channel`
- [ ] Same response format regardless of channel
- [ ] Metering applies to both channels
- [ ] Billing only applies to direct channel
- [ ] Proxy secret stored in environment variable
