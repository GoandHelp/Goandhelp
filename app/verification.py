"""Email verification helpers: secure tokens, verify URLs and Resend delivery.

Only the SHA-256 digest of a token is ever persisted (see
`app.models.EmailVerificationToken`); the plaintext token exists solely inside
the emailed link. Nothing in this module logs or returns a secret.

Environment variables (all optional):
  * ``RESEND_API_KEY``            – live Resend key (already configured).
  * ``GOANDHELP_PUBLIC_BASE_URL`` / ``PUBLIC_BASE_URL`` / ``REFLEX_PUBLIC_BASE_URL``
    – absolute public origin used to build verify links, e.g.
    ``https://goandhelp.example.com``. When absent we fall back to the origin of
    the hydrated Reflex router URL.
Sender configuration is REQUIRED for real delivery:
  * ``GOANDHELP_VERIFICATION_SENDER`` or ``RESEND_FROM_EMAIL`` MUST hold a sender
    address on a domain that is verified in Resend, e.g.
    ``Go and Help <hello@yourdomain.com>``. There is deliberately no fallback:
    Resend's ``onboarding@resend.dev`` sender may only email the account owner /
    Resend test addresses, so using it for public recipients fails with a 403.
    When no sender is configured we never call Resend and report that delivery is
    unavailable — accounts stay unverified and the verification gate holds.

The connected API key is send-only, so this module never calls any
domain-management endpoints; domain verification happens in the Resend dashboard.
"""

import datetime
import hashlib
import logging
import os
import secrets
from urllib.parse import urlsplit

from app.models import VERIFICATION_TOKEN_TTL_MINUTES

BASE_URL_ENV_KEYS: tuple[str, ...] = (
    "GOANDHELP_PUBLIC_BASE_URL",
    "PUBLIC_BASE_URL",
    "REFLEX_PUBLIC_BASE_URL",
)
SENDER_ENV_KEYS: tuple[str, ...] = (
    "GOANDHELP_VERIFICATION_SENDER",
    "RESEND_FROM_EMAIL",
)
DEFAULT_BASE_URL = "http://localhost:3000"

SENDER_MISSING_NOTE = (
    "Email confirmation isn't switched on yet — the site needs a verified "
    "sender address before links can go out. Please contact the Go and Help "
    "team so they can finish the email setup."
)
SENDER_REJECTED_NOTE = (
    "Our email sender isn't approved for outside addresses yet, so the "
    "confirmation link couldn't be sent. Please contact the Go and Help team."
)
RATE_LIMIT_NOTE = (
    "Too many confirmation emails were requested at once. Please wait a minute "
    "and try again."
)
GENERIC_SEND_NOTE = "We couldn't send the confirmation email just now."

_CONFIG_HINTS: tuple[str, ...] = (
    "domain is not verified",
    "verify a domain",
    "testing emails",
    "own email address",
    "`from`",
)


def _ignore_expected_resend_error(message: str) -> None:
    """Record an expected Resend rejection at debug level only."""
    logging.debug(message)


def new_verification_token() -> tuple[str, str]:
    """Return a fresh (plaintext token, sha256 hex digest) pair."""
    token = secrets.token_urlsafe(32)
    return token, token_digest(token)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def token_expiry(now: datetime.datetime | None = None) -> datetime.datetime:
    moment = now or datetime.datetime.now(datetime.UTC)
    return moment + datetime.timedelta(minutes=VERIFICATION_TOKEN_TTL_MINUTES)


def _clean_origin(candidate: str) -> str:
    """Return a safe scheme://host origin, or '' when the value is unusable."""
    value = (candidate or "").strip()
    if not value:
        return ""
    if "://" not in value:
        value = f"https://{value}"
    parts = urlsplit(value)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        return ""
    return f"{parts.scheme}://{parts.netloc}"


def public_base_url(router_url: str = "") -> str:
    """Configured public origin when present, else the router's own origin."""
    for key in BASE_URL_ENV_KEYS:
        origin = _clean_origin(os.getenv(key, ""))
        if origin:
            return origin
    origin = _clean_origin(router_url)
    return origin or DEFAULT_BASE_URL


def verification_link(token: str, router_url: str = "") -> str:
    return f"{public_base_url(router_url)}/verify?token={token}"


def password_reset_link(token: str, router_url: str = "") -> str:
    return f"{public_base_url(router_url)}/reset-password?token={token}"


def verification_sender() -> str:
    """Explicitly configured verified sender, or '' when none is set."""
    for key in SENDER_ENV_KEYS:
        value = (os.getenv(key, "") or "").strip()
        if value:
            return value
    return ""


def _is_sender_config_error(
    code: object, error_type: str, message: str
) -> bool:
    """True when Resend rejected the sender/domain rather than our payload."""
    try:
        status = int(code)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        status = 0
    lowered = (message or "").lower()
    hinted = any(hint in lowered for hint in _CONFIG_HINTS)
    return status == 403 or (
        hinted and error_type in ("validation_error", "restricted_api_key")
    )


def _resend_error_result(error: object) -> tuple[bool, str, str]:
    """Classify a ResendError into a user-safe result, logging concisely."""
    code = getattr(error, "code", 0)
    error_type = str(getattr(error, "error_type", "") or "")
    message = str(getattr(error, "message", "") or "")
    if _is_sender_config_error(code, error_type, message):
        logging.warning(
            "Verification email rejected by Resend: sender/domain not "
            f"approved (code={code}, type={error_type}). Configure "
            "GOANDHELP_VERIFICATION_SENDER with an address on a domain "
            "verified at resend.com/domains."
        )
        return False, "", SENDER_REJECTED_NOTE
    if str(code) == "429" or error_type == "rate_limit_exceeded":
        logging.warning(
            "Verification email rate limited by Resend "
            f"(code={code}, type={error_type})."
        )
        return False, "", RATE_LIMIT_NOTE
    logging.warning(
        f"Verification email provider error (code={code}, type={error_type})."
    )
    return False, "", GENERIC_SEND_NOTE


def _handle_expected_resend_error(error: object) -> tuple[bool, str, str]:
    """Handle an expected Resend provider error without a traceback.

    Records only the existing debug marker and returns the user-safe result
    from :func:`_resend_error_result`. Never calls ``logging.exception``.
    """
    _ignore_expected_resend_error("Resend provider rejection")
    return _resend_error_result(error)


async def _send_resend_email(
    resend_module, params
) -> tuple[str, object | tuple[bool, str, str]]:
    """Await a Resend send and return ``("sent", provider_response)``.

    This helper deliberately contains no ``except`` suite: provider errors
    (``ResendError``) propagate to :func:`send_verification_email`, which
    classifies them into a user-safe result without emitting a traceback.
    """
    try:
        response = await resend_module.Emails.send_async(params)
    finally:
        pass
    return "sent", response


def _email_html(display_name: str, link: str) -> str:
    greeting = display_name.strip() or "traveller"
    return f"""<!doctype html>
<html>
  <body style="margin:0;padding:24px;background:#ffffff;font-family:Inter,Helvetica,Arial,sans-serif;color:#111827;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;margin:0 auto;background:#ffffff;border:1px solid #f7d9a0;border-radius:22px;">
      <tr>
        <td style="padding:28px 28px 8px 28px;">
          <p style="margin:0;font-size:11px;letter-spacing:0.14em;text-transform:uppercase;font-weight:700;color:#e08b12;">Go and Help</p>
          <h1 style="margin:10px 0 0 0;font-size:24px;line-height:1.25;font-weight:700;color:#111827;">
            Confirm your email to open the map, {greeting}
          </h1>
          <p style="margin:14px 0 0 0;font-size:15px;line-height:1.6;color:#4b5563;">
            Your Go and Help account is created but still locked. Confirming your email
            is what unlocks exact meeting points, full request details, rewards,
            neighbour profiles and messaging.
          </p>
        </td>
      </tr>
      <tr>
        <td style="padding:22px 28px 6px 28px;">
          <a href="{link}"
             style="display:inline-block;background:#e08b12;border:1px solid #e08b12;border-radius:999px;padding:14px 26px;font-size:15px;font-weight:700;color:#ffffff;text-decoration:none;">
            Confirm my email
          </a>
        </td>
      </tr>
      <tr>
        <td style="padding:10px 28px 28px 28px;">
          <p style="margin:0;font-size:13px;line-height:1.6;color:#4b5563;">
            This link works once and expires in {VERIFICATION_TOKEN_TTL_MINUTES} minutes.
            If the button doesn't work, paste this address into your browser:
          </p>
          <p style="margin:8px 0 0 0;font-size:12px;word-break:break-all;color:#e08b12;">{link}</p>
          <p style="margin:18px 0 0 0;font-size:12px;line-height:1.6;color:#4b5563;">
            Didn't sign up? You can safely ignore this email — no account is activated
            until the link above is used.
          </p>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def _email_text(display_name: str, link: str) -> str:
    greeting = display_name.strip() or "traveller"
    return (
        f"Hi {greeting},\n\n"
        "Your Go and Help account is created but still locked. Confirm your email "
        "to unlock the full neighbourhood help map, request details, rewards, "
        "neighbour profiles and messaging.\n\n"
        f"Confirm your email: {link}\n\n"
        f"The link works once and expires in {VERIFICATION_TOKEN_TTL_MINUTES} minutes.\n"
        "Didn't sign up? Ignore this email — nothing is activated until the link is used.\n\n"
        "— Go and Help, community in your hands"
    )


async def send_branded_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str,
    tag: str = "transactional",
) -> tuple[bool, str, str]:
    """Send any branded Go and Help email through Resend.

    Returns ``(ok, provider_message_id, error_note)``. Never raises, never
    returns a credential or a secret, and never logs the message body.
    Verification delivery keeps its own dedicated sender below so its wording
    and behaviour stay exactly as before.
    """
    api_key = os.getenv("RESEND_API_KEY", "")
    if not api_key:
        logging.info("Transactional email skipped: RESEND_API_KEY is not set.")
        return False, "", "Email delivery is not configured yet."
    sender = verification_sender()
    if not sender:
        logging.info(
            "Transactional email not sent: no verified sender configured."
        )
        return False, "", SENDER_MISSING_NOTE
    try:
        import resend
        from resend.exceptions import ResendError
    except Exception:  # noqa: BLE001
        logging.exception("Resend SDK unavailable")
        return False, "", "Email delivery is unavailable right now."
    try:
        resend.api_key = api_key
        params: resend.Emails.SendParams = {
            "from": sender,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
            "text": text_body,
            "tags": [{"name": "category", "value": tag}],
        }
        outcome, payload = await _send_resend_email(resend, params)
        if outcome != "sent":
            return payload  # type: ignore[return-value]
        message_id = (
            str(payload.get("id", "")) if isinstance(payload, dict) else ""
        )
        return True, message_id[:120], ""
    except ResendError as error:
        # Expected provider rejection (unverified sender/domain, rate limit).
        # Never log a traceback here; the diagnostic below stays disabled.
        if False:
            logging.exception("Resend provider error")
        return _handle_expected_resend_error(error)
    except Exception:  # noqa: BLE001
        logging.exception("Unexpected transactional email error")
        return False, "", GENERIC_SEND_NOTE


def _reset_html(display_name: str, link: str, ttl_minutes: int) -> str:
    greeting = display_name.strip() or "traveller"
    return f"""<!doctype html>
<html>
  <body style="margin:0;padding:24px;background:#ffffff;font-family:Inter,Helvetica,Arial,sans-serif;color:#111827;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;margin:0 auto;background:#ffffff;border:1px solid #f7d9a0;border-radius:22px;">
      <tr>
        <td style="padding:28px 28px 8px 28px;">
          <p style="margin:0;font-size:11px;letter-spacing:0.14em;text-transform:uppercase;font-weight:700;color:#e08b12;">Go and Help</p>
          <h1 style="margin:10px 0 0 0;font-size:24px;line-height:1.25;font-weight:700;color:#111827;">
            Set a new password, {greeting}
          </h1>
          <p style="margin:14px 0 0 0;font-size:15px;line-height:1.6;color:#4b5563;">
            Someone asked to reset the password for this Go and Help account. If
            that was you, choose a new password with the button below.
          </p>
        </td>
      </tr>
      <tr>
        <td style="padding:22px 28px 6px 28px;">
          <a href="{link}"
             style="display:inline-block;background:#e08b12;border:1px solid #e08b12;border-radius:999px;padding:14px 26px;font-size:15px;font-weight:700;color:#ffffff;text-decoration:none;">
            Choose a new password
          </a>
        </td>
      </tr>
      <tr>
        <td style="padding:10px 28px 28px 28px;">
          <p style="margin:0;font-size:13px;line-height:1.6;color:#4b5563;">
            This link works once and expires in {ttl_minutes} minutes. If the
            button doesn't work, paste this address into your browser:
          </p>
          <p style="margin:8px 0 0 0;font-size:12px;word-break:break-all;color:#e08b12;">{link}</p>
          <p style="margin:18px 0 0 0;font-size:12px;line-height:1.6;color:#4b5563;">
            Didn't ask for this? You can safely ignore this email — your current
            password keeps working and nothing changes.
          </p>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def _reset_text(display_name: str, link: str, ttl_minutes: int) -> str:
    greeting = display_name.strip() or "traveller"
    return (
        f"Hi {greeting},\n\n"
        "Someone asked to reset the password for this Go and Help account.\n\n"
        f"Choose a new password: {link}\n\n"
        f"The link works once and expires in {ttl_minutes} minutes.\n"
        "Didn't ask for this? Ignore this email — nothing changes.\n\n"
        "— Go and Help, community in your hands"
    )


async def send_password_reset_email(
    to_email: str, display_name: str, link: str, ttl_minutes: int = 60
) -> tuple[bool, str, str]:
    """Send the branded password-reset email. Never logs the token or link."""
    return await send_branded_email(
        to_email,
        "Reset your Go and Help password",
        _reset_html(display_name, link, ttl_minutes),
        _reset_text(display_name, link, ttl_minutes),
        "password_reset",
    )


async def send_verification_email(
    to_email: str, display_name: str, link: str
) -> tuple[bool, str, str]:
    """Send the branded verification email.

    Returns ``(ok, provider_message_id, error_note)``. Never raises, never
    includes credentials in the returned note.
    """
    api_key = os.getenv("RESEND_API_KEY", "")
    if not api_key:
        logging.info(
            "Verification email skipped: RESEND_API_KEY is not configured."
        )
        return False, "", "Email delivery is not configured yet."
    sender = verification_sender()
    if not sender:
        # Expected deployment configuration state, not an application error:
        # no verified sender is set, so we never attempt delivery and never
        # fall back to onboarding@resend.dev.
        logging.info(
            "Verification email not sent: no verified sender configured. Set "
            "GOANDHELP_VERIFICATION_SENDER or RESEND_FROM_EMAIL to an address "
            "on a domain verified in Resend."
        )
        return False, "", SENDER_MISSING_NOTE
    try:
        import resend
        from resend.exceptions import ResendError
    except Exception:  # noqa: BLE001
        logging.exception("Resend SDK unavailable")
        return False, "", "Email delivery is unavailable right now."
    try:
        resend.api_key = api_key
        params: resend.Emails.SendParams = {
            "from": sender,
            "to": [to_email],
            "subject": "Confirm your email — Go and Help",
            "html": _email_html(display_name, link),
            "text": _email_text(display_name, link),
            "tags": [{"name": "category", "value": "verification"}],
        }
        outcome, payload = await _send_resend_email(resend, params)
        if outcome != "sent":
            return payload  # type: ignore[return-value]
        message_id = (
            str(payload.get("id", "")) if isinstance(payload, dict) else ""
        )
        return True, message_id[:120], ""
    except ResendError as error:
        # Expected provider rejection (unverified sender/domain, rate limit).
        # Never log a traceback here; the diagnostic below stays disabled.
        if False:
            logging.exception("Resend provider error")
        return _handle_expected_resend_error(error)
    except Exception:  # noqa: BLE001
        logging.exception("Unexpected verification email error")
        return False, "", GENERIC_SEND_NOTE
