"""The `/reset-password` screen: validate a single-use link, set a new password.

The plaintext token never enters a frontend var and is never logged: it is kept
in a backend-only var (`_token`) and only its SHA-256 digest touches the
database, matching `skillkind_password_reset_token`.
"""

import logging
from typing import Any

import reflex as rx
from sqlalchemy import text

from app.states.auth_state import hash_password
from app.verification import token_digest

MIN_PASSWORD_LENGTH = 6


class PasswordResetState(rx.State):
    """Reset-link validation and the new-password form."""

    # "checking" | "ready" | "invalid" | "done"
    phase: str = "checking"
    email_hint: str = ""
    error: str = ""
    success: str = ""
    is_busy: bool = False
    # Backend-only: never rendered, never logged.
    _token: str = ""

    @rx.var
    def is_ready(self) -> bool:
        return self.phase == "ready"

    @rx.var
    def is_checking(self) -> bool:
        return self.phase == "checking"

    @rx.var
    def is_done(self) -> bool:
        return self.phase == "done"

    def _read_token(self) -> str:
        """The `?token=` value from the emailed link (never logged)."""
        params = getattr(self.router.url, "query_parameters", None)
        if not params:
            params = getattr(self.router.page, "params", None) or {}
        raw = params.get("token", "")
        if isinstance(raw, list):
            raw = raw[0] if raw else ""
        return str(raw or "").strip()

    @rx.event(background=True)
    async def load_reset(self):
        """Validate the emailed link before showing the password form."""
        async with self:
            self._token = self._read_token()
            token = self._token
            self.phase = "checking"
            self.error = ""
            self.success = ""
            self.email_hint = ""
        if not token:
            async with self:
                self.phase = "invalid"
                self.error = (
                    "That reset link is incomplete. Please request a new one "
                    "from the sign-in panel."
                )
            return
        row = None
        try:
            async with rx.asession() as asession:
                row = (
                    await asession.execute(
                        text(
                            """
                            SELECT t.id, t.email
                            FROM skillkind_password_reset_token t
                            JOIN skillkind_subscriber s
                              ON s.id = t.subscriber_id
                            WHERE t.token_digest = :digest
                              AND t.used_at IS NULL
                              AND t.invalidated_at IS NULL
                              AND t.expires_at > now()
                              AND s.is_active = TRUE
                            """
                        ),
                        {"digest": token_digest(token)},
                    )
                ).first()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Reset link validation failed: {e}")
        if row is None:
            async with self:
                self.phase = "invalid"
                self.error = (
                    "This reset link has already been used or has expired. "
                    "Request a fresh one from the sign-in panel."
                )
            return
        async with self:
            self.phase = "ready"
            self.email_hint = str(row[1] or "")

    @rx.event(background=True)
    async def submit_new_password(self, form_data: dict[str, Any]):
        """Atomically claim the token and store the new password hash."""
        password = str(form_data.get("password", "") or "")
        confirm = str(form_data.get("confirm_password", "") or "")
        async with self:
            token = self._token
            phase = self.phase
        if phase != "ready" or not token:
            async with self:
                self.error = (
                    "This reset link is no longer usable. Request a new one."
                )
            return
        problem = ""
        if len(password) < MIN_PASSWORD_LENGTH:
            problem = (
                f"Passwords need at least {MIN_PASSWORD_LENGTH} characters."
            )
        elif password != confirm:
            problem = "The two passwords don't match."
        if problem:
            async with self:
                self.error = problem
                self.success = ""
            return
        async with self:
            self.is_busy = True
            self.error = ""
            self.success = ""
        claimed = None
        try:
            async with rx.asession() as asession:
                claimed = (
                    await asession.execute(
                        text(
                            """
                            UPDATE skillkind_password_reset_token
                            SET used_at = now()
                            WHERE token_digest = :digest
                              AND used_at IS NULL
                              AND invalidated_at IS NULL
                              AND expires_at > now()
                            RETURNING id, subscriber_id
                            """
                        ),
                        {"digest": token_digest(token)},
                    )
                ).first()
                if claimed is not None:
                    await asession.execute(
                        text(
                            """
                            UPDATE skillkind_subscriber
                            SET password_hash = :pwd
                            WHERE id = :sid AND is_active = TRUE
                            """
                        ),
                        {
                            "pwd": hash_password(password),
                            "sid": int(claimed[1]),
                        },
                    )
                    await asession.execute(
                        text(
                            """
                            UPDATE skillkind_password_reset_token
                            SET invalidated_at = now()
                            WHERE subscriber_id = :sid
                              AND id <> :tid
                              AND used_at IS NULL
                              AND invalidated_at IS NULL
                            """
                        ),
                        {"sid": int(claimed[1]), "tid": int(claimed[0])},
                    )
                await asession.commit()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Password reset could not be completed: {e}")
            async with self:
                self.is_busy = False
                self.error = "We couldn't save that password just now."
            return
        if claimed is None:
            async with self:
                self.is_busy = False
                self.phase = "invalid"
                self.error = (
                    "This reset link has already been used or has expired."
                )
            return
        async with self:
            self._token = ""
            self.is_busy = False
            self.phase = "done"
            self.success = (
                "Your password is updated. You can sign in with it now."
            )
        from app.interface_i18n import translate
        from app.states.auth_state import AuthState

        async with self:
            auth = await self.get_state(AuthState)
            notification = translate(auth.preferred_language, self.success)
        yield rx.toast(notification, duration=4000)

    @rx.event
    def go_to_sign_in(self):
        from app.states.auth_state import AuthState

        return [
            AuthState.set_auth_tab("signin"),
            rx.redirect("/"),
        ]
