"""Registration / sign-in state for Go and Help subscribers."""

import asyncio
import datetime
import hashlib
import json
import logging
import re
from typing import Any
from urllib.parse import urlsplit

import reflex as rx
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.interface_i18n import catalog, translate
from app.countries import (
    DEFAULT_PHONE_CODE_VALUE,
    PHONE_CODE_VALUES,
    compose_phone,
    dial_prefix,
    is_plausible_phone_number,
    national_digits,
)
from app.models import (
    DEFAULT_LANGUAGE,
    PASSWORD_RESET_MAX_SENDS_PER_DAY,
    PASSWORD_RESET_RESEND_COOLDOWN_SECONDS,
    PASSWORD_RESET_TOKEN_TTL_MINUTES,
    FAMILY_NAME_MAX_LENGTH,
    FIRST_NAME_MAX_LENGTH,
    HELP_MODE_BOTH,
    HELP_MODES,
    LANGUAGE_CODES,
    LANGUAGE_LABELS,
    VERIFICATION_MAX_SENDS_PER_DAY,
    VERIFICATION_PURPOSE_RESEND,
    VERIFICATION_PURPOSE_SIGNUP,
    VERIFICATION_RESEND_COOLDOWN_SECONDS,
)
from app.verification import (
    new_verification_token,
    password_reset_link,
    send_password_reset_email,
    send_verification_email,
    token_expiry,
    verification_link,
)

# Generic, non-enumerating reply used for every password-reset request.
RESET_GENERIC_NOTE = (
    "If that email belongs to a Go and Help account, a password reset link is "
    "on its way. Check your inbox and spam folder."
)
RESET_THROTTLED_NOTE = (
    "A reset link was requested very recently. Please wait a couple of minutes "
    "before asking for another one."
)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")

# Reversible temporary access flag: active accounts with valid credentials may
# use the product before confirming email. The database truth remains unverified.
# Set to False to restore the email-confirmation gate and signup delivery.
ALLOW_UNVERIFIED_SIGN_IN = True

UNVERIFIED_BYPASS_NOTE = (
    "Temporary access granted while your email is still unconfirmed."
)

# Generic, non-enumerating reply used for every resend outcome.
RESEND_GENERIC_NOTE = (
    "If that email belongs to an unconfirmed Go and Help account, a fresh "
    "confirmation link is on its way. Check your inbox and spam folder."
)
LOCAL_PREVIEW_HOSTS: tuple[str, ...] = (
    "localhost",
    "127.0.0.1",
    "[::1]",
    "::1",
)
LOCAL_PREVIEW_ONLY_NOTE = (
    "The member preview only works on a local development machine "
    "(localhost or 127.0.0.1). Please sign in with a confirmed account."
)


def is_local_host(router_url: str) -> bool:
    """True only when the request origin is a local development host."""
    host = urlsplit(router_url or "").hostname or ""
    return host.lower() in LOCAL_PREVIEW_HOSTS


CHECK_EMAIL_NOTE = (
    "Almost there — we sent a confirmation link to {email}. Confirm your email, "
    "then sign in to explore more."
)


MIN_REGISTRATION_AGE = 16


def normalized_name(raw: str) -> str:
    """Trimmed name with runs of whitespace collapsed to single spaces."""
    return " ".join((raw or "").split())


def compose_display_name(first_name: str, family_name: str) -> str:
    """Public display name: `First Family` with single spacing."""
    return normalized_name(f"{first_name} {family_name}")


def parse_birth_parts(
    day: str, month: str, year: str
) -> tuple[datetime.date | None, str]:
    """Combine three required birth-date parts into a validated date.

    Rejects missing/non-numeric parts, impossible calendar dates, future dates
    and registrants younger than 16. Independently testable and never raises.
    """
    parts = [(day or "").strip(), (month or "").strip(), (year or "").strip()]
    if not all(parts):
        return None, "Please add your full date of birth."
    if not all(part.isdigit() for part in parts):
        return None, "Use numbers only for your date of birth."
    day_value, month_value, year_value = (int(part) for part in parts)
    if len(parts[2]) != 4 or year_value < 1900:
        return None, "Enter your birth year as four digits."
    try:
        born = datetime.date(year_value, month_value, day_value)
    except ValueError:
        return None, "That date of birth doesn't exist on the calendar."
    return validate_birth_date(born)


def validate_birth_date(
    born: datetime.date,
) -> tuple[datetime.date | None, str]:
    """Reject future dates and under-16 registrants (accurate calendar age)."""
    today = datetime.date.today()
    if born > today:
        return None, "That date of birth is in the future."
    age = (
        today.year
        - born.year
        - ((today.month, today.day) < (born.month, born.day))
    )
    if age < MIN_REGISTRATION_AGE:
        return None, "You need to be at least 16 to join Go and Help."
    return born, ""


def parse_date_of_birth(raw: str) -> tuple[datetime.date | None, str]:
    """Parse an ISO date of birth; returns (date, problem).

    Rejects missing/unparseable values, future dates and registrants who are
    younger than 16 using accurate calendar-date comparison.
    """
    value = (raw or "").strip()
    if not value:
        return None, "Please add your date of birth."
    try:
        born = datetime.date.fromisoformat(value)
    except ValueError:
        return None, "Enter your date of birth as YYYY-MM-DD."
    return validate_birth_date(born)


def hash_password(password: str) -> str:
    return hashlib.sha256(f"skillkind::{password}".encode()).hexdigest()


async def issue_verification_email(
    subscriber_id: int,
    email: str,
    display_name: str,
    router_url: str,
    purpose: str,
) -> tuple[bool, str]:
    """Issue a fresh single-use token and email it. Returns (ok, note).

    Any previously unused token for the subscriber is invalidated first, so only
    the newest link ever works. Delivery failures are recorded on the token row
    and never mark the account verified.
    """
    token, digest = new_verification_token()
    expires = token_expiry()
    try:
        async with rx.asession() as asession:
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
                        INSERT INTO skillkind_email_verification_token
                            (subscriber_id, token_digest, email, purpose,
                             expires_at, send_attempts, last_attempt_at,
                             provider_message_id, last_error, requested_ip,
                             requested_user_agent, consumed_ip)
                        VALUES
                            (:sid, :digest, :email, :purpose, :expires, 1, now(),
                             '', '', '', '', '')
                        RETURNING id
                        """
                    ),
                    {
                        "sid": subscriber_id,
                        "digest": digest,
                        "email": email,
                        "purpose": purpose,
                        "expires": expires,
                    },
                )
            ).first()
            token_id = int(row[0])
            await asession.commit()
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Could not store verification token: {e}")
        return False, "We couldn't start email confirmation just now."

    link = verification_link(token, router_url)
    ok, message_id, error_note = await send_verification_email(
        email, display_name, link
    )
    try:
        async with rx.asession() as asession:
            if ok:
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_email_verification_token
                        SET sent_at = now(), provider_message_id = :mid,
                            last_error = ''
                        WHERE id = :tid
                        """
                    ),
                    {"mid": message_id, "tid": token_id},
                )
            else:
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_email_verification_token
                        SET last_error = :err, invalidated_at = now()
                        WHERE id = :tid
                        """
                    ),
                    {"err": error_note[:255], "tid": token_id},
                )
            await asession.commit()
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Could not record verification send state: {e}")
    if ok:
        return True, ""
    return False, error_note or "We couldn't send the confirmation email."


def password_reset_expiry(
    now: datetime.datetime | None = None,
) -> datetime.datetime:
    moment = now or datetime.datetime.now(datetime.UTC)
    return moment + datetime.timedelta(minutes=PASSWORD_RESET_TOKEN_TTL_MINUTES)


class AuthState(rx.State):
    subscriber_id: str = rx.LocalStorage("", name="goandhelp_sid")
    email: str = ""
    display_name: str = ""
    phone: str = ""
    help_mode: str = "both"
    preferred_language: str = rx.LocalStorage(
        DEFAULT_LANGUAGE, name="goandhelp_interface_language", sync=True
    )
    language_saving: bool = False
    language_error: str = ""

    @rx.var
    def interface_text(self) -> dict[str, str]:
        return catalog(self.preferred_language)

    @rx.var
    def localized_error(self) -> str:
        return translate(self.preferred_language, self.error)

    @rx.var
    def localized_success(self) -> str:
        greeting = f"Good to see you again, {self.display_name}."
        if self.success in (greeting, f"{greeting} {UNVERIFIED_BYPASS_NOTE}"):
            text = translate(
                self.preferred_language, "Good to see you again, {name}."
            ).format(name=self.display_name)
            if self.success.endswith(UNVERIFIED_BYPASS_NOTE):
                text = f"{text} {translate(self.preferred_language, UNVERIFIED_BYPASS_NOTE)}"
            return text
        if self.pending_email and self.success == CHECK_EMAIL_NOTE.format(
            email=self.pending_email
        ):
            return translate(self.preferred_language, CHECK_EMAIL_NOTE).format(
                email=self.pending_email
            )
        return translate(self.preferred_language, self.success)

    @rx.var
    def interface_direction(self) -> str:
        return "rtl" if self.preferred_language in ("ar", "he", "fa") else "ltr"

    joined_label: str = ""
    auth_tab: str = "register"
    # Controlled country calling-code selections (never a credential).
    register_phone_code: str = DEFAULT_PHONE_CODE_VALUE
    signin_phone_code: str = DEFAULT_PHONE_CODE_VALUE
    legal_dialog_open: bool = False
    is_busy: bool = False
    checking_session: bool = True
    error: str = ""
    success: str = ""
    # Email confirmation state (never holds a token or any secret).
    awaiting_verification: bool = False
    pending_email: str = ""
    resend_busy: bool = False
    resend_note: str = ""
    # Non-secret marker: the current session belongs to an unverified account
    # allowed in by the temporary bypass flag above.
    unverified_access: bool = False
    # Read from the database on every session load. `is_verified` means the
    # email address was confirmed — never a real-world identity check.
    is_verified: bool = False
    is_admin: bool = False
    # Password reset request panel (never holds a token or a password).
    forgot_open: bool = False
    forgot_busy: bool = False
    forgot_note: str = ""

    @rx.event
    def open_forgot_password(self):
        self.forgot_open = True
        self.forgot_note = ""
        self.error = ""
        self.success = ""

    @rx.event
    def close_forgot_password(self):
        self.forgot_open = False
        self.forgot_note = ""

    @rx.event(background=True)
    async def request_password_reset(self, form_data: dict[str, Any]):
        """Email a single-use reset link, without revealing whether an
        account exists. Only the SHA-256 digest of the token is stored.
        """
        email = str(form_data.get("reset_email", "") or "").strip().lower()
        async with self:
            router_url = str(self.router.url)
        if not EMAIL_PATTERN.match(email):
            async with self:
                self.forgot_note = "Enter the email address you signed up with."
            return
        async with self:
            self.forgot_busy = True
            self.forgot_note = ""
            self.error = ""

        target: tuple[int, str] | None = None
        throttled = False
        token, digest = new_verification_token()
        expires = password_reset_expiry()
        token_id = 0
        try:
            async with rx.asession() as asession:
                row = (
                    await asession.execute(
                        text(
                            """
                            SELECT id, display_name
                            FROM skillkind_subscriber
                            WHERE email = :email AND is_active = TRUE
                            """
                        ),
                        {"email": email},
                    )
                ).first()
                if row is not None:
                    limits = (
                        await asession.execute(
                            text(
                                """
                                SELECT COUNT(*),
                                       COALESCE(MIN(EXTRACT(EPOCH FROM
                                           (now() - created_at))), 999999)
                                FROM skillkind_password_reset_token
                                WHERE subscriber_id = :sid
                                  AND created_at > now() - INTERVAL '1 day'
                                """
                            ),
                            {"sid": int(row[0])},
                        )
                    ).first()
                    sent_today = int(limits[0] or 0)
                    since_last = float(limits[1] or 999999)
                    if sent_today >= PASSWORD_RESET_MAX_SENDS_PER_DAY or (
                        sent_today > 0
                        and since_last < PASSWORD_RESET_RESEND_COOLDOWN_SECONDS
                    ):
                        throttled = True
                    else:
                        # Retire every live link before issuing a fresh one.
                        await asession.execute(
                            text(
                                """
                                UPDATE skillkind_password_reset_token
                                SET invalidated_at = now()
                                WHERE subscriber_id = :sid
                                  AND used_at IS NULL
                                  AND invalidated_at IS NULL
                                """
                            ),
                            {"sid": int(row[0])},
                        )
                        created = (
                            await asession.execute(
                                text(
                                    """
                                    INSERT INTO skillkind_password_reset_token
                                        (subscriber_id, token_digest, email,
                                         expires_at, send_attempts,
                                         last_attempt_at)
                                    VALUES
                                        (:sid, :digest, :email, :expires, 1,
                                         now())
                                    RETURNING id
                                    """
                                ),
                                {
                                    "sid": int(row[0]),
                                    "digest": digest,
                                    "email": email,
                                    "expires": expires,
                                },
                            )
                        ).first()
                        token_id = int(created[0])
                        await asession.commit()
                        target = (int(row[0]), str(row[1] or ""))
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Password reset request failed: {e}")

        if target is not None:
            link = password_reset_link(token, router_url)
            ok, message_id, error_note = await send_password_reset_email(
                email,
                target[1],
                link,
                PASSWORD_RESET_TOKEN_TTL_MINUTES,
            )
            try:
                async with rx.asession() as asession:
                    if ok:
                        await asession.execute(
                            text(
                                """
                                UPDATE skillkind_password_reset_token
                                SET sent_at = now(), provider_message_id = :mid,
                                    last_error = ''
                                WHERE id = :tid
                                """
                            ),
                            {"mid": message_id, "tid": token_id},
                        )
                    else:
                        await asession.execute(
                            text(
                                """
                                UPDATE skillkind_password_reset_token
                                SET last_error = :err, invalidated_at = now()
                                WHERE id = :tid
                                """
                            ),
                            {"err": error_note[:255], "tid": token_id},
                        )
                    await asession.commit()
            except Exception as e:  # noqa: BLE001
                logging.exception(f"Could not record reset send state: {e}")

        async with self:
            self.forgot_busy = False
            self.forgot_note = (
                RESET_THROTTLED_NOTE if throttled else RESET_GENERIC_NOTE
            )
        yield rx.toast(RESET_GENERIC_NOTE, duration=6000)

    @rx.var
    def is_signed_in(self) -> bool:
        return self.subscriber_id != "" and self.email != ""

    @rx.var
    def is_local_development(self) -> bool:
        """True only for localhost / 127.0.0.1 origins (dev preview affordance)."""
        return is_local_host(str(self.router.url))

    @rx.var
    def mode_label(self) -> str:
        labels = {
            "offer_help": "Offering help",
            "receive_help": "Getting help",
            "both": "Helping & receiving",
        }
        return labels.get(self.help_mode, "Helping & receiving")

    @rx.var
    def language_label(self) -> str:
        return LANGUAGE_LABELS.get(self.preferred_language, "English")

    @rx.var
    def register_dial_prefix(self) -> str:
        """Dial prefix shown over the collapsed registration code select."""
        return dial_prefix(self.register_phone_code) or "+"

    @rx.var
    def signin_dial_prefix(self) -> str:
        """Dial prefix shown over the collapsed sign-in code select."""
        return dial_prefix(self.signin_phone_code) or "+"

    @rx.event
    def set_register_phone_code(self, value: str):
        self.register_phone_code = value

    @rx.event
    def set_signin_phone_code(self, value: str):
        self.signin_phone_code = value

    @rx.event
    def open_legal_dialog(self):
        self.legal_dialog_open = True

    @rx.event
    def close_legal_dialog(self):
        self.legal_dialog_open = False

    @rx.event
    def set_auth_tab(self, tab: str):
        self.auth_tab = tab
        self.legal_dialog_open = False
        self.error = ""
        self.success = ""
        self.resend_note = ""

    @rx.event
    def back_to_sign_in(self):
        self.awaiting_verification = False
        self.auth_tab = "signin"
        self.pending_email = ""
        self.resend_note = ""
        self.error = ""
        self.success = ""
        self.forgot_note = ""
        self.forgot_open = False
        self.legal_dialog_open = False

    @rx.event
    def dismiss_verification_notice(self):
        self.awaiting_verification = False
        self.pending_email = ""
        self.resend_note = ""

    @rx.event(background=True)
    async def resend_verification(self, form_data: dict[str, Any]):
        """Resend a confirmation link with anti-enumeration, cooled-down replies."""
        email = str(form_data.get("email", "") or "").strip().lower()
        async with self:
            fallback = self.pending_email
            router_url = str(self.router.url)
        if not email:
            email = fallback
        if not EMAIL_PATTERN.match(email):
            async with self:
                self.resend_note = "Enter the email address you signed up with."
            return
        async with self:
            self.resend_busy = True
            self.resend_note = ""
            self.error = ""

        target: tuple[int, str] | None = None
        throttled = False
        try:
            async with rx.asession() as asession:
                row = (
                    await asession.execute(
                        text(
                            """
                            SELECT id, display_name
                            FROM skillkind_subscriber
                            WHERE email = :email AND is_active = TRUE
                              AND is_verified = FALSE
                            """
                        ),
                        {"email": email},
                    )
                ).first()
                if row is not None:
                    limits = (
                        await asession.execute(
                            text(
                                """
                                SELECT COUNT(*),
                                       COALESCE(MIN(EXTRACT(EPOCH FROM
                                           (now() - created_at))), 999999)
                                FROM skillkind_email_verification_token
                                WHERE subscriber_id = :sid
                                  AND created_at > now() - INTERVAL '1 day'
                                """
                            ),
                            {"sid": int(row[0])},
                        )
                    ).first()
                    sent_today = int(limits[0] or 0)
                    since_last = float(limits[1] or 999999)
                    if sent_today >= VERIFICATION_MAX_SENDS_PER_DAY or (
                        sent_today > 0
                        and since_last < VERIFICATION_RESEND_COOLDOWN_SECONDS
                    ):
                        throttled = True
                    else:
                        target = (int(row[0]), str(row[1] or ""))
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Resend verification lookup failed: {e}")

        if target is not None:
            ok, note = await issue_verification_email(
                target[0],
                email,
                target[1],
                router_url,
                VERIFICATION_PURPOSE_RESEND,
            )
            if not ok:
                async with self:
                    self.resend_busy = False
                    self.resend_note = note
                async with self:
                    notification = translate(self.preferred_language, note)
                yield rx.toast(notification, duration=5000)
                return

        async with self:
            self.resend_busy = False
            self.awaiting_verification = True
            self.pending_email = email
            self.resend_note = (
                "A confirmation link was requested very recently — please wait a "
                "couple of minutes before asking for another one."
                if throttled
                else RESEND_GENERIC_NOTE
            )
        async with self:
            notification = translate(self.preferred_language, self.resend_note)
        yield rx.toast(notification, duration=5000)

    @rx.event(background=True)
    async def preview_as_local_member(self):
        """Local-development-only signed-in preview.

        Refuses on any non-local host, never writes to the database and never
        marks a subscriber verified. It simply reads one existing active
        subscriber (a verified one when available, otherwise the newest active
        account purely for preview) and populates the same session/profile state
        a successful sign-in would.
        """
        async with self:
            router_url = str(self.router.url)
        if not is_local_host(router_url):
            async with self:
                self.error = LOCAL_PREVIEW_ONLY_NOTE
                self.success = ""
            yield rx.toast(LOCAL_PREVIEW_ONLY_NOTE, duration=5000)
            return
        async with self:
            self.is_busy = True
            self.error = ""
            self.success = ""
        row = None
        try:
            async with rx.asession() as asession:
                row = (
                    await asession.execute(
                        text(
                            """
                            SELECT id, email, display_name, phone, help_mode,
                                   joined_at,
                                   COALESCE(preferred_language, 'en'),
                                   is_verified, is_admin
                            FROM skillkind_subscriber
                            WHERE is_active = TRUE
                            ORDER BY is_verified DESC, id DESC
                            LIMIT 1
                            """
                        )
                    )
                ).first()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Local preview lookup failed: {e}")
        if row is None:
            async with self:
                self.is_busy = False
                self.error = (
                    "No active account exists yet — register one locally first, "
                    "then use the local preview."
                )
            return
        async with self:
            self.subscriber_id = str(int(row[0]))
            self.email = str(row[1])
            self.display_name = str(row[2] or "")
            self.phone = str(row[3] or "")
            self.help_mode = str(row[4] or "both")
            self.joined_label = (
                row[5].strftime("%b %d, %Y") if row[5] is not None else ""
            )
            self.preferred_language = str(row[6] or DEFAULT_LANGUAGE)
            self.is_verified = bool(row[7])
            self.is_admin = bool(row[8])
            self.is_busy = False
            self.checking_session = False
            self.awaiting_verification = False
            self.pending_email = ""
            self.resend_note = ""
            self.error = ""
            self.success = (
                "Local preview only — signed in as "
                f"{row[2] or row[1]} without changing any account."
            )
        yield rx.toast(
            "Local preview only: production email verification is unchanged.",
            duration=4000,
        )
        from app.states.membership_state import MembershipState
        from app.states.profile_state import ProfileState

        yield ProfileState.load_profile
        yield MembershipState.load_membership

    @rx.event(background=True)
    async def load_session(self):
        from app.states.membership_state import MembershipState
        from app.states.onboarding_state import OnboardingState
        from app.states.profile_state import ProfileState

        async with self:
            sid = self.subscriber_id
            self.checking_session = True
        hydrated = False
        try:
            row = None
            if sid.isdigit():
                async with asyncio.timeout(12):
                    async with rx.asession() as asession:
                        row = (
                            await asession.execute(
                                text("""
                                    WITH active AS (
                                        UPDATE skillkind_subscriber
                                        SET last_seen_at = now()
                                        WHERE id = :sid AND is_active = TRUE
                                          AND (is_verified = TRUE OR :allow_unverified)
                                        RETURNING id, email, display_name, phone,
                                                  help_mode, joined_at,
                                                  preferred_language, is_verified, is_admin
                                    )
                                    SELECT s.email, s.display_name, s.phone, s.help_mode,
                                           s.joined_at, COALESCE(s.preferred_language, 'en'),
                                           s.is_verified, s.is_admin, p.subscriber_id,
                                           p.current_step, p.completed_steps, p.answers_json,
                                           p.permissions_json, p.completed_at,
                                           p.tour_current_step, p.tour_completed_at
                                    FROM active s
                                    LEFT JOIN skillkind_onboarding_progress p
                                      ON p.subscriber_id = s.id
                                """),
                                {
                                    "sid": int(sid),
                                    "allow_unverified": ALLOW_UNVERIFIED_SIGN_IN,
                                },
                            )
                        ).first()
                        await asession.commit()
            async with self:
                if self.subscriber_id != sid:
                    return
                onboarding = await self.get_state(OnboardingState)
                if row is not None:
                    onboarding._apply_progress_row(
                        row[9:16] if row[8] is not None else None
                    )
                    self.unverified_access = not bool(row[6])
                    self.is_verified = bool(row[6])
                    self.is_admin = bool(row[7])
                    self.email = str(row[0])
                    self.display_name = str(row[1] or "")
                    self.phone = str(row[2] or "")
                    self.help_mode = str(row[3] or "both")
                    self.joined_label = (
                        row[4].strftime("%b %d, %Y")
                        if row[4] is not None
                        else ""
                    )
                    self.preferred_language = str(row[5] or DEFAULT_LANGUAGE)
                    onboarding.interface_language = self.preferred_language
                    hydrated = True
        except Exception as e:
            logging.exception(f"Could not restore session: {e}")
            async with self:
                self.error = (
                    "We couldn't restore your session. Please sign in again."
                )
        finally:
            async with self:
                if self.subscriber_id == sid and not hydrated:
                    self.subscriber_id = ""
                    self.email = ""
                    self.display_name = ""
                    self.phone = ""
                    self.unverified_access = False
                    self.is_verified = False
                    self.is_admin = False
                    onboarding = await self.get_state(OnboardingState)
                    onboarding._reset()
                    onboarding.progress_loaded = True
                self.checking_session = False
        if hydrated:
            yield ProfileState.load_profile
            yield MembershipState.load_membership

    @rx.event(background=True)
    async def register(self, form_data: dict[str, Any]):
        email = str(form_data.get("email", "") or "").strip().lower()
        first_name = normalized_name(str(form_data.get("first_name", "") or ""))
        family_name = normalized_name(
            str(form_data.get("family_name", "") or "")
        )
        name = compose_display_name(first_name, family_name)
        phone_code = str(form_data.get("phone_code", "") or "").strip()
        phone_number = str(form_data.get("phone_number", "") or "").strip()
        phone = compose_phone(phone_code, phone_number)
        password = str(form_data.get("password", "") or "")
        confirm = str(form_data.get("confirm_password", "") or "")
        mode = HELP_MODE_BOTH if HELP_MODE_BOTH in HELP_MODES else "both"
        async with self:
            language = (
                self.preferred_language
                if self.preferred_language in LANGUAGE_CODES
                else DEFAULT_LANGUAGE
            )
        born, dob_problem = parse_birth_parts(
            str(form_data.get("birth_day", "") or ""),
            str(form_data.get("birth_month", "") or ""),
            str(form_data.get("birth_year", "") or ""),
        )
        problem = ""
        if not first_name:
            problem = "Please add your first name."
        elif not family_name:
            problem = "Please add your family name."
        elif len(first_name) > FIRST_NAME_MAX_LENGTH:
            problem = f"First name must be {FIRST_NAME_MAX_LENGTH} characters or fewer."
        elif len(family_name) > FAMILY_NAME_MAX_LENGTH:
            problem = (
                f"Family name must be {FAMILY_NAME_MAX_LENGTH} characters "
                "or fewer."
            )
        elif not EMAIL_PATTERN.match(email):
            problem = "That email address doesn't look right."
        elif len(password.strip()) < 6 or not confirm.strip():
            problem = "Passwords need at least 6 characters."
        elif password != confirm:
            problem = "The two passwords don't match."
        elif dob_problem:
            problem = dob_problem
        elif phone_code not in PHONE_CODE_VALUES:
            problem = "Please choose your country calling code."
        elif not national_digits(phone_number):
            problem = "Please add your phone number."
        elif not is_plausible_phone_number(phone_number):
            problem = (
                "That phone number doesn't look complete \u2014 enter it without "
                "the country code."
            )
        elif not phone:
            problem = "Please add a valid phone number."
        elif str(form_data.get("terms_consent", "")).strip().lower() not in (
            "accepted",
            "true",
            "on",
            "1",
        ):
            problem = "Please accept the Terms before creating your account."
        if problem:
            async with self:
                self.error = problem
                self.success = ""
            return
        async with self:
            self.is_busy = True
            self.error = ""
            self.success = ""
        new_id = 0
        duplicate_email = False
        try:
            async with rx.asession() as asession:
                new_row = (
                    await asession.execute(
                        text(
                            """
                            INSERT INTO skillkind_subscriber
                                (email, display_name, first_name, family_name,
                                 password_hash, phone,
                                 date_of_birth, help_mode,
                                 preferred_language, is_active, is_admin, is_verified)
                            VALUES
                                (:email, :name, :first_name, :family_name,
                                 :pwd, :phone, :dob, :mode,
                                 :language, TRUE, FALSE, FALSE)
                            ON CONFLICT (email) DO NOTHING
                            RETURNING id, joined_at
                            """
                        ),
                        {
                            "email": email,
                            "name": name,
                            "first_name": first_name,
                            "family_name": family_name,
                            "pwd": hash_password(password),
                            "phone": phone,
                            "dob": born,
                            "mode": mode,
                            "language": language,
                        },
                    )
                ).first()
                if new_row is None:
                    duplicate_email = True
                else:
                    new_id = int(new_row[0])
                    await asession.execute(
                        text(
                            """
                            INSERT INTO skillkind_profile
                                (subscriber_id, headline, bio, avatar_seed, home_city,
                                 home_country, current_city, travel_radius_km, languages,
                                 skills, preferred_categories, availability_note,
                                 helper_rating_avg, helper_rating_count,
                                 traveller_rating_avg, traveller_rating_count,
                                 tasks_helped_count, tasks_received_count, kindness_points)
                            VALUES
                                (:sid, '', '', :seed, '', '', '', 10, '', '', '', '',
                                 0, 0, 0, 0, 0, 0, 0)
                            """
                        ),
                        {"sid": new_id, "seed": f"member-{new_id}"},
                    )
                    await asession.execute(
                        text(
                            """
                            INSERT INTO skillkind_onboarding_progress
                                (subscriber_id, current_step, completed_steps,
                                 answers_json, permissions_json, tour_current_step)
VALUES (:sid, 1, '', :answers, '{}', 0)
                            ON CONFLICT (subscriber_id) DO NOTHING
                            """
                        ),
                        {
                            "sid": new_id,
                            "answers": json.dumps(
                                {"preferred_language": language}
                            ),
                        },
                    )
                    await asession.commit()
        except SQLAlchemyError as e:
            logging.exception(
                f"Error: registration database transaction failed ({type(e).__name__})"
            )
            async with self:
                self.is_busy = False
                self.success = ""
                self.error = "We couldn't create your account right now. Please try again."
            return

        if duplicate_email:
            async with self:
                self.is_busy = False
                self.success = ""
                self.error = (
                    "That email is already on Go and Help — try signing in."
                )
            return
        if ALLOW_UNVERIFIED_SIGN_IN:
            async with self:
                self.subscriber_id = str(new_id)
                self.email = email
                self.display_name = name
                self.phone = phone
                self.help_mode = mode
                self.preferred_language = language
                self.joined_label = datetime.date.today().strftime("%b %d, %Y")
                self.is_admin = False
                self.is_verified = False
                self.unverified_access = True
                self.is_busy = False
                self.checking_session = True
                self.awaiting_verification = False
                self.pending_email = ""
                self.auth_tab = "signin"
                self.legal_dialog_open = False
                self.error = ""
                self.success = "Account created. Temporary access is active while email confirmation remains optional."
            async with self:
                notification = self.localized_success
            yield rx.toast(notification, duration=5000)
            from app.states.onboarding_state import OnboardingState

            async with self:
                onboarding = await self.get_state(OnboardingState)
            async with onboarding:
                await onboarding._resolve_progress(str(new_id), False)
            async with self:
                onboarding = await self.get_state(OnboardingState)
                onboarding.interface_language = self.preferred_language
                self.checking_session = False
            from app.states.membership_state import MembershipState
            from app.states.profile_state import ProfileState

            yield ProfileState.load_profile
            yield MembershipState.load_membership
            return
        async with self:
            router_url = str(self.router.url)
        ok, note = await issue_verification_email(
            new_id, email, name, router_url, VERIFICATION_PURPOSE_SIGNUP
        )
        async with self:
            self.subscriber_id = ""
            self.email = ""
            self.display_name = ""
            self.is_busy = False
            self.checking_session = False
            self.awaiting_verification = True
            self.pending_email = email
            self.auth_tab = "signin"
            self.legal_dialog_open = False
            self.error = ""
            self.success = CHECK_EMAIL_NOTE.format(email=email) if ok else ""
            self.resend_note = ""
        async with self:
            notification = (
                self.localized_success
                if ok
                else translate(self.preferred_language, note)
            )
        yield rx.toast(notification, duration=6000)

    @rx.event(background=True)
    async def sign_in(self, form_data: dict[str, Any]):
        email = str(form_data.get("email", "") or "").strip().lower()
        password = str(form_data.get("password", "") or "")
        # Email and password are the only credentials: no phone value is read.
        if not EMAIL_PATTERN.match(email) or not password:
            async with self:
                self.error = "Enter your email and password to continue."
                self.success = ""
            return
        async with self:
            self.is_busy = True
            self.error = ""
            self.success = ""
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT id, display_name, phone, help_mode, joined_at, password_hash,
                               COALESCE(preferred_language, 'en'), is_verified,
                               is_admin
                        FROM skillkind_subscriber
                        WHERE email = :email AND is_active = TRUE
                        """
                    ),
                    {"email": email},
                )
            ).first()
            if row is None or str(row[5]) != hash_password(password):  # noqa: PLR2004
                async with self:
                    self.is_busy = False
                    self.error = "We couldn't match that email and password."
                return
            if not bool(row[7]) and not ALLOW_UNVERIFIED_SIGN_IN:
                async with self:
                    self.is_busy = False
                    self.awaiting_verification = True
                    self.pending_email = email
                    self.success = ""
                    self.error = (
                        "This email isn't confirmed yet, so the map stays locked. "
                        "Open the link we emailed you, or resend it below."
                    )
                return
            await asession.execute(
                text(
                    "UPDATE skillkind_subscriber SET last_seen_at = now() WHERE id = :sid"
                ),
                {"sid": int(row[0])},
            )
            await asession.commit()
        from app.states.unified_inbox_state import UnifiedInboxState

        async with self:
            unified = await self.get_state(UnifiedInboxState)
            unified._sync_visited_account(str(int(row[0])))
            self.subscriber_id = str(int(row[0]))
            self.email = email
            self.display_name = str(row[1])
            self.phone = str(row[2] or "")
            self.help_mode = str(row[3] or "both")
            self.preferred_language = str(row[6] or DEFAULT_LANGUAGE)
            self.joined_label = (
                row[4].strftime("%b %d, %Y") if row[4] is not None else ""
            )
            self.is_busy = False
            self.checking_session = True
            self.awaiting_verification = False
            self.pending_email = ""
            self.resend_note = ""
            self.unverified_access = not bool(row[7])
            self.is_verified = bool(row[7])
            self.is_admin = bool(row[8])
            self.success = (
                f"Good to see you again, {row[1]}."
                if bool(row[7])
                else f"Good to see you again, {row[1]}. {UNVERIFIED_BYPASS_NOTE}"
            )
        from app.states.onboarding_state import OnboardingState

        async with self:
            onboarding = await self.get_state(OnboardingState)
        try:
            async with onboarding:
                await onboarding._resolve_progress(
                    str(int(row[0])), bool(row[7])
                )
        finally:
            async with self:
                onboarding = await self.get_state(OnboardingState)
                onboarding.interface_language = self.preferred_language
                self.checking_session = False
        from app.states.membership_state import MembershipState
        from app.states.profile_state import ProfileState

        yield ProfileState.load_profile
        yield MembershipState.load_membership

    @rx.event
    async def sign_out(self):
        from app.states.unified_inbox_state import UnifiedInboxState

        unified = await self.get_state(UnifiedInboxState)
        unified.visited_keys = []
        unified.visited_account = ""
        from app.states.membership_state import MembershipState
        from app.states.onboarding_state import OnboardingState
        from app.states.profile_metrics_state import ProfileMetricsState
        from app.states.profile_state import ProfileState

        onboarding = await self.get_state(OnboardingState)
        onboarding._reset()
        profile = await self.get_state(ProfileState)
        profile.clear_profile()
        from app.states.event_state import EventState

        events = await self.get_state(EventState)
        events._check_events_owner("")
        events.events = []
        events.event_markers = []
        events.selected_event = []
        membership = await self.get_state(MembershipState)
        membership._reset()
        metrics = await self.get_state(ProfileMetricsState)
        metrics._reset()
        self.subscriber_id = ""
        self.email = ""
        self.display_name = ""
        self.phone = ""
        self.help_mode = "both"
        self.language_error = ""
        self.joined_label = ""
        self.auth_tab = "register"
        self.register_phone_code = DEFAULT_PHONE_CODE_VALUE
        self.signin_phone_code = DEFAULT_PHONE_CODE_VALUE
        self.legal_dialog_open = False
        self.is_verified = False
        self.is_admin = False
        self.error = ""
        self.success = ""
        self.checking_session = False
        self.awaiting_verification = False
        self.pending_email = ""
        self.resend_note = ""
        self.unverified_access = False

    @rx.event(background=True)
    async def update_help_mode(self, mode: str):
        if mode not in HELP_MODES:
            return
        async with self:
            sid = self.subscriber_id
        if not sid.isdigit():
            return
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    "UPDATE skillkind_subscriber SET help_mode = :mode WHERE id = :sid"
                ),
                {"mode": mode, "sid": int(sid)},
            )
            await asession.commit()
        async with self:
            self.help_mode = mode
        yield rx.toast("Participation mode updated.", duration=2500)

    @rx.event(background=True)
    async def update_language(self, language: str):
        if language not in LANGUAGE_CODES:
            return
        from app.states.onboarding_state import OnboardingState

        async with self:
            if self.language_saving:
                return
            sid = self.subscriber_id
            previous = self.preferred_language
            self.language_saving = True
            self.language_error = ""
            self.preferred_language = language
        try:
            if sid.isdigit():
                async with rx.asession() as session:
                    await session.execute(
                        text(
                            "UPDATE skillkind_subscriber SET preferred_language = :lang WHERE id = :sid"
                        ),
                        {"lang": language, "sid": int(sid)},
                    )
                    await session.execute(
                        text("""
                            UPDATE skillkind_onboarding_progress
                            SET answers_json = (CAST(COALESCE(NULLIF(answers_json, ''), '{}') AS jsonb)
                                || CAST(:patch AS jsonb))::text, updated_at = now()
                            WHERE subscriber_id = :sid
                        """),
                        {
                            "sid": int(sid),
                            "patch": json.dumps(
                                {"preferred_language": language}
                            ),
                        },
                    )
                    await session.commit()
            async with self:
                if self.subscriber_id == sid:
                    onboarding = await self.get_state(OnboardingState)
                    onboarding.interface_language = language
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                if self.subscriber_id == sid:
                    self.preferred_language = previous
                    self.language_error = translate(
                        previous, "Could not save language. Please try again."
                    )
        finally:
            async with self:
                self.language_saving = False
