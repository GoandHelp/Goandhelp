"""Central membership state: tier, entitlement, paywall and Stripe checkout."""

import logging
from typing import TypedDict
from urllib.parse import parse_qs, urlsplit

import reflex as rx
from sqlalchemy import text

from app.membership import (
    FREE_BENEFITS,
    FREE_POST_LIMIT,
    PAYMENTS_NOT_CONFIGURED,
    PLAN_PRICE_LABEL,
    PREMIUM_BENEFITS,
    PREMIUM_POST_LIMIT,
    TIER_COFFEE,
    TIER_DINNER,
    TIER_FREE,
    create_billing_portal,
    create_checkout_session,
    ensure_expiry_notices,
    load_membership,
    public_base_url,
    retrieve_checkout,
    stripe_secret_key,
    subscription_period,
    tier_label,
    upsert_membership,
)
from app.states.auth_state import AuthState


class NoticeItem(TypedDict):
    id: int
    kind: str
    title: str
    body: str
    created: str


class MembershipState(rx.State):
    """Authoritative membership view model for the signed-in subscriber."""

    tier: str = TIER_FREE
    status: str = "none"
    is_premium: bool = False
    # Non-secret Stripe customer reference, used only to offer the portal.
    has_billing_account: bool = False
    renewal_label: str = ""
    is_loading: bool = False
    loaded: bool = False

    paywall_open: bool = False
    upgrade_reason: str = ""
    selected_plan: str = TIER_COFFEE
    checkout_busy: bool = False
    error: str = ""

    notices: list[NoticeItem] = []

    # /membership/success verification
    verify_state: str = "idle"
    verify_message: str = ""

    premium_benefits: list[str] = PREMIUM_BENEFITS
    free_benefits: list[str] = FREE_BENEFITS

    @rx.var
    def tier_name(self) -> str:
        return tier_label(self.tier)

    @rx.var
    def post_limit(self) -> int:
        return PREMIUM_POST_LIMIT if self.is_premium else FREE_POST_LIMIT

    @rx.var
    def post_limit_label(self) -> str:
        if self.is_premium:
            return f"Up to {PREMIUM_POST_LIMIT} open requests · visible 1 year"
        return f"Up to {FREE_POST_LIMIT} open requests · visible 1 month"

    @rx.var
    def coffee_price_label(self) -> str:
        return PLAN_PRICE_LABEL[TIER_COFFEE]

    @rx.var
    def dinner_price_label(self) -> str:
        return PLAN_PRICE_LABEL[TIER_DINNER]

    @rx.var
    def coffee_selected(self) -> bool:
        return self.selected_plan == TIER_COFFEE

    @rx.var
    def dinner_selected(self) -> bool:
        return self.selected_plan == TIER_DINNER

    @rx.var
    def has_notices(self) -> bool:
        return len(self.notices) > 0

    @rx.var
    def notice_count_label(self) -> str:
        count = len(self.notices)
        if count == 1:
            return "1 membership notice"
        return f"{count} membership notices"

    # ------------------------------------------------------------------
    # Paywall surface
    # ------------------------------------------------------------------

    @rx.event
    def open_paywall(self, reason: str = ""):
        self.paywall_open = True
        self.upgrade_reason = reason
        self.error = ""

    @rx.event
    def close_paywall(self):
        self.paywall_open = False
        self.upgrade_reason = ""
        self.error = ""

    @rx.event
    def select_plan(self, plan: str):
        if plan in (TIER_COFFEE, TIER_DINNER):
            self.selected_plan = plan
            self.error = ""

    def _reset(self):
        self.tier = TIER_FREE
        self.status = "none"
        self.is_premium = False
        self.has_billing_account = False
        self.renewal_label = ""
        self.notices = []
        self.paywall_open = False
        self.upgrade_reason = ""
        self.selected_plan = TIER_COFFEE
        self.checkout_busy = False
        self.error = ""
        self.loaded = False
        self.is_loading = False
        self.verify_state = "idle"
        self.verify_message = ""

    @rx.event
    def clear_membership(self):
        self.tier = TIER_FREE
        self.status = "none"
        self.is_premium = False
        self.has_billing_account = False
        self.renewal_label = ""
        self.notices = []
        self.paywall_open = False
        self.upgrade_reason = ""
        self.selected_plan = TIER_COFFEE
        self.checkout_busy = False
        self.error = ""
        self.loaded = False
        self.is_loading = False
        self.verify_state = "idle"
        self.verify_message = ""

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    @rx.event(background=True)
    async def load_membership(self):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
        if not sid.isdigit():
            async with self:
                self._reset()
            return
        async with self:
            self.is_loading = True
            self.error = ""
        async with rx.asession() as asession:
            snapshot = await load_membership(asession, int(sid))
            try:
                await ensure_expiry_notices(asession, int(sid))
            except Exception as e:  # noqa: BLE001
                logging.exception(f"Could not evaluate post expiry: {e}")
            notice_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT id, kind, title, COALESCE(body, ''), created_at
                        FROM skillkind_membership_notice
                        WHERE subscriber_id = :sid AND is_read = FALSE
                        ORDER BY created_at DESC
                        LIMIT 10
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).all()
        async with self:
            self.tier = snapshot["tier"]
            self.status = snapshot["status"]
            self.is_premium = snapshot["premium"] == "1"
            self.has_billing_account = snapshot["customer"] != ""
            self.renewal_label = snapshot["renewal"]
            self.notices = [
                {
                    "id": int(r[0]),
                    "kind": str(r[1] or ""),
                    "title": str(r[2] or ""),
                    "body": str(r[3] or ""),
                    "created": r[4].strftime("%b %d, %Y · %H:%M")
                    if r[4] is not None
                    else "",
                }
                for r in notice_rows
            ]
            self.is_loading = False
            self.loaded = True

    @rx.event(background=True)
    async def dismiss_notice(self, notice_id: int):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
        if not sid.isdigit():
            return
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_membership_notice
                    SET is_read = TRUE, read_at = now()
                    WHERE id = :nid AND subscriber_id = :sid
                    """
                ),
                {"nid": int(notice_id), "sid": int(sid)},
            )
            await asession.commit()
        async with self:
            self.notices = [n for n in self.notices if n["id"] != notice_id]

    # ------------------------------------------------------------------
    # Stripe checkout / portal
    # ------------------------------------------------------------------

    @rx.event(background=True)
    async def start_checkout(self):
        key = stripe_secret_key()
        async with self:
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id
            email = auth.email
            plan = self.selected_plan
            base_url = public_base_url(str(self.router.url))
        if not key:
            async with self:
                self.error = (
                    f"{PAYMENTS_NOT_CONFIGURED} — no membership was started "
                    "and nothing was charged."
                )
                self.checkout_busy = False
            yield rx.toast(PAYMENTS_NOT_CONFIGURED, duration=5000)
            return
        if not sid.isdigit():
            async with self:
                self.error = "Please sign in again before upgrading."
            return
        if not base_url:
            async with self:
                self.error = (
                    "We couldn't work out a safe return address for checkout."
                )
            return
        async with self:
            self.checkout_busy = True
            self.error = ""
        async with rx.asession() as asession:
            snapshot = await load_membership(asession, int(sid))
        url, customer_id, problem = await create_checkout_session(
            key,
            plan,
            int(sid),
            email,
            snapshot["customer"],
            base_url,
        )
        if customer_id and customer_id != snapshot["customer"]:
            async with rx.asession() as asession:
                await asession.execute(
                    text(
                        """
                        INSERT INTO skillkind_membership_subscription
                            (subscriber_id, tier, status, stripe_customer_id,
                             updated_at)
                        VALUES (:sid, 'free', 'incomplete', :customer, now())
                        ON CONFLICT (subscriber_id) DO UPDATE SET
                            stripe_customer_id = EXCLUDED.stripe_customer_id,
                            updated_at = now()
                        """
                    ),
                    {"sid": int(sid), "customer": customer_id[:255]},
                )
                await asession.commit()
        if problem:
            async with self:
                self.checkout_busy = False
                self.error = problem
            yield rx.toast(problem, duration=5000)
            return
        async with self:
            self.checkout_busy = False
            self.has_billing_account = True
        yield rx.redirect(url, is_external=True)

    @rx.event(background=True)
    async def open_billing_portal(self):
        key = stripe_secret_key()
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            base_url = public_base_url(str(self.router.url))
        if not key:
            async with self:
                self.error = PAYMENTS_NOT_CONFIGURED
            yield rx.toast(PAYMENTS_NOT_CONFIGURED, duration=5000)
            return
        if not sid.isdigit():
            return
        async with rx.asession() as asession:
            snapshot = await load_membership(asession, int(sid))
        if not snapshot["customer"]:
            async with self:
                self.error = "There is no billing account to manage yet."
            return
        url, problem = await create_billing_portal(
            key, snapshot["customer"], base_url
        )
        if problem or not url:
            async with self:
                self.error = problem or "The billing portal is unavailable."
            return
        yield rx.redirect(url, is_external=True)

    # ------------------------------------------------------------------
    # /membership/success — verified server-side, never from query params
    # ------------------------------------------------------------------

    @rx.event(background=True)
    async def verify_checkout(self):
        key = stripe_secret_key()
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            raw_url = str(self.router.url)
            self.verify_state = "verifying"
            self.verify_message = ""
        session_id = ""
        try:
            query = parse_qs(urlsplit(raw_url).query)
            session_id = (query.get("session_id") or [""])[0].strip()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Could not read the checkout reference: {e}")
        if not key:
            async with self:
                self.verify_state = "error"
                self.verify_message = (
                    f"{PAYMENTS_NOT_CONFIGURED} — no membership was activated."
                )
            return
        if not sid.isdigit():
            async with self:
                self.verify_state = "error"
                self.verify_message = (
                    "Please sign in with the account you paid with so we can "
                    "confirm your membership."
                )
            return
        if not session_id.startswith("cs_"):
            async with self:
                self.verify_state = "error"
                self.verify_message = (
                    "That link has no valid checkout reference, so nothing "
                    "was changed."
                )
            return
        try:
            session = await retrieve_checkout(key, session_id)
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Checkout verification failed: {e}")
            async with self:
                self.verify_state = "error"
                self.verify_message = (
                    "We couldn't verify that payment with our provider. Your "
                    "membership was not changed."
                )
            return

        metadata = dict(session.get("metadata") or {})
        meta_sid = str(metadata.get("subscriber_id") or "")
        client_ref = str(session.get("client_reference_id") or "")
        tier = str(metadata.get("tier") or "")
        payment_status = str(session.get("payment_status") or "")
        subscription = session.get("subscription")
        customer = session.get("customer")
        customer_id = (
            str(customer.get("id"))
            if isinstance(customer, dict)
            else str(customer or "")
        )
        if sid not in (meta_sid, client_ref) or tier not in (
            TIER_COFFEE,
            TIER_DINNER,
        ):
            async with self:
                self.verify_state = "error"
                self.verify_message = (
                    "That checkout belongs to a different account, so no "
                    "membership was granted."
                )
            return
        if payment_status not in ("paid", "no_payment_required"):
            async with self:
                self.verify_state = "error"
                self.verify_message = (
                    "Stripe has not confirmed that payment yet. Nothing was "
                    "changed — please try again shortly."
                )
            return
        if not isinstance(subscription, dict):
            async with self:
                self.verify_state = "error"
                self.verify_message = (
                    "Stripe has not created the subscription yet. Nothing was "
                    "changed — please refresh in a moment."
                )
            return
        start, end, status, price_id, cancel = subscription_period(subscription)
        subscription_id = str(subscription.get("id") or "")
        async with rx.asession() as asession:
            await upsert_membership(
                asession,
                int(sid),
                tier,
                status,
                customer_id,
                subscription_id,
                price_id,
                session_id,
                start,
                end,
                cancel,
            )
        async with self:
            self.verify_state = "ok"
            self.verify_message = (
                "Thank you — your premium membership is active."
            )
            self.paywall_open = False
            self.upgrade_reason = ""
        yield MembershipState.load_membership
