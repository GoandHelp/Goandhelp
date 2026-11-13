"""Server-side consumption of an emailed verification link."""

import logging

import reflex as rx
from sqlalchemy import text

from app.verification import token_digest

STATUS_CHECKING = "checking"
STATUS_SUCCESS = "success"
STATUS_MISSING = "missing"
STATUS_INVALID = "invalid"
STATUS_ERROR = "error"


class VerifyState(rx.State):
    """Consumes ?token=... exactly once, atomically, on the server."""

    status: str = STATUS_CHECKING
    verified_email: str = ""
    verified_name: str = ""
    headline: str = "Confirming your email…"
    detail: str = "Give us a moment while we check your confirmation link."

    @rx.var
    def is_checking(self) -> bool:
        return self.status == STATUS_CHECKING

    @rx.var
    def is_success(self) -> bool:
        return self.status == STATUS_SUCCESS

    @rx.event(background=True)
    async def consume_token(self):
        async with self:
            raw = self.router.url.query_parameters.get("token", "")
            self.status = STATUS_CHECKING
            self.headline = "Confirming your email…"
            self.detail = (
                "Give us a moment while we check your confirmation link."
            )
            self.verified_email = ""
            self.verified_name = ""
        token = str(raw or "").strip()
        if not token:
            async with self:
                self.status = STATUS_MISSING
                self.headline = "This link is missing its confirmation code"
                self.detail = (
                    "Open the confirmation link straight from the email we sent, "
                    "or request a fresh one below."
                )
            return

        digest = token_digest(token)
        try:
            async with rx.asession() as asession:
                # Atomic single-use claim: only an unused, un-invalidated and
                # unexpired row can be stamped, so a replayed link does nothing.
                claimed = (
                    await asession.execute(
                        text(
                            """
                            UPDATE skillkind_email_verification_token
                            SET used_at = now()
                            WHERE token_digest = :digest
                              AND used_at IS NULL
                              AND invalidated_at IS NULL
                              AND expires_at > now()
                            RETURNING id, subscriber_id, email
                            """
                        ),
                        {"digest": digest},
                    )
                ).first()
                if claimed is None:
                    await asession.commit()
                    async with self:
                        self.status = STATUS_INVALID
                        self.headline = "This confirmation link no longer works"
                        self.detail = (
                            "Links expire after an hour and can only be used once. "
                            "Ask for a fresh confirmation link below."
                        )
                    return
                subscriber_id = int(claimed[1])
                email = str(claimed[2] or "")
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_subscriber
                        SET is_verified = TRUE, is_active = TRUE
                        WHERE id = :sid
                        """
                    ),
                    {"sid": subscriber_id},
                )
                # Any other outstanding link for this account is now dead.
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_email_verification_token
                        SET invalidated_at = now()
                        WHERE subscriber_id = :sid
                          AND used_at IS NULL AND invalidated_at IS NULL
                        """
                    ),
                    {"sid": subscriber_id},
                )
                row = (
                    await asession.execute(
                        text(
                            """
                            SELECT display_name, email, phone, help_mode,
                                   joined_at,
                                   COALESCE(preferred_language, 'en'),
                                   is_admin
                            FROM skillkind_subscriber WHERE id = :sid
                            """
                        ),
                        {"sid": subscriber_id},
                    )
                ).first()
                # Safety net only: registration already creates this row in its
                # own transaction. This idempotent insert covers accounts made
                # before that invariant existed; an existing row is untouched and
                # no historic account is ever backfilled in bulk.
                await asession.execute(
                    text(
                        """
                        INSERT INTO skillkind_onboarding_progress
                            (subscriber_id, current_step, completed_steps,
                             answers_json, permissions_json, tour_current_step)
                        VALUES (:sid, 1, '', '{}', '{}', 0)
                        ON CONFLICT (subscriber_id) DO NOTHING
                        """
                    ),
                    {"sid": subscriber_id},
                )
                await asession.commit()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Verification failed: {e}")
            async with self:
                self.status = STATUS_ERROR
                self.headline = "We couldn't confirm your email just now"
                self.detail = (
                    "Something went wrong on our side. Please try the link again "
                    "in a moment, or request a fresh one."
                )
            return

        name = str(row[0] or "") if row is not None else ""
        verified_email = str(row[1] or email) if row is not None else email
        from app.states.auth_state import AuthState
        from app.states.membership_state import MembershipState
        from app.states.onboarding_state import OnboardingState
        from app.states.profile_state import ProfileState

        async with self:
            self.status = STATUS_SUCCESS
            self.verified_email = verified_email
            self.verified_name = name
            self.headline = "Email confirmed — let's set up your account"
            self.detail = (
                "Your Go and Help account is active and you're signed in. "
                "Fifteen quick taps and your map is ready."
            )
            # Hydrate the session for exactly this just-verified subscriber.
            auth = await self.get_state(AuthState)
            auth.subscriber_id = str(subscriber_id)
            auth.email = verified_email
            auth.display_name = name
            auth.is_verified = True
            auth.unverified_access = False
            auth.checking_session = False
            auth.awaiting_verification = False
            auth.pending_email = ""
            auth.error = ""
            auth.success = ""
            if row is not None:
                auth.phone = str(row[2] or "")
                auth.help_mode = str(row[3] or "both")
                auth.joined_label = (
                    row[4].strftime("%b %d, %Y") if row[4] is not None else ""
                )
                auth.preferred_language = str(row[5] or "en")
                auth.is_admin = bool(row[6])
            # Onboarding must be fully resolved before we redirect home, so the
            # root gate never renders the product for this fresh account.
            onboarding = await self.get_state(OnboardingState)
            await onboarding._resolve_progress(str(subscriber_id), True)
        yield ProfileState.load_profile
        yield MembershipState.load_membership
        from app.interface_i18n import translate

        async with self:
            auth = await self.get_state(AuthState)
            notification = translate(auth.preferred_language, self.headline)
        yield rx.toast(notification, duration=4000)
        yield rx.redirect("/")
