"""Membership tiers, entitlement rules, post lifetimes and Stripe plumbing.

Everything here is server-side. The Stripe secret key is read from the
environment inside this module only, is never returned to the frontend, and is
validated to be a secret key before any API call is attempted.
"""

import asyncio
import datetime
import logging
import os
from urllib.parse import urlsplit

from sqlalchemy import text

# ---------------------------------------------------------------------------
# Tiers and entitlement
# ---------------------------------------------------------------------------

TIER_FREE = "free"
TIER_COFFEE = "coffee_monthly"
TIER_DINNER = "dinner_annual"
PREMIUM_TIERS: tuple[str, ...] = (TIER_COFFEE, TIER_DINNER)
ENTITLED_STATUSES: tuple[str, ...] = ("active", "trialing")

TIER_LABELS: dict[str, str] = {
    TIER_FREE: "Free member",
    TIER_COFFEE: "Monthly Ticket",
    TIER_DINNER: "Annual pass",
}

PLAN_PRICE_CENTS: dict[str, int] = {TIER_COFFEE: 500, TIER_DINNER: 4900}
PLAN_INTERVAL: dict[str, str] = {TIER_COFFEE: "month", TIER_DINNER: "year"}
PLAN_PRICE_LABEL: dict[str, str] = {
    TIER_COFFEE: "$5 monthly",
    TIER_DINNER: "$49 annually",
}
PLAN_PRODUCT_NAME: dict[str, str] = {
    TIER_COFFEE: "Go and Help — Monthly Ticket",
    TIER_DINNER: "Go and Help — Annual pass",
}

# Exact order shown in the membership window. This list is the single source of
# truth for the premium benefit copy.
PREMIUM_BENEFITS: list[str] = [
    "Unlimited community forum topics and comments",
    "Unlimited help offers",
    "Request multiple helpers for events",
    "Priority view help requests",
    "Metrics for increased responses",
    "Advanced Search Options",
    "10 simultaneous help requests",
    "Custom themes and modes",
]

FREE_BENEFITS: list[str] = [
    "1 help offer a day",
    "2 simultaneous help requests",
    "One-month post visibility",
    "Offer and give help anywhere, always free",
    "Read the community forum",
    "1 forum topic per UTC calendar month",
    "10 forum comments per UTC calendar month across all discussions",
    "Basic search by job category and reward",
]

# Concurrent open (unexpired) help request allowances.
FREE_POST_LIMIT = 2
PREMIUM_POST_LIMIT = 10

# Post lifetimes, expressed as fixed SQL interval literals.
FREE_POST_INTERVAL = "1 month"
PREMIUM_POST_INTERVAL = "1 year"

PAYMENTS_NOT_CONFIGURED = "Payments are not configured yet"

# Stripe replaces this literal token in the success URL with the real session
# id. It must never be interpolated by Python, so it is kept as a constant.
STRIPE_SESSION_TOKEN = "{CHECKOUT_SESSION_ID}"


def checkout_success_url(base_url: str) -> str:
    """Success URL carrying Stripe's literal `{CHECKOUT_SESSION_ID}` token."""
    root = (base_url or "").rstrip("/")
    return "".join(
        (root, "/membership/success?session_id=", STRIPE_SESSION_TOKEN)
    )


def checkout_cancel_url(base_url: str) -> str:
    root = (base_url or "").rstrip("/")
    return f"{root}/?membership=cancelled"


# Only open, unexpired posts count and appear in active browsing.
ACTIVE_POST_CLAUSE = "(p.expires_at IS NULL OR p.expires_at > now())"


def tier_label(tier: str) -> str:
    return TIER_LABELS.get(tier, TIER_LABELS[TIER_FREE])


def post_limit_for_tier(is_premium: bool) -> int:
    return PREMIUM_POST_LIMIT if is_premium else FREE_POST_LIMIT


def post_interval_for_tier(is_premium: bool) -> str:
    return PREMIUM_POST_INTERVAL if is_premium else FREE_POST_INTERVAL


def entitled(tier: str, status: str, period_end) -> bool:
    """Premium only for an active/trialing Coffee or Dinner inside its period."""
    if tier not in PREMIUM_TIERS or status not in ENTITLED_STATUSES:
        return False
    if period_end is None:
        return True
    now = datetime.datetime.now(datetime.UTC)
    try:
        if period_end.tzinfo is None:
            period_end = period_end.replace(tzinfo=datetime.UTC)
        return period_end >= now
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Could not compare membership period: {e}")
        return True


# ---------------------------------------------------------------------------
# Database reads / writes (all parameterised)
# ---------------------------------------------------------------------------


async def load_membership(asession, sid: int) -> dict[str, str]:
    """Authoritative membership snapshot. An absent row means free."""
    row = (
        await asession.execute(
            text(
                """
                SELECT tier, status, COALESCE(stripe_customer_id, ''),
                       current_period_end, cancel_at_period_end
                FROM skillkind_membership_subscription
                WHERE subscriber_id = :sid
                """
            ),
            {"sid": int(sid)},
        )
    ).first()
    if row is None:
        return {
            "tier": TIER_FREE,
            "status": "none",
            "customer": "",
            "premium": "0",
            "renewal": "",
        }
    tier = str(row[0] or TIER_FREE)
    status = str(row[1] or "none")
    premium = entitled(tier, status, row[3])
    renewal = ""
    if row[3] is not None:
        stamp = row[3].strftime("%b %d, %Y")
        renewal = f"Ends {stamp}" if bool(row[4]) else f"Renews {stamp}"
    return {
        "tier": tier,
        "status": status,
        "customer": str(row[2] or ""),
        "premium": "1" if premium else "0",
        "renewal": renewal,
    }


async def db_is_premium(asession, sid: int) -> bool:
    """Premium check straight from the database, for server-side write gates."""
    snapshot = await load_membership(asession, sid)
    return snapshot["premium"] == "1"


async def lock_subscriber(asession, sid: int) -> None:
    """Transaction-scoped advisory lock so concurrent posts cannot race."""
    await asession.execute(
        text("SELECT pg_advisory_xact_lock(:key, :sid)"),
        {"key": 918273, "sid": int(sid)},
    )


async def count_active_posts(asession, sid: int) -> int:
    row = (
        await asession.execute(
            text(
                f"""
                SELECT COUNT(*)
                FROM skillkind_help_post p
                WHERE p.author_id = :sid AND p.status = 'open'
                  AND {ACTIVE_POST_CLAUSE}
                """
            ),
            {"sid": int(sid)},
        )
    ).first()
    return int(row[0] or 0) if row else 0


async def check_post_allowance(
    asession, sid: int
) -> tuple[bool, bool, int, int]:
    """(allowed, is_premium, used, limit) under an advisory lock.

    Must be called inside the same transaction as the INSERT it guards.
    """
    await lock_subscriber(asession, sid)
    premium = await db_is_premium(asession, sid)
    used = await count_active_posts(asession, sid)
    limit = post_limit_for_tier(premium)
    return used < limit, premium, used, limit


def cap_message(is_premium: bool, limit: int) -> str:
    if is_premium:
        return (
            f"You already have {limit} open help requests — close or complete "
            "one before posting another."
        )
    return (
        f"Free membership allows {limit} open help requests at a time. "
        "Upgrade to keep up to 10 running, each visible for a whole year."
    )


async def ensure_expiry_notices(asession, sid: int) -> int:
    """Create exactly one unread `post_expiring` notice per post due in 24h."""
    rows = (
        await asession.execute(
            text(
                """
                SELECT id, title
                FROM skillkind_help_post
                WHERE author_id = :sid AND status = 'open'
                  AND expires_at IS NOT NULL
                  AND expires_at > now()
                  AND expires_at <= now() + INTERVAL '24 hours'
                  AND expiry_notice_sent_at IS NULL
                ORDER BY expires_at ASC
                LIMIT 25
                FOR UPDATE SKIP LOCKED
                """
            ),
            {"sid": int(sid)},
        )
    ).all()
    created = 0
    for row in rows:
        post_id = int(row[0])
        title = str(row[1] or "Your help request")
        inserted = (
            await asession.execute(
                text(
                    """
                    INSERT INTO skillkind_membership_notice
                        (subscriber_id, help_post_id, kind, title, body, is_read)
                    SELECT :sid, :pid, 'post_expiring', :title, :body, FALSE
                    WHERE NOT EXISTS (
                        SELECT 1 FROM skillkind_membership_notice
                        WHERE help_post_id = :pid AND kind = 'post_expiring'
                    )
                    RETURNING id
                    """
                ),
                {
                    "sid": int(sid),
                    "pid": post_id,
                    "title": "A help request expires within 24 hours",
                    "body": (
                        f'"{title}" disappears from the map and search when it '
                        "expires. Premium members keep every request visible "
                        "for a full year."
                    ),
                },
            )
        ).first()
        await asession.execute(
            text(
                """
                UPDATE skillkind_help_post
                SET expiry_notice_sent_at = now()
                WHERE id = :pid
                """
            ),
            {"pid": post_id},
        )
        if inserted is not None:
            created += 1
    await asession.commit()
    return created


async def upsert_membership(
    asession,
    sid: int,
    tier: str,
    status: str,
    customer_id: str,
    subscription_id: str,
    price_id: str,
    session_id: str,
    period_start,
    period_end,
    cancel_at_period_end: bool,
) -> None:
    await asession.execute(
        text(
            """
            INSERT INTO skillkind_membership_subscription
                (subscriber_id, tier, status, stripe_customer_id,
                 stripe_subscription_id, stripe_price_id,
                 stripe_checkout_session_id, current_period_start,
                 current_period_end, cancel_at_period_end, last_synced_at,
                 updated_at)
            VALUES
                (:sid, :tier, :status, :customer, :subscription, :price,
                 :session, :period_start, :period_end, :cancel, now(), now())
            ON CONFLICT (subscriber_id) DO UPDATE SET
                tier = EXCLUDED.tier,
                status = EXCLUDED.status,
                stripe_customer_id = EXCLUDED.stripe_customer_id,
                stripe_subscription_id = EXCLUDED.stripe_subscription_id,
                stripe_price_id = EXCLUDED.stripe_price_id,
                stripe_checkout_session_id =
                    EXCLUDED.stripe_checkout_session_id,
                current_period_start = EXCLUDED.current_period_start,
                current_period_end = EXCLUDED.current_period_end,
                cancel_at_period_end = EXCLUDED.cancel_at_period_end,
                last_synced_at = now(),
                updated_at = now()
            """
        ),
        {
            "sid": int(sid),
            "tier": tier,
            "status": status,
            "customer": customer_id[:255],
            "subscription": subscription_id[:255],
            "price": price_id[:255],
            "session": session_id[:255],
            "period_start": period_start,
            "period_end": period_end,
            "cancel": bool(cancel_at_period_end),
        },
    )
    await asession.commit()


# ---------------------------------------------------------------------------
# Stripe
# ---------------------------------------------------------------------------


def stripe_secret_key() -> str:
    """The configured Stripe SECRET key, or "" when unusable.

    A publishable key (`pk_...`) or a missing value returns "" so callers can
    refuse to continue instead of failing mid-checkout.
    """
    key = (os.environ.get("STRIPE_API_KEY") or "").strip()
    if key.startswith("sk_") or key.startswith("rk_"):
        return key
    return ""


def public_base_url(router_url: str) -> str:
    """Configured public base URL, else the current request origin."""
    configured = (os.environ.get("GOANDHELP_PUBLIC_BASE_URL") or "").strip()
    if configured:
        return configured.rstrip("/")
    parts = urlsplit(router_url or "")
    if parts.scheme and parts.netloc:
        return f"{parts.scheme}://{parts.netloc}"
    return ""


def _timestamp(value) -> datetime.datetime | None:
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        return None
    if seconds <= 0:
        return None
    return datetime.datetime.fromtimestamp(seconds, datetime.UTC)


def subscription_period(
    subscription,
) -> tuple[datetime.datetime | None, datetime.datetime | None, str, str, bool]:
    """Extract (start, end, status, price_id, cancel_at_period_end)."""
    status = str(subscription.get("status") or "incomplete")
    cancel = bool(subscription.get("cancel_at_period_end") or False)
    start = _timestamp(subscription.get("current_period_start"))
    end = _timestamp(subscription.get("current_period_end"))
    price_id = ""
    items = (subscription.get("items") or {}).get("data") or []
    if items:
        first = items[0]
        price_id = str((first.get("price") or {}).get("id") or "")
        if start is None:
            start = _timestamp(first.get("current_period_start"))
        if end is None:
            end = _timestamp(first.get("current_period_end"))
    return start, end, status, price_id, cancel


async def create_checkout_session(
    key: str,
    tier: str,
    subscriber_id: int,
    email: str,
    customer_id: str,
    base_url: str,
) -> tuple[str, str, str]:
    """Create/reuse a Stripe customer and a subscription Checkout Session.

    Returns (checkout_url, customer_id, error). No secret is ever returned.
    """
    import stripe

    price_cents = PLAN_PRICE_CENTS.get(tier)
    interval = PLAN_INTERVAL.get(tier)
    if price_cents is None or interval is None:
        return (
            "",
            customer_id,
            "Choose the Monthly Ticket or the Annual pass first.",
        )
    try:
        if not customer_id:
            customer = await asyncio.to_thread(
                stripe.Customer.create,
                api_key=key,
                email=email,
                metadata={"subscriber_id": str(subscriber_id)},
            )
            customer_id = str(customer.id)
        session = await asyncio.to_thread(
            stripe.checkout.Session.create,
            api_key=key,
            mode="subscription",
            # Use standard Stripe Checkout/Billing regardless of the account Managed Payments default.
            managed_payments={"enabled": False},
            customer=customer_id,
            client_reference_id=str(subscriber_id),
            success_url=checkout_success_url(base_url),
            cancel_url=checkout_cancel_url(base_url),
            line_items=[
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": price_cents,
                        "recurring": {"interval": interval},
                        "product_data": {
                            "name": PLAN_PRODUCT_NAME[tier],
                        },
                    },
                }
            ],
            metadata={"subscriber_id": str(subscriber_id), "tier": tier},
            subscription_data={
                "metadata": {
                    "subscriber_id": str(subscriber_id),
                    "tier": tier,
                }
            },
        )
        url = str(session.url or "")
        if not url:
            return "", customer_id, "Stripe did not return a checkout page."
        return url, customer_id, ""
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Stripe checkout session failed: {e}")
        return (
            "",
            customer_id,
            "We couldn't start checkout with our payment provider. "
            "Please try again in a moment.",
        )


async def retrieve_checkout(key: str, session_id: str):
    """Retrieve a Checkout Session with its subscription expanded."""
    import stripe

    return await asyncio.to_thread(
        stripe.checkout.Session.retrieve,
        session_id,
        api_key=key,
        expand=["subscription"],
    )


async def create_billing_portal(
    key: str, customer_id: str, base_url: str
) -> tuple[str, str]:
    """Return (portal_url, error) for managing or cancelling a membership."""
    import stripe

    try:
        session = await asyncio.to_thread(
            stripe.billing_portal.Session.create,
            api_key=key,
            customer=customer_id,
            return_url=f"{base_url}/",
        )
        return str(session.url or ""), ""
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Stripe billing portal failed: {e}")
        return "", "We couldn't open the billing portal just now."
