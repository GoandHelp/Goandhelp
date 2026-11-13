"""Go and Help persistent data models.

Schema-only definitions for the travel help marketplace: subscribers, profiles,
help posts, job applications/acceptances, message threads, completed tasks and
reciprocal reviews. No UI queries these tables yet.
"""

import reflex as rx

import datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text as sa_text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    pass


# ---------------------------------------------------------------------------
# Domain vocabularies (kept as plain string constants so migrations stay simple)
# ---------------------------------------------------------------------------

HELP_MODE_OFFER = "offer_help"
HELP_MODE_RECEIVE = "receive_help"
HELP_MODE_BOTH = "both"
HELP_MODES: list[str] = [HELP_MODE_OFFER, HELP_MODE_RECEIVE, HELP_MODE_BOTH]

CATEGORY_OTHER = "other"

# Canonical shared job taxonomy. Keys are stable lowercase tokens; display
# choices may be alphabetized independently of stored selection order.
# Legacy tokens are resolved through LEGACY_CATEGORY_ALIASES on read only.
TASK_CATEGORIES: list[str] = [
    "translator",
    "first_aid",
    "arts",
    "agriculture",
    "carer",
    "construction",
    "cook",
    "cleaner",
    "craftwork",
    "healthcare",
    "labour",
    "legal",
    "mechanic",
    "media",
    "music",
    "sales",
    "spirituality",
    "sports",
    "teaching",
    "technician",
    "tourism",
    "workshop",
    CATEGORY_OTHER,
]

CATEGORY_LABELS: dict[str, str] = {
    "translator": "Translator",
    "first_aid": "First-aid",
    "arts": "Arts",
    "agriculture": "Agriculture",
    "carer": "Carer",
    "construction": "Construction",
    "cook": "Cook",
    "cleaner": "Cleaner",
    "craftwork": "Craftwork",
    "healthcare": "Healthcare",
    "labour": "Labour",
    "legal": "Legal",
    "mechanic": "Mechanic",
    "media": "Media",
    "music": "Music",
    "sales": "Sales",
    "spirituality": "Spirituality",
    "sports": "Sports",
    "teaching": "Teaching",
    "technician": "Technician",
    "tourism": "Tourism",
    "workshop": "Workshop",
    CATEGORY_OTHER: "Other",
}

CATEGORY_ICONS: dict[str, str] = {
    "translator": "languages",
    "first_aid": "briefcase-medical",
    "arts": "palette",
    "agriculture": "sprout",
    "carer": "hand-heart",
    "construction": "hard-hat",
    "cook": "cooking-pot",
    "cleaner": "brush",
    "craftwork": "hammer",
    "healthcare": "heart-pulse",
    "labour": "package",
    "legal": "scale",
    "mechanic": "car",
    "media": "camera",
    "music": "music",
    "sales": "shopping-bag",
    "spirituality": "sparkles",
    "sports": "dumbbell",
    "teaching": "graduation-cap",
    "technician": "cpu",
    "tourism": "map",
    "workshop": "wrench",
    CATEGORY_OTHER: "hand-helping",
}

# Legacy stored token -> current canonical key. Old help posts and profiles keep
# their original values in the database; every read path resolves them here so
# they still filter and display sensibly.
LEGACY_CATEGORY_ALIASES: dict[str, str] = {
    "translation": "translator",
    "translator": "translator",
    "first-aid": "first_aid",
    "first aid": "first_aid",
    "first_aid": "first_aid",
    "artist": "arts",
    "babysitter": "carer",
    "nanny": "carer",
    "builder": "construction",
    "craftworker": "craftwork",
    "health_worker": "healthcare",
    "labourer": "labour",
    "teacher": "teaching",
    "services": CATEGORY_OTHER,
    "coach": "sports",
    "fitness": "sports",
}

# ---------------------------------------------------------------------------
# Help duration vocabulary (`HelpPost.duration_minutes`)
# ---------------------------------------------------------------------------

# 0 means "Any" and is a perfectly valid stored value.
HELP_DURATION_CHOICES: list[tuple[int, str]] = [
    (0, "Any"),
    (15, "15 min"),
    (30, "30 min"),
    (60, "1 hour"),
    (120, "2 hours"),
    (180, "3 hours"),
    (240, "4 hours"),
    (300, "5 hours"),
    (360, "6 hours"),
    (420, "7 hours"),
    (1440, "1 day"),
]

HELP_DURATION_LABELS: dict[int, str] = {
    minutes: label for minutes, label in HELP_DURATION_CHOICES
}

HELP_DURATION_VALUES: list[str] = [
    str(minutes) for minutes, _ in HELP_DURATION_CHOICES
]

HELP_DURATION_OPTIONS: list[dict[str, str]] = [
    {"value": str(minutes), "label": label}
    for minutes, label in HELP_DURATION_CHOICES
]

DEFAULT_HELP_DURATION_MINUTES = 60


def help_duration_label(minutes: int) -> str:
    """Readable duration; zero means the duration still needs agreement."""
    safe = max(int(minutes or 0), 0)
    if safe <= 0:
        return "Duration to be agreed / quoted"
    if safe in HELP_DURATION_LABELS:
        return HELP_DURATION_LABELS[safe]
    if safe % 60 == 0:
        hours = safe // 60
        return "1 hour" if hours == 1 else f"{hours} hours"
    return f"{safe} min"


LANGUAGE_OPTIONS: list[tuple[str, str]] = [
    ("am", "Amharic"),
    ("ar", "Arabic"),
    ("bn", "Bengali"),
    ("my", "Burmese"),
    ("zh", "Chinese"),
    ("cs", "Czech"),
    ("da", "Danish"),
    ("nl", "Dutch"),
    ("en", "English"),
    ("fi", "Finnish"),
    ("fr", "French"),
    ("de", "German"),
    ("el", "Greek"),
    ("gu", "Gujarati"),
    ("he", "Hebrew"),
    ("hi", "Hindi"),
    ("hu", "Hungarian"),
    ("id", "Indonesian"),
    ("it", "Italian"),
    ("ja", "Japanese"),
    ("kn", "Kannada"),
    ("ko", "Korean"),
    ("ml", "Malayalam"),
    ("mr", "Marathi"),
    ("ne", "Nepali"),
    ("fa", "Persian"),
    ("pl", "Polish"),
    ("pt", "Portuguese"),
    ("ro", "Romanian"),
    ("es", "Spanish"),
    ("sw", "Swahili"),
    ("sv", "Swedish"),
    ("ta", "Tamil"),
    ("te", "Telugu"),
    ("th", "Thai"),
    ("tr", "Turkish"),
    ("vi", "Vietnamese"),
]

LANGUAGE_LABELS: dict[str, str] = {
    code: label for code, label in LANGUAGE_OPTIONS
}
LANGUAGE_CODES: list[str] = [code for code, _ in LANGUAGE_OPTIONS]
DEFAULT_LANGUAGE = "en"

REWARD_TYPES: list[str] = [
    "cash",
    "meal",
    "coffee",
    "local_tour",
    "skill_swap",
    "gift",
    "gratitude_only",
    "custom",
]

POST_STATUS_OPEN = "open"
POST_STATUS_MATCHED = "matched"
POST_STATUS_COMPLETED = "completed"
POST_STATUS_CANCELLED = "cancelled"
POST_STATUS_EXPIRED = "expired"
POST_STATUSES: list[str] = [
    POST_STATUS_OPEN,
    POST_STATUS_MATCHED,
    POST_STATUS_COMPLETED,
    POST_STATUS_CANCELLED,
    POST_STATUS_EXPIRED,
]
POST_STATUS_LABELS: dict[str, str] = {
    POST_STATUS_OPEN: "Open",
    POST_STATUS_MATCHED: "Confirmed",
    POST_STATUS_COMPLETED: "Completed",
    POST_STATUS_CANCELLED: "Cancelled",
    POST_STATUS_EXPIRED: "Expired",
}

APPLICATION_PENDING = "pending"
APPLICATION_ACCEPTED = "accepted"
APPLICATION_DECLINED = "declined"
APPLICATION_WITHDRAWN = "withdrawn"
APPLICATION_STATUSES: list[str] = [
    APPLICATION_PENDING,
    APPLICATION_ACCEPTED,
    APPLICATION_DECLINED,
    APPLICATION_WITHDRAWN,
]

APPLICATION_REQUEST_HELPER_OFFER = "helper_offer"
APPLICATION_REQUEST_DIRECT_HELP = "direct_help_request"
APPLICATION_REQUEST_TYPES: list[str] = [
    APPLICATION_REQUEST_HELPER_OFFER,
    APPLICATION_REQUEST_DIRECT_HELP,
]
_APPLICATION_REQUEST_TYPES_SQL = ", ".join(
    f"'{request_type}'" for request_type in APPLICATION_REQUEST_TYPES
)

CANCELLATION_PROPOSAL_PENDING = "pending"
CANCELLATION_PROPOSAL_ACCEPTED = "accepted"
CANCELLATION_PROPOSAL_DECLINED = "declined"
CANCELLATION_PROPOSAL_STATUSES: list[str] = [
    CANCELLATION_PROPOSAL_PENDING,
    CANCELLATION_PROPOSAL_ACCEPTED,
    CANCELLATION_PROPOSAL_DECLINED,
]
CANCELLATION_PROPOSAL_STATUS_LABELS: dict[str, str] = {
    CANCELLATION_PROPOSAL_PENDING: "Awaiting response",
    CANCELLATION_PROPOSAL_ACCEPTED: "Cancellation confirmed",
    CANCELLATION_PROPOSAL_DECLINED: "Cancellation declined",
}
_CANCELLATION_PROPOSAL_STATUSES_SQL = ", ".join(
    f"'{status}'" for status in CANCELLATION_PROPOSAL_STATUSES
)

# Two-party rescheduling of an accepted job application.
SCHEDULE_PROPOSAL_PENDING = "pending"
SCHEDULE_PROPOSAL_ACCEPTED = "accepted"
SCHEDULE_PROPOSAL_DECLINED = "declined"
SCHEDULE_PROPOSAL_SUPERSEDED = "superseded"
SCHEDULE_PROPOSAL_STATUSES: list[str] = [
    SCHEDULE_PROPOSAL_PENDING,
    SCHEDULE_PROPOSAL_ACCEPTED,
    SCHEDULE_PROPOSAL_DECLINED,
    SCHEDULE_PROPOSAL_SUPERSEDED,
]
SCHEDULE_PROPOSAL_STATUS_LABELS: dict[str, str] = {
    SCHEDULE_PROPOSAL_PENDING: "Awaiting response",
    SCHEDULE_PROPOSAL_ACCEPTED: "Confirmed",
    SCHEDULE_PROPOSAL_DECLINED: "Declined",
    SCHEDULE_PROPOSAL_SUPERSEDED: "Replaced",
}
_SCHEDULE_PROPOSAL_STATUSES_SQL = ", ".join(
    f"'{status}'" for status in SCHEDULE_PROPOSAL_STATUSES
)

CONTACT_PENDING = "pending"
CONTACT_ACCEPTED = "accepted"
CONTACT_DECLINED = "declined"
CONTACT_REMOVED = "removed"
CONTACT_STATUSES: list[str] = [
    CONTACT_PENDING,
    CONTACT_ACCEPTED,
    CONTACT_DECLINED,
    CONTACT_REMOVED,
]

CONTACT_STATUS_LABELS: dict[str, str] = {
    CONTACT_PENDING: "Request pending",
    CONTACT_ACCEPTED: "Contacts",
    CONTACT_DECLINED: "Request declined",
    CONTACT_REMOVED: "Contact removed",
}

REVIEW_POSTER_TO_HELPER = "poster_to_helper"
REVIEW_HELPER_TO_POSTER = "helper_to_poster"
REVIEW_DIRECTIONS: list[str] = [
    REVIEW_POSTER_TO_HELPER,
    REVIEW_HELPER_TO_POSTER,
]

URGENCY_LEVELS: list[str] = ["flexible", "soon", "urgent"]

# ---------------------------------------------------------------------------
# Profile location sharing modes
# ---------------------------------------------------------------------------

# `hidden`: never shown on any map (the safe default for existing members).
# `approximate`: replaces the legacy `fixed` mode. The stored latitude and
#   longitude remain the PRIVATE exact source coordinates; public and guest maps
#   must only ever render a land-safe offset derived from them.
# `live`: the pin follows the device location whenever it is refreshed (still
#   published to others only as an approximate point).
LOCATION_MODE_HIDDEN = "hidden"
LOCATION_MODE_APPROXIMATE = "approximate"
LOCATION_MODE_LIVE = "live"
LOCATION_MODES: list[str] = [
    LOCATION_MODE_HIDDEN,
    LOCATION_MODE_APPROXIMATE,
    LOCATION_MODE_LIVE,
]
# Modes that make a member visible on maps and in people search results.
# `Profile.show_location` stays as compatibility state and is true exactly for
# these modes.
VISIBLE_LOCATION_MODES: list[str] = [
    LOCATION_MODE_APPROXIMATE,
    LOCATION_MODE_LIVE,
]
DEFAULT_LOCATION_MODE = LOCATION_MODE_HIDDEN

LOCATION_MODE_LABELS: dict[str, str] = {
    LOCATION_MODE_HIDDEN: "Hidden",
    LOCATION_MODE_APPROXIMATE: "Approximate area",
    LOCATION_MODE_LIVE: "Live location",
}

LOCATION_MODE_DESCRIPTIONS: dict[str, str] = {
    LOCATION_MODE_HIDDEN: (
        "You stay off every map. Only the details you write in your profile "
        "are visible."
    ),
    LOCATION_MODE_APPROXIMATE: (
        "Members see a nearby area rather than your exact address, and it "
        "stays put until you move it yourself."
    ),
    LOCATION_MODE_LIVE: (
        "Your approximate area follows your device location each time you "
        "refresh it."
    ),
}

LOCATION_MODE_ICONS: dict[str, str] = {
    LOCATION_MODE_HIDDEN: "eye-off",
    LOCATION_MODE_APPROXIMATE: "circle-dot",
    LOCATION_MODE_LIVE: "locate-fixed",
}

# SQL literal list used by the profile location mode check constraint.
_LOCATION_MODES_SQL = ", ".join(f"'{mode}'" for mode in LOCATION_MODES)

# ---------------------------------------------------------------------------
# Help post (job) location modes
# ---------------------------------------------------------------------------

# `approximate`: the public request only ever reveals a nearby area. The exact
#   meeting address is supplied privately once a helper is accepted, via the
#   `accepted_*` columns on HelpPost.
# `place`: the request is about a public place (a business, venue or landmark)
#   so its address is safe to publish from the start.
JOB_LOCATION_MODE_APPROXIMATE = "approximate"
JOB_LOCATION_MODE_PLACE = "place"
JOB_LOCATION_MODES: list[str] = [
    JOB_LOCATION_MODE_APPROXIMATE,
    JOB_LOCATION_MODE_PLACE,
]
DEFAULT_JOB_LOCATION_MODE = JOB_LOCATION_MODE_APPROXIMATE

JOB_LOCATION_MODE_LABELS: dict[str, str] = {
    JOB_LOCATION_MODE_APPROXIMATE: "Approximate area",
    JOB_LOCATION_MODE_PLACE: "Public place",
}

JOB_LOCATION_MODE_DESCRIPTIONS: dict[str, str] = {
    JOB_LOCATION_MODE_APPROXIMATE: (
        "Show a nearby area publicly. Share the exact meeting address only "
        "with the helper you accept."
    ),
    JOB_LOCATION_MODE_PLACE: (
        "This job is at a public place, so its address can be shown to "
        "everyone."
    ),
}

JOB_LOCATION_MODE_ICONS: dict[str, str] = {
    JOB_LOCATION_MODE_APPROXIMATE: "circle-dot",
    JOB_LOCATION_MODE_PLACE: "map-pin",
}

# SQL literal list used by the help post location mode check constraint.
_JOB_LOCATION_MODES_SQL = ", ".join(f"'{mode}'" for mode in JOB_LOCATION_MODES)

# Exact meeting address, only revealed to the poster and the accepted helper.
ACCEPTED_LOCATION_NAME_MAX_LENGTH = 200

# Structured profile address parts (private detail used by the location editor).
ADDRESS_ROAD_MAX_LENGTH = 200
ADDRESS_TOWN_MAX_LENGTH = 120
ADDRESS_POSTCODE_MAX_LENGTH = 32

# Public profile handle rules (validated in app code, enforced in the schema by
# length plus a partial unique index that ignores the empty migration default).
USERNAME_MAX_LENGTH = 40
NATIONALITY_MAX_LENGTH = 120
# Personal name parts collected at registration (kept separate from the
# composed public `display_name`).
FIRST_NAME_MAX_LENGTH = 80
FAMILY_NAME_MAX_LENGTH = 80
AVATAR_PATH_MAX_LENGTH = 1024

# Reviews score four categories from 1 to 5; `Review.rating` keeps the rounded
# average of the four so existing aggregate logic stays valid.
REVIEW_CATEGORY_FIELDS: list[str] = [
    "category_one",
    "category_two",
    "category_three",
    "category_four",
]
# Both directions follow the review form's category_one..four order.
REVIEW_POSTER_CATEGORY_LABELS: list[str] = [
    "Timeliness",
    "Work ethic",
    "Skill",
    "Friendliness",
]
REVIEW_HELPER_CATEGORY_LABELS: list[str] = REVIEW_POSTER_CATEGORY_LABELS.copy()

REVIEW_CATEGORY_MIN = 1
REVIEW_CATEGORY_MAX = 5
REVIEW_CATEGORY_DEFAULT = 5

# Community forum (text-only topics and comments)
COMMUNITY_TOPIC_TITLE_MAX_LENGTH = 200

# Pinned discussion subjects. Stored verbatim as the canonical label so the
# column reads well in the database; `Other` is the safe default for existing
# rows and any custom topic that does not fit a pinned subject.
COMMUNITY_SUBJECT_OTHER = "Other"
COMMUNITY_SUBJECTS: list[str] = [
    "First time Helper",
    "First time Helpee",
    "Communication",
    "Privacy",
    "Emergencies",
    "Events",
    "Activities",
    "Job management",
    "Health and Safety",
    "Regulations",
    "Work visas",
    "Meeting people",
    "Businesses",
    "Money",
    "Workshops",
    "Tours",
    "Dinner",
    COMMUNITY_SUBJECT_OTHER,
]
COMMUNITY_SUBJECT_MAX_LENGTH = 48
COMMUNITY_SUBJECT_ICONS: dict[str, str] = {
    "First time Helper": "hand-helping",
    "First time Helpee": "hand-heart",
    "Communication": "messages-square",
    "Privacy": "shield",
    "Emergencies": "siren",
    "Events": "calendar-days",
    "Activities": "activity",
    "Job management": "clipboard-list",
    "Health and Safety": "heart-pulse",
    "Regulations": "scale",
    "Work visas": "stamp",
    "Meeting people": "users",
    "Businesses": "store",
    "Money": "coins",
    "Workshops": "wrench",
    "Tours": "map",
    "Dinner": "utensils",
    COMMUNITY_SUBJECT_OTHER: "circle-ellipsis",
}

# SQL literal list used by the topic subject check constraint.
_COMMUNITY_SUBJECTS_SQL = ", ".join(
    f"'{subject}'" for subject in COMMUNITY_SUBJECTS
)

# ---------------------------------------------------------------------------
# Completion success stories and safety reporting
# ---------------------------------------------------------------------------

# Photos uploaded AFTER a task is completed (kept separate from the original
# help-post photos, which describe the request rather than the outcome).
COMPLETED_TASK_PHOTO_PATH_MAX_LENGTH = 1024
COMPLETED_TASK_PHOTO_MAX_COUNT = 5

SAFETY_CATEGORY_RUDE = "rude_behaviour"
SAFETY_CATEGORY_ABUSIVE_LANGUAGE = "abusive_language"
SAFETY_CATEGORY_THREATS = "threats_or_violence"
SAFETY_CATEGORY_SEXUAL_HARASSMENT = "sexual_harassment"
SAFETY_CATEGORY_DISCRIMINATION = "discrimination"
SAFETY_CATEGORY_UNSAFE_CONDUCT = "unsafe_conduct"
SAFETY_CATEGORY_FRAUD_OR_THEFT = "fraud_or_theft"
SAFETY_CATEGORY_PRIVACY_VIOLATION = "privacy_violation"
SAFETY_CATEGORY_OTHER = "other"
SAFETY_REPORT_CATEGORIES: list[str] = [
    SAFETY_CATEGORY_RUDE,
    SAFETY_CATEGORY_ABUSIVE_LANGUAGE,
    SAFETY_CATEGORY_THREATS,
    SAFETY_CATEGORY_SEXUAL_HARASSMENT,
    SAFETY_CATEGORY_DISCRIMINATION,
    SAFETY_CATEGORY_UNSAFE_CONDUCT,
    SAFETY_CATEGORY_FRAUD_OR_THEFT,
    SAFETY_CATEGORY_PRIVACY_VIOLATION,
    SAFETY_CATEGORY_OTHER,
]
SAFETY_REPORT_CATEGORY_LABELS: dict[str, str] = {
    SAFETY_CATEGORY_RUDE: "Rude behaviour",
    SAFETY_CATEGORY_ABUSIVE_LANGUAGE: "Abusive language",
    SAFETY_CATEGORY_THREATS: "Threats or violence",
    SAFETY_CATEGORY_SEXUAL_HARASSMENT: "Sexual harassment",
    SAFETY_CATEGORY_DISCRIMINATION: "Discrimination",
    SAFETY_CATEGORY_UNSAFE_CONDUCT: "Unsafe conduct",
    SAFETY_CATEGORY_FRAUD_OR_THEFT: "Fraud or theft",
    SAFETY_CATEGORY_PRIVACY_VIOLATION: "Privacy violation",
    SAFETY_CATEGORY_OTHER: "Other",
}
# Categories an admin should always treat as high risk.
SAFETY_SEVERE_CATEGORIES: list[str] = [
    SAFETY_CATEGORY_THREATS,
    SAFETY_CATEGORY_SEXUAL_HARASSMENT,
    SAFETY_CATEGORY_DISCRIMINATION,
    SAFETY_CATEGORY_FRAUD_OR_THEFT,
]

SAFETY_STATUS_OPEN = "open"
SAFETY_STATUS_REVIEWING = "reviewing"
SAFETY_STATUS_RESOLVED = "resolved"
SAFETY_STATUS_DISMISSED = "dismissed"
SAFETY_REPORT_STATUSES: list[str] = [
    SAFETY_STATUS_OPEN,
    SAFETY_STATUS_REVIEWING,
    SAFETY_STATUS_RESOLVED,
    SAFETY_STATUS_DISMISSED,
]
SAFETY_REPORT_STATUS_LABELS: dict[str, str] = {
    SAFETY_STATUS_OPEN: "Open",
    SAFETY_STATUS_REVIEWING: "Reviewing",
    SAFETY_STATUS_RESOLVED: "Resolved",
    SAFETY_STATUS_DISMISSED: "Dismissed",
}
SAFETY_REPORT_DETAILS_MAX_WORDS = 500

# Account moderation outcomes. `clear` is the safe default for every existing
# subscriber; `is_active` stays the separate account-enabled flag.
MODERATION_STATUS_CLEAR = "clear"
MODERATION_STATUS_WARNED = "warned"
MODERATION_STATUS_BANNED = "banned"
MODERATION_STATUSES: list[str] = [
    MODERATION_STATUS_CLEAR,
    MODERATION_STATUS_WARNED,
    MODERATION_STATUS_BANNED,
]
MODERATION_STATUS_LABELS: dict[str, str] = {
    MODERATION_STATUS_CLEAR: "Clear",
    MODERATION_STATUS_WARNED: "Warned",
    MODERATION_STATUS_BANNED: "Banned",
}
# Limits enforced by the UI layer (kept here as the single source of truth).
COMMUNITY_TOPIC_MAX_WORDS = 5000
COMMUNITY_COMMENT_MAX_WORDS = 1000

# Email verification (Resend links)
VERIFICATION_PURPOSE_SIGNUP = "signup"
VERIFICATION_PURPOSE_RESEND = "resend"
VERIFICATION_PURPOSES: list[str] = [
    VERIFICATION_PURPOSE_SIGNUP,
    VERIFICATION_PURPOSE_RESEND,
]

# Token digests are SHA-256 hex strings: always 64 characters.
VERIFICATION_TOKEN_DIGEST_LENGTH = 64
# How long a verification link stays valid, and the minimum gap between sends.
VERIFICATION_TOKEN_TTL_MINUTES = 60
VERIFICATION_RESEND_COOLDOWN_SECONDS = 120
VERIFICATION_MAX_SENDS_PER_DAY = 5

# ---------------------------------------------------------------------------
# Membership tiers and billing vocabularies
# ---------------------------------------------------------------------------

MEMBERSHIP_TIER_FREE = "free"
MEMBERSHIP_TIER_COFFEE_MONTHLY = "coffee_monthly"
MEMBERSHIP_TIER_DINNER_ANNUAL = "dinner_annual"
MEMBERSHIP_TIERS: list[str] = [
    MEMBERSHIP_TIER_FREE,
    MEMBERSHIP_TIER_COFFEE_MONTHLY,
    MEMBERSHIP_TIER_DINNER_ANNUAL,
]
PREMIUM_MEMBERSHIP_TIERS: list[str] = [
    MEMBERSHIP_TIER_COFFEE_MONTHLY,
    MEMBERSHIP_TIER_DINNER_ANNUAL,
]

MEMBERSHIP_TIER_LABELS: dict[str, str] = {
    MEMBERSHIP_TIER_FREE: "Free",
    MEMBERSHIP_TIER_COFFEE_MONTHLY: "Coffee (monthly)",
    MEMBERSHIP_TIER_DINNER_ANNUAL: "Dinner (annual)",
}

# Display prices (USD). Stripe remains the source of truth for billing.
MEMBERSHIP_TIER_PRICES: dict[str, float] = {
    MEMBERSHIP_TIER_FREE: 0.0,
    MEMBERSHIP_TIER_COFFEE_MONTHLY: 5.0,
    MEMBERSHIP_TIER_DINNER_ANNUAL: 49.0,
}

SUBSCRIPTION_STATUS_NONE = "none"
SUBSCRIPTION_STATUS_INCOMPLETE = "incomplete"
SUBSCRIPTION_STATUS_TRIALING = "trialing"
SUBSCRIPTION_STATUS_ACTIVE = "active"
SUBSCRIPTION_STATUS_PAST_DUE = "past_due"
SUBSCRIPTION_STATUS_UNPAID = "unpaid"
SUBSCRIPTION_STATUS_CANCELED = "canceled"
SUBSCRIPTION_STATUS_EXPIRED = "expired"
SUBSCRIPTION_STATUSES: list[str] = [
    SUBSCRIPTION_STATUS_NONE,
    SUBSCRIPTION_STATUS_INCOMPLETE,
    SUBSCRIPTION_STATUS_TRIALING,
    SUBSCRIPTION_STATUS_ACTIVE,
    SUBSCRIPTION_STATUS_PAST_DUE,
    SUBSCRIPTION_STATUS_UNPAID,
    SUBSCRIPTION_STATUS_CANCELED,
    SUBSCRIPTION_STATUS_EXPIRED,
]
# Statuses that grant premium capabilities while the period is still valid.
ENTITLED_SUBSCRIPTION_STATUSES: list[str] = [
    SUBSCRIPTION_STATUS_TRIALING,
    SUBSCRIPTION_STATUS_ACTIVE,
    SUBSCRIPTION_STATUS_PAST_DUE,
]

STRIPE_ID_MAX_LENGTH = 255

# Help post lifetimes (hours) and the expiry upgrade notice window.
FREE_POST_LIFETIME_HOURS = 7 * 24
PREMIUM_POST_LIFETIME_HOURS = 30 * 24
EXPIRY_NOTICE_LEAD_HOURS = 24
# Concurrent open post allowances per tier.
FREE_ACTIVE_POST_LIMIT = 1
PREMIUM_ACTIVE_POST_LIMIT = 10

# In-app membership notices
NOTICE_KIND_POST_EXPIRING = "post_expiring"
NOTICE_KIND_POST_EXPIRED = "post_expired"
NOTICE_KIND_UPGRADE_PROMPT = "upgrade_prompt"
NOTICE_KIND_MEMBERSHIP_ACTIVE = "membership_active"
NOTICE_KIND_MEMBERSHIP_ENDED = "membership_ended"
MEMBERSHIP_NOTICE_KINDS: list[str] = [
    NOTICE_KIND_POST_EXPIRING,
    NOTICE_KIND_POST_EXPIRED,
    NOTICE_KIND_UPGRADE_PROMPT,
    NOTICE_KIND_MEMBERSHIP_ACTIVE,
    NOTICE_KIND_MEMBERSHIP_ENDED,
]


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------


class Subscriber(Base):
    """A Go and Help account: a traveller or local who signed up."""

    __tablename__ = "skillkind_subscriber"
    __table_args__ = (
        CheckConstraint(
            "moderation_status IN ('clear', 'warned', 'banned')",
            name="ck_subscriber_moderation_status",
        ),
        CheckConstraint(
            "warning_count >= 0",
            name="ck_subscriber_warning_count_non_negative",
        ),
        # Admin risk review queue: "who is warned or banned, most recent first?"
        Index(
            "ix_subscriber_moderation_status_updated",
            "moderation_status",
            "moderation_updated_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    # Mandatory for new registrations (validated in app code); nullable with no
    # server default so pre-existing subscriber rows stay valid and no name is
    # ever fabricated. `display_name` is composed from these two going forward.
    first_name: Mapped[str | None] = mapped_column(
        String(FIRST_NAME_MAX_LENGTH), default=None, nullable=True
    )
    family_name: Mapped[str | None] = mapped_column(
        String(FAMILY_NAME_MAX_LENGTH), default=None, nullable=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    # Optional date of birth. Nullable with no server default so existing
    # subscriber rows stay valid and no birthday is ever fabricated.
    date_of_birth: Mapped[datetime.date | None] = mapped_column(
        Date, default=None, nullable=True
    )
    help_mode: Mapped[str] = mapped_column(String(32), default=HELP_MODE_BOTH)
    # Nullable-safe + server default so the column can be added to a table that
    # already has subscriber rows; existing rows backfill to 'en'.
    preferred_language: Mapped[str | None] = mapped_column(
        String(8),
        default=DEFAULT_LANGUAGE,
        nullable=True,
        server_default=sa_text("'en'"),
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    # Email verification only: confirms the address is reachable. It never
    # asserts a real-world identity and no identity document is ever stored.
    is_verified: Mapped[bool] = mapped_column(default=False)
    # Moderation outcome from admin risk review. `is_active` is intentionally
    # left untouched here; banning logic sets it false separately.
    moderation_status: Mapped[str] = mapped_column(
        String(16),
        default=MODERATION_STATUS_CLEAR,
        server_default=sa_text("'clear'"),
        index=True,
    )
    warning_count: Mapped[int] = mapped_column(
        default=0, server_default=sa_text("0")
    )
    moderation_note: Mapped[str] = mapped_column(
        Text, default="", server_default=sa_text("''")
    )
    moderation_updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    joined_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    last_seen_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    profile: Mapped["Profile | None"] = relationship(
        back_populates="subscriber",
        uselist=False,
        default=None,
        cascade="all, delete-orphan",
    )
    help_posts: Mapped[list["HelpPost"]] = relationship(
        back_populates="author",
        default_factory=list,
        foreign_keys="HelpPost.author_id",
    )
    applications: Mapped[list["JobApplication"]] = relationship(
        back_populates="helper",
        default_factory=list,
        foreign_keys="JobApplication.helper_id",
    )
    verification_tokens: Mapped[list["EmailVerificationToken"]] = relationship(
        back_populates="subscriber",
        default_factory=list,
        cascade="all, delete-orphan",
        order_by="EmailVerificationToken.created_at",
    )
    community_topics: Mapped[list["CommunityTopic"]] = relationship(
        back_populates="author",
        default_factory=list,
        foreign_keys="CommunityTopic.author_id",
        cascade="all, delete-orphan",
    )
    community_comments: Mapped[list["CommunityComment"]] = relationship(
        back_populates="author",
        default_factory=list,
        foreign_keys="CommunityComment.author_id",
        cascade="all, delete-orphan",
    )
    # One-to-one membership record. Absent (None) means the subscriber is on the
    # free tier, so existing rows need no backfill.
    membership: Mapped["MembershipSubscription | None"] = relationship(
        back_populates="subscriber",
        uselist=False,
        default=None,
        cascade="all, delete-orphan",
    )
    membership_notices: Mapped[list["MembershipNotice"]] = relationship(
        back_populates="subscriber",
        default_factory=list,
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="MembershipNotice.created_at",
    )
    # Safety reporting: reports this subscriber filed, and reports about them.
    safety_reports_filed: Mapped[list["SafetyReport"]] = relationship(
        back_populates="reporter",
        default_factory=list,
        foreign_keys="SafetyReport.reporter_id",
        passive_deletes=True,
        order_by="SafetyReport.created_at",
    )
    safety_reports_received: Mapped[list["SafetyReport"]] = relationship(
        back_populates="reported",
        default_factory=list,
        foreign_keys="SafetyReport.reported_id",
        passive_deletes=True,
        order_by="SafetyReport.created_at",
    )
    completed_task_photos: Mapped[list["CompletedTaskPhoto"]] = relationship(
        back_populates="uploader",
        default_factory=list,
        foreign_keys="CompletedTaskPhoto.uploader_id",
        passive_deletes=True,
        order_by="CompletedTaskPhoto.created_at",
    )
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        back_populates="subscriber",
        default_factory=list,
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PasswordResetToken.created_at",
    )
    notifications: Mapped[list["MemberNotification"]] = relationship(
        back_populates="recipient",
        default_factory=list,
        foreign_keys="MemberNotification.recipient_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="MemberNotification.created_at",
    )
    content_reports_filed: Mapped[list["ContentReport"]] = relationship(
        back_populates="reporter",
        default_factory=list,
        foreign_keys="ContentReport.reporter_id",
        passive_deletes=True,
        order_by="ContentReport.created_at",
    )
    content_reports_received: Mapped[list["ContentReport"]] = relationship(
        back_populates="reported",
        default_factory=list,
        foreign_keys="ContentReport.reported_id",
        passive_deletes=True,
        order_by="ContentReport.created_at",
    )
    # Recurring help-request schedules this member owns.
    recurring_help_schedules: Mapped[list["RecurringHelpSchedule"]] = (
        relationship(
            back_populates="owner",
            default_factory=list,
            foreign_keys="RecurringHelpSchedule.owner_id",
            cascade="all, delete-orphan",
            passive_deletes=True,
            order_by="RecurringHelpSchedule.next_occurrence_at",
        )
    )
    # Scheduled job check-ins this member created inside a thread.
    job_check_ins_created: Mapped[list["JobCheckIn"]] = relationship(
        back_populates="creator",
        default_factory=list,
        foreign_keys="JobCheckIn.creator_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="JobCheckIn.due_at",
    )
    # One-to-one required onboarding progress. Absent (None) means the member
    # predates onboarding, so existing accounts need no backfill row.
    onboarding_progress: Mapped["OnboardingProgress | None"] = relationship(
        back_populates="subscriber",
        uselist=False,
        default=None,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    # Private member blocking. `blocks_created` are the members this subscriber
    # blocked (never revealed to the blocked side); `blocks_received` are the
    # blocks other members placed on this subscriber. Communication checks treat
    # a block in EITHER direction as blocked.
    blocks_created: Mapped[list["MemberBlock"]] = relationship(
        back_populates="blocker",
        default_factory=list,
        foreign_keys="MemberBlock.blocker_id",
        passive_deletes=True,
        order_by="MemberBlock.created_at.desc()",
    )
    blocks_received: Mapped[list["MemberBlock"]] = relationship(
        back_populates="blocked",
        default_factory=list,
        foreign_keys="MemberBlock.blocked_id",
        passive_deletes=True,
        order_by="MemberBlock.created_at.desc()",
    )


class MembershipSubscription(Base):
    """A subscriber's paid membership state, mirrored from Stripe.

    Exactly one row per subscriber (unique FK). A missing row means "free": no
    backfill is required for existing subscribers. Stripe identifiers default to
    the empty string so the columns are never NULL, and are indexed for webhook
    lookups; partial unique indexes ignore the empty placeholder so many free /
    pending rows can coexist.
    """

    __tablename__ = "skillkind_membership_subscription"
    __table_args__ = (
        UniqueConstraint(
            "subscriber_id", name="uq_membership_subscription_subscriber"
        ),
        CheckConstraint(
            "tier IN ('free', 'coffee_monthly', 'dinner_annual')",
            name="ck_membership_subscription_tier",
        ),
        CheckConstraint(
            "status IN ('none', 'incomplete', 'trialing', 'active', "
            "'past_due', 'unpaid', 'canceled', 'expired')",
            name="ck_membership_subscription_status",
        ),
        CheckConstraint(
            "current_period_end IS NULL OR current_period_start IS NULL "
            "OR current_period_end >= current_period_start",
            name="ck_membership_subscription_period_order",
        ),
        # Webhook lookups by Stripe identifier, ignoring empty placeholders.
        Index(
            "uq_membership_subscription_stripe_subscription",
            "stripe_subscription_id",
            unique=True,
            postgresql_where=sa_text("stripe_subscription_id <> ''"),
        ),
        Index(
            "ix_membership_subscription_stripe_customer",
            "stripe_customer_id",
            postgresql_where=sa_text("stripe_customer_id <> ''"),
        ),
        # Entitlement sweeps: "which active memberships lapse next?"
        Index(
            "ix_membership_subscription_status_period_end",
            "status",
            "current_period_end",
        ),
        Index(
            "ix_membership_subscription_tier_status",
            "tier",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    subscriber_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    tier: Mapped[str] = mapped_column(
        String(32),
        default=MEMBERSHIP_TIER_FREE,
        server_default=sa_text("'free'"),
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(24),
        default=SUBSCRIPTION_STATUS_NONE,
        server_default=sa_text("'none'"),
        index=True,
    )
    stripe_customer_id: Mapped[str] = mapped_column(
        String(STRIPE_ID_MAX_LENGTH),
        default="",
        server_default=sa_text("''"),
    )
    stripe_subscription_id: Mapped[str] = mapped_column(
        String(STRIPE_ID_MAX_LENGTH),
        default="",
        server_default=sa_text("''"),
    )
    stripe_price_id: Mapped[str] = mapped_column(
        String(STRIPE_ID_MAX_LENGTH),
        default="",
        server_default=sa_text("''"),
    )
    stripe_checkout_session_id: Mapped[str] = mapped_column(
        String(STRIPE_ID_MAX_LENGTH),
        default="",
        server_default=sa_text("''"),
    )
    current_period_start: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    current_period_end: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(
        default=False, server_default=sa_text("false")
    )
    canceled_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    last_synced_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    subscriber: Mapped["Subscriber"] = relationship(
        back_populates="membership", default=None
    )


class MembershipNotice(Base):
    """An in-app notice about membership or post expiry.

    Rows are created lazily whenever the app evaluates a subscriber's posts, so
    the 24-hour expiry upgrade notice works without a background scheduler.
    `help_post_id` is optional: general membership notices are not tied to a
    post, and post-specific notices are de-duplicated in app code via
    (subscriber, post, kind) plus `HelpPost.expiry_notice_sent_at`.
    """

    __tablename__ = "skillkind_membership_notice"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('post_expiring', 'post_expired', 'upgrade_prompt', "
            "'membership_active', 'membership_ended')",
            name="ck_membership_notice_kind",
        ),
        CheckConstraint(
            "btrim(title) <> ''", name="ck_membership_notice_title_not_blank"
        ),
        # Unread badge count and newest-first inbox for one subscriber.
        Index(
            "ix_membership_notice_subscriber_created",
            "subscriber_id",
            "created_at",
        ),
        Index(
            "ix_membership_notice_subscriber_unread",
            "subscriber_id",
            "is_read",
        ),
        # De-duplication lookup for a post-specific notice kind.
        Index(
            "ix_membership_notice_post_kind",
            "help_post_id",
            "kind",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    subscriber_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    help_post_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_help_post.id", ondelete="CASCADE"),
        default=None,
        nullable=True,
        index=True,
    )
    kind: Mapped[str] = mapped_column(
        String(32),
        default=NOTICE_KIND_UPGRADE_PROMPT,
        server_default=sa_text("'upgrade_prompt'"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), default="Membership update")
    body: Mapped[str] = mapped_column(Text, default="")
    is_read: Mapped[bool] = mapped_column(
        default=False, server_default=sa_text("false")
    )
    read_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )

    subscriber: Mapped["Subscriber"] = relationship(
        back_populates="membership_notices", default=None
    )
    help_post: Mapped["HelpPost | None"] = relationship(
        back_populates="membership_notices", default=None
    )


class EmailVerificationToken(Base):
    """A one-time email verification link issued to a subscriber.

    Only the SHA-256 hex digest of the token is ever stored: the plaintext
    token lives exclusively inside the emailed link, so a database leak cannot
    be replayed. A row is single-use — `used_at` is stamped on redemption and
    any remaining unused rows for that subscriber should be invalidated.

    Request metadata (`requested_ip`, `requested_user_agent`, `send_attempts`,
    `sent_at`) exists so resend can be throttled safely per subscriber and per
    origin without a second table.
    """

    __tablename__ = "skillkind_email_verification_token"
    __table_args__ = (
        UniqueConstraint(
            "token_digest", name="uq_email_verification_token_digest"
        ),
        CheckConstraint(
            "char_length(token_digest) = 64",
            name="ck_email_verification_token_digest_sha256",
        ),
        CheckConstraint(
            "expires_at > created_at",
            name="ck_email_verification_token_expiry_after_creation",
        ),
        CheckConstraint(
            "send_attempts >= 0",
            name="ck_email_verification_token_send_attempts_non_negative",
        ),
        # Fast lookup of the live token(s) for a subscriber when throttling or
        # invalidating on a fresh resend.
        Index(
            "ix_email_verification_token_subscriber_created",
            "subscriber_id",
            "created_at",
        ),
        # Supports expiry sweeps and "is this link still usable?" checks.
        Index(
            "ix_email_verification_token_used_expires",
            "used_at",
            "expires_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    subscriber_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    # SHA-256 hex digest of the single-use token. Never the plaintext token.
    token_digest: Mapped[str] = mapped_column(String(64), index=True)
    # Email the link was addressed to, so a later address change invalidates it.
    email: Mapped[str] = mapped_column(String(255), index=True)
    purpose: Mapped[str] = mapped_column(
        String(24), default=VERIFICATION_PURPOSE_SIGNUP, index=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=None
    )
    sent_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    used_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    invalidated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    # Resend bookkeeping / abuse metadata.
    send_attempts: Mapped[int] = mapped_column(default=0)
    last_attempt_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    provider_message_id: Mapped[str] = mapped_column(String(120), default="")
    last_error: Mapped[str] = mapped_column(String(255), default="")
    requested_ip: Mapped[str] = mapped_column(
        String(64), default="", index=True
    )
    requested_user_agent: Mapped[str] = mapped_column(String(255), default="")
    consumed_ip: Mapped[str] = mapped_column(String(64), default="")

    subscriber: Mapped["Subscriber"] = relationship(
        back_populates="verification_tokens", default=None
    )


class Profile(Base):
    """Travel-journal style profile attached to a subscriber."""

    __tablename__ = "skillkind_profile"
    __table_args__ = (
        CheckConstraint(
            "username = lower(username)",
            name="ck_profile_username_lowercase",
        ),
        CheckConstraint(
            "char_length(username) <= 40",
            name="ck_profile_username_max_length",
        ),
        # Unique per handle, but the empty migration default may repeat, so the
        # uniqueness is enforced only over real handles.
        Index(
            "uq_profile_username_lower",
            "username",
            unique=True,
            postgresql_where=sa_text("username <> ''"),
        ),
        Index("ix_profile_nationality", "nationality"),
        CheckConstraint(
            f"location_mode IN ({_LOCATION_MODES_SQL})",
            name="ck_profile_location_mode",
        ),
        # Map visibility sweeps: "which members are pinned right now?"
        Index(
            "ix_profile_location_mode_updated",
            "location_mode",
            "location_updated_at",
        ),
        # Bounding-box map queries over visible members only.
        Index(
            "ix_profile_visible_location",
            "latitude",
            "longitude",
            postgresql_where=sa_text("location_mode <> 'hidden'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    subscriber_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    # Public lowercase handle. Defaults to empty so the column can be added to
    # a table that already has profile rows; a handle is claimed later.
    username: Mapped[str] = mapped_column(
        String(USERNAME_MAX_LENGTH),
        default="",
        index=True,
        server_default=sa_text("''"),
    )
    headline: Mapped[str] = mapped_column(String(160), default="")
    bio: Mapped[str] = mapped_column(Text, default="")
    avatar_seed: Mapped[str] = mapped_column(String(64), default="")
    # Upload-dir relative filename of a user-uploaded profile photo. Empty means
    # fall back to the generated avatar from `avatar_seed`.
    avatar_path: Mapped[str] = mapped_column(
        String(AVATAR_PATH_MAX_LENGTH), default="", server_default=sa_text("''")
    )
    nationality: Mapped[str] = mapped_column(
        String(NATIONALITY_MAX_LENGTH),
        default="",
        server_default=sa_text("''"),
    )
    # Opt-in: share the account phone number with signed-in members. Safe
    # server default keeps every existing profile's phone private.
    show_phone_to_members: Mapped[bool] = mapped_column(
        default=False, server_default=sa_text("false")
    )
    # Opt-in: only signed-in members who enable this appear on user maps and in
    # people search results. Safe server default keeps existing rows private.
    show_location: Mapped[bool] = mapped_column(
        default=False, server_default=sa_text("false"), index=True
    )
    # Sharing mode: hidden / approximate / live (the legacy `fixed` mode is
    # replaced by `approximate`). Server default keeps every existing profile
    # row hidden; app code keeps `show_location` in sync as
    # (location_mode <> 'hidden'), i.e. true for approximate and live.
    location_mode: Mapped[str] = mapped_column(
        String(16),
        default=DEFAULT_LOCATION_MODE,
        server_default=sa_text("'hidden'"),
        index=True,
    )
    # When the stored latitude/longitude was last refreshed. Nullable with no
    # server default so existing rows stay valid and no time is fabricated.
    location_updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    home_city: Mapped[str] = mapped_column(String(120), default="")
    home_country: Mapped[str] = mapped_column(String(120), default="")
    current_city: Mapped[str] = mapped_column(String(120), default="")
    # Structured street address parts for the profile location editor. All are
    # additive, non-null with empty-string Python and server defaults so every
    # existing profile row stays valid.
    road_and_number: Mapped[str] = mapped_column(
        String(ADDRESS_ROAD_MAX_LENGTH),
        default="",
        server_default=sa_text("''"),
    )
    town: Mapped[str] = mapped_column(
        String(ADDRESS_TOWN_MAX_LENGTH),
        default="",
        server_default=sa_text("''"),
    )
    postcode: Mapped[str] = mapped_column(
        String(ADDRESS_POSTCODE_MAX_LENGTH),
        default="",
        server_default=sa_text("''"),
    )
    # PRIVATE exact source coordinates.
    # guest views must render a derived approximate point instead.
    latitude: Mapped[float | None] = mapped_column(
        Numeric(9, 6), default=None, nullable=True
    )
    longitude: Mapped[float | None] = mapped_column(
        Numeric(9, 6), default=None, nullable=True
    )
    travel_radius_km: Mapped[int] = mapped_column(default=10)
    languages: Mapped[str] = mapped_column(String(255), default="")
    skills: Mapped[str] = mapped_column(String(500), default="")
    preferred_categories: Mapped[str] = mapped_column(String(500), default="")
    availability_note: Mapped[str] = mapped_column(String(255), default="")
    helper_rating_avg: Mapped[float] = mapped_column(Numeric(3, 2), default=0)
    helper_rating_count: Mapped[int] = mapped_column(default=0)
    traveller_rating_avg: Mapped[float] = mapped_column(
        Numeric(3, 2), default=0
    )
    traveller_rating_count: Mapped[int] = mapped_column(default=0)
    tasks_helped_count: Mapped[int] = mapped_column(default=0)
    tasks_received_count: Mapped[int] = mapped_column(default=0)
    kindness_points: Mapped[int] = mapped_column(default=0)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )

    subscriber: Mapped["Subscriber"] = relationship(
        back_populates="profile", default=None
    )


# ---------------------------------------------------------------------------
# Help requests and matching
# ---------------------------------------------------------------------------


class HelpPost(Base):
    """A request for practical help posted by a traveller or local."""

    __tablename__ = "skillkind_help_post"
    __table_args__ = (
        CheckConstraint(
            "renewed_from_post_id IS NULL OR renewed_from_post_id <> id",
            name="ck_help_post_renewal_not_self",
        ),
        # Active-post listings: open posts that have not expired yet.
        Index(
            "ix_help_post_status_expires",
            "status",
            "expires_at",
        ),
        # Per-author active post counting (free / premium limits).
        Index(
            "ix_help_post_author_status_expires",
            "author_id",
            "status",
            "expires_at",
        ),
        # Expiry-notice sweeps: posts nearing expiry with no notice sent yet.
        Index(
            "ix_help_post_expiry_notice",
            "expires_at",
            "expiry_notice_sent_at",
        ),
        # Premium posts surface first within a result set.
        Index(
            "ix_help_post_priority_created",
            "premium_priority",
            "created_at",
        ),
        CheckConstraint(
            f"location_mode IN ({_JOB_LOCATION_MODES_SQL})",
            name="ck_help_post_location_mode",
        ),
        # Public map queries filter by mode before reading coordinates.
        Index(
            "ix_help_post_location_mode_status",
            "location_mode",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True, init=False)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    # Legacy PRIMARY category: always the FIRST selected category. Existing
    # filters, labels, colours and indexes keep reading this column, so it must
    # never be left blank while `category_tags` holds values.
    category: Mapped[str] = mapped_column(
        String(48), default="other", index=True
    )
    # Normalized comma-separated set of up to three category keys, e.g.
    # "craftwork,teaching". Additive with an empty server default so it can be
    # added to a table that already holds help post rows; an empty value means
    # "fall back to the single legacy `category`".
    #
    # App-level validation rules (not enforced by the database):
    #   * only keys present in TASK_CATEGORIES are permitted;
    #   * duplicates are removed, preserving the order the member picked;
    #   * at most three categories may be stored;
    #   * the first selected value is also written into the legacy `category`
    #     column so old filters, labels, colours and indexes keep working.
    category_tags: Mapped[str] = mapped_column(
        String(255), default="", server_default=sa_text("''")
    )
    reward_type: Mapped[str] = mapped_column(
        String(32), default="gratitude_only"
    )
    reward_details: Mapped[str] = mapped_column(String(255), default="")
    reward_value: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    reward_currency: Mapped[str] = mapped_column(String(8), default="USD")
    location_name: Mapped[str] = mapped_column(String(200), default="")
    city: Mapped[str] = mapped_column(String(120), default="", index=True)
    country: Mapped[str] = mapped_column(String(120), default="")
    latitude: Mapped[float | None] = mapped_column(
        Numeric(9, 6), default=None, nullable=True
    )
    longitude: Mapped[float | None] = mapped_column(
        Numeric(9, 6), default=None, nullable=True
    )
    scheduled_for: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    duration_minutes: Mapped[int] = mapped_column(default=60)
    # New Help-screen form fields. All are additive with safe defaults so they
    # can be added to a table that already holds help post rows; the legacy
    # `scheduled_for`, `duration_minutes`, `reward_type` and `reward_details`
    # columns above stay authoritative for summary and ordering behaviour.
    # Normalized comma-separated ISO dates (YYYY-MM-DD) picked in the calendar.
    help_dates: Mapped[str] = mapped_column(
        Text, default="", server_default=sa_text("''")
    )
    start_time: Mapped[str] = mapped_column(
        String(16), default="", server_default=sa_text("''")
    )
    tools: Mapped[str] = mapped_column(
        Text, default="", server_default=sa_text("''")
    )
    knowledge_skills: Mapped[str] = mapped_column(
        Text, default="", server_default=sa_text("''")
    )
    # Normalized comma-separated reward keys (multiple rewards allowed).
    reward_types: Mapped[str] = mapped_column(
        String(255), default="", server_default=sa_text("''")
    )
    accommodation_nights: Mapped[int] = mapped_column(
        default=0, server_default=sa_text("0")
    )
    guided_tour_details: Mapped[str] = mapped_column(
        String(500), default="", server_default=sa_text("''")
    )
    activity_details: Mapped[str] = mapped_column(
        String(500), default="", server_default=sa_text("''")
    )
    other_reward_details: Mapped[str] = mapped_column(
        String(500), default="", server_default=sa_text("''")
    )
    urgency: Mapped[str] = mapped_column(String(24), default="flexible")
    helpers_needed: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(
        String(24), default=POST_STATUS_OPEN, index=True
    )
    view_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    # Lifetime bookkeeping. Nullable so the column can be added to a table that
    # already holds posts (existing rows stay valid and never expire until the
    # app stamps them); `premium_priority` defaults false for every old row.
    expires_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    expired_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True, index=True
    )
    # The new post points back to its expired/cancelled source; eligibility is
    # a cross-row lifecycle rule, not enforceable by a row CHECK constraint.
    renewed_from_post_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_help_post.id", ondelete="SET NULL"),
        default=None,
        nullable=True,
        index=True,
    )
    expiry_notice_sent_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    premium_priority: Mapped[bool] = mapped_column(
        default=False, server_default=sa_text("false")
    )
    # How the job location may be shown publicly: `approximate` (default, safe
    # for every existing row) or `place`. Additive with a server default so it
    # can be added to a table that already holds posts.
    location_mode: Mapped[str] = mapped_column(
        String(16),
        default=DEFAULT_JOB_LOCATION_MODE,
        server_default=sa_text("'approximate'"),
        index=True,
    )
    # PRIVATE to the poster and the accepted helper: the exact meeting address
    # and coordinates, supplied only after a helper is accepted when the public
    # request used approximate mode. These MUST never appear in public or guest
    # queries.
    accepted_location_name: Mapped[str] = mapped_column(
        String(ACCEPTED_LOCATION_NAME_MAX_LENGTH),
        default="",
        server_default=sa_text("''"),
    )
    accepted_latitude: Mapped[float | None] = mapped_column(
        Numeric(9, 6), default=None, nullable=True
    )
    accepted_longitude: Mapped[float | None] = mapped_column(
        Numeric(9, 6), default=None, nullable=True
    )

    author: Mapped["Subscriber"] = relationship(
        back_populates="help_posts", foreign_keys=[author_id], default=None
    )
    applications: Mapped[list["JobApplication"]] = relationship(
        back_populates="post",
        default_factory=list,
        cascade="all, delete-orphan",
    )
    photos: Mapped[list["HelpPostPhoto"]] = relationship(
        back_populates="help_post",
        default_factory=list,
        cascade="all, delete-orphan",
        order_by="HelpPostPhoto.display_order",
    )
    membership_notices: Mapped[list["MembershipNotice"]] = relationship(
        back_populates="help_post",
        default_factory=list,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    # Recurring schedules that use THIS post as their template.
    recurring_schedules: Mapped[list["RecurringHelpSchedule"]] = relationship(
        back_populates="source_post",
        default_factory=list,
        foreign_keys="RecurringHelpSchedule.source_post_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RecurringHelpSchedule.created_at",
    )
    # The occurrence row recording that THIS post was generated by a schedule.
    generated_occurrence: Mapped["RecurringHelpOccurrence | None"] = (
        relationship(
            back_populates="generated_post",
            uselist=False,
            default=None,
            foreign_keys="RecurringHelpOccurrence.generated_post_id",
            cascade="all, delete-orphan",
            passive_deletes=True,
        )
    )


class JobApplication(Base):
    """A helper offer or direct-help invitation (request -> acceptance)."""

    __tablename__ = "skillkind_job_application"
    __table_args__ = (
        UniqueConstraint(
            "post_id", "helper_id", name="uq_application_post_helper"
        ),
        CheckConstraint(
            f"request_type IN ({_APPLICATION_REQUEST_TYPES_SQL})",
            name="ck_application_request_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_help_post.id", ondelete="CASCADE"), index=True
    )
    helper_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    request_type: Mapped[str] = mapped_column(
        String(24),
        default=APPLICATION_REQUEST_HELPER_OFFER,
        server_default=sa_text("'helper_offer'"),
    )
    initiator_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="SET NULL"),
        default=None,
        nullable=True,
        index=True,
    )
    pitch: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(
        String(24), default=APPLICATION_PENDING, index=True
    )
    proposed_time: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    responded_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    post: Mapped["HelpPost"] = relationship(
        back_populates="applications", default=None
    )


class JobScheduleProposal(Base):
    """A proposed new date/time for an already accepted job application.

    Either participant (poster or helper) may propose; the other side responds.
    At most one proposal may be pending per application at a time.
    """

    __tablename__ = "skillkind_job_schedule_proposal"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({_SCHEDULE_PROPOSAL_STATUSES_SQL})",
            name="ck_schedule_proposal_status",
        ),
        CheckConstraint(
            "responder_id IS NULL OR responder_id <> proposer_id",
            name="ck_schedule_proposal_distinct_parties",
        ),
        # Fast lookup of the live proposal for an application.
        Index(
            "ix_schedule_proposal_application_status",
            "application_id",
            "status",
        ),
        # Participant-facing lists ordered by the proposed slot.
        Index(
            "ix_schedule_proposal_proposer_time",
            "proposer_id",
            "proposed_for",
        ),
        Index(
            "ix_schedule_proposal_responder_time",
            "responder_id",
            "proposed_for",
        ),
        Index(
            "ix_schedule_proposal_status_time",
            "status",
            "proposed_for",
        ),
        # At most one pending proposal per application.
        Index(
            "uq_schedule_proposal_one_pending",
            "application_id",
            unique=True,
            postgresql_where=sa_text(f"status = '{SCHEDULE_PROPOSAL_PENDING}'"),
            sqlite_where=sa_text(f"status = '{SCHEDULE_PROPOSAL_PENDING}'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_job_application.id", ondelete="CASCADE"),
        index=True,
    )
    proposer_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    proposed_for: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), index=True
    )
    reason: Mapped[str | None] = mapped_column(
        Text, default="", server_default=sa_text("''"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(24),
        default=SCHEDULE_PROPOSAL_PENDING,
        server_default=sa_text(f"'{SCHEDULE_PROPOSAL_PENDING}'"),
        index=True,
    )
    responder_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="SET NULL"),
        default=None,
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    responded_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )


class JobCancellationProposal(Base):
    """Mutual cancellation of an accepted application, not unilateral removal.

    Accepted-application eligibility and participant membership require lifecycle
    validation against the application and post when this record is written.
    """

    __tablename__ = "skillkind_job_cancellation_proposal"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({_CANCELLATION_PROPOSAL_STATUSES_SQL})",
            name="ck_cancellation_proposal_status",
        ),
        CheckConstraint(
            "length(trim(reason)) > 0",
            name="ck_cancellation_proposal_reason_nonblank",
        ),
        CheckConstraint(
            "responder_id IS NULL OR responder_id <> proposer_id",
            name="ck_cancellation_proposal_distinct_parties",
        ),
        CheckConstraint(
            "responded_at IS NULL OR responded_at >= created_at",
            name="ck_cancellation_proposal_response_time",
        ),
        Index(
            "ix_cancellation_proposal_application_status",
            "application_id",
            "status",
        ),
        Index(
            "ix_cancellation_proposal_proposer_time",
            "proposer_id",
            "created_at",
        ),
        Index(
            "ix_cancellation_proposal_responder_time",
            "responder_id",
            "created_at",
        ),
        Index("ix_cancellation_proposal_status_time", "status", "created_at"),
        Index(
            "uq_cancellation_proposal_one_pending",
            "application_id",
            unique=True,
            postgresql_where=sa_text(
                f"status = '{CANCELLATION_PROPOSAL_PENDING}'"
            ),
            sqlite_where=sa_text(f"status = '{CANCELLATION_PROPOSAL_PENDING}'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_job_application.id", ondelete="CASCADE"),
        index=True,
    )
    proposer_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(24),
        default=CANCELLATION_PROPOSAL_PENDING,
        server_default=sa_text(f"'{CANCELLATION_PROPOSAL_PENDING}'"),
        index=True,
    )
    responder_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="SET NULL"),
        default=None,
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    responded_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )


class JobNoShowReport(Base):
    """Private participant report, never a public review or public rating.

    The writer must validate that both members belong to the application.
    """

    __tablename__ = "skillkind_job_no_show_report"
    __table_args__ = (
        UniqueConstraint(
            "application_id", name="uq_no_show_report_application"
        ),
        CheckConstraint(
            "reporter_id <> reported_member_id",
            name="ck_no_show_report_distinct_parties",
        ),
        Index("ix_no_show_report_reporter_time", "reporter_id", "created_at"),
        Index(
            "ix_no_show_report_reported_time",
            "reported_member_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_job_application.id", ondelete="CASCADE")
    )
    reporter_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    reported_member_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    reason: Mapped[str | None] = mapped_column(
        Text, default="", server_default=sa_text("''"), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=None,
        index=True,
    )


class HelpPostPhoto(Base):
    """An ordered uploaded photo attached to a help post."""

    __tablename__ = "skillkind_help_post_photo"
    __table_args__ = (
        UniqueConstraint(
            "help_post_id",
            "display_order",
            name="uq_help_post_photo_order",
        ),
        CheckConstraint(
            "display_order BETWEEN 0 AND 4",
            name="ck_help_post_photo_order_max_five",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    help_post_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_help_post.id", ondelete="CASCADE"), index=True
    )
    path: Mapped[str] = mapped_column(String(1024))
    display_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    help_post: Mapped["HelpPost"] = relationship(
        back_populates="photos", default=None
    )


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------


class InboxThreadDismissal(Base):
    """A member's private Inbox dismissal; migrate before use in queries or UI."""

    __tablename__ = "skillkind_inbox_thread_dismissal"
    __table_args__ = (
        UniqueConstraint(
            "subscriber_id",
            "kind",
            "ref_id",
            name="uq_inbox_thread_dismissal_subscriber_kind_ref",
        ),
        CheckConstraint(
            "kind IN ('contact','noncontact','job')",
            name="ck_inbox_thread_dismissal_kind",
        ),
        CheckConstraint(
            "ref_id > 0",
            name="ck_inbox_thread_dismissal_ref_positive",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    subscriber_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(20))
    ref_id: Mapped[int] = mapped_column()
    dismissed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )


class MessageThread(Base):
    """A conversation between a poster and a helper about one help post."""

    __tablename__ = "skillkind_message_thread"
    __table_args__ = (
        UniqueConstraint("post_id", "helper_id", name="uq_thread_post_helper"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_help_post.id", ondelete="CASCADE"), index=True
    )
    poster_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    helper_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    subject: Mapped[str] = mapped_column(String(200), default="")
    is_archived: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    last_message_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    post: Mapped["HelpPost"] = relationship(default=None)
    poster: Mapped["Subscriber"] = relationship(
        foreign_keys=[poster_id], default=None
    )
    helper: Mapped["Subscriber"] = relationship(
        foreign_keys=[helper_id], default=None
    )
    messages: Mapped[list["Message"]] = relationship(
        back_populates="thread",
        default_factory=list,
        cascade="all, delete-orphan",
        order_by="Message.sent_at",
    )
    check_ins: Mapped[list["JobCheckIn"]] = relationship(
        back_populates="thread",
        default_factory=list,
        foreign_keys="JobCheckIn.thread_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="JobCheckIn.due_at",
    )


class Message(Base):
    """A single chat message inside a thread."""

    __tablename__ = "skillkind_message"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    thread_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_message_thread.id", ondelete="CASCADE"),
        index=True,
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    body: Mapped[str] = mapped_column(Text, default="")
    sent_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    read_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    thread: Mapped["MessageThread"] = relationship(
        back_populates="messages", default=None
    )
    sender: Mapped["Subscriber"] = relationship(
        foreign_keys=[sender_id], default=None
    )


# ---------------------------------------------------------------------------
# Contacts (person-to-person connections, independent of help posts)
# ---------------------------------------------------------------------------


class ContactLink(Base):
    """A contact request between two subscribers, and the resulting connection.

    One row per requester/recipient pair. `status` moves through
    pending -> accepted / declined, and accepted links can later be `removed`.
    Message tracking columns let a contacts list be rendered without an extra
    aggregate query over `skillkind_contact_message`.
    """

    __tablename__ = "skillkind_contact_link"
    __table_args__ = (
        UniqueConstraint(
            "requester_id",
            "recipient_id",
            name="uq_contact_link_requester_recipient",
        ),
        CheckConstraint(
            "requester_id <> recipient_id",
            name="ck_contact_link_not_self",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    requester_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(24), default=CONTACT_PENDING, index=True
    )
    intro_note: Mapped[str] = mapped_column(String(500), default="")
    requester_city: Mapped[str] = mapped_column(String(120), default="")
    recipient_city: Mapped[str] = mapped_column(String(120), default="")
    message_count: Mapped[int] = mapped_column(default=0)
    last_message_preview: Mapped[str] = mapped_column(String(255), default="")
    last_message_sender_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="SET NULL"),
        default=None,
        nullable=True,
    )
    last_message_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    responded_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    accepted_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    declined_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    removed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    removed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="SET NULL"),
        default=None,
        nullable=True,
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    requester: Mapped["Subscriber"] = relationship(
        foreign_keys=[requester_id], default=None
    )
    recipient: Mapped["Subscriber"] = relationship(
        foreign_keys=[recipient_id], default=None
    )
    messages: Mapped[list["ContactMessage"]] = relationship(
        back_populates="contact_link",
        default_factory=list,
        cascade="all, delete-orphan",
        order_by="ContactMessage.sent_at",
    )


class ContactMessage(Base):
    """A direct message exchanged between two confirmed contacts."""

    __tablename__ = "skillkind_contact_message"
    __table_args__ = (
        CheckConstraint(
            "sender_id <> recipient_id",
            name="ck_contact_message_not_self",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    contact_link_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_contact_link.id", ondelete="CASCADE"),
        index=True,
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    body: Mapped[str] = mapped_column(Text, default="")
    sent_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    read_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    contact_link: Mapped["ContactLink"] = relationship(
        back_populates="messages", default=None
    )
    sender: Mapped["Subscriber"] = relationship(
        foreign_keys=[sender_id], default=None
    )
    recipient: Mapped["Subscriber"] = relationship(
        foreign_keys=[recipient_id], default=None
    )


# ---------------------------------------------------------------------------
# Completion and reciprocal reviews
# ---------------------------------------------------------------------------


class CompletedTask(Base):
    """Record of a help post that was carried out by a helper."""

    __tablename__ = "skillkind_completed_task"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_help_post.id", ondelete="CASCADE"), index=True
    )
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_job_application.id", ondelete="SET NULL"),
        default=None,
        nullable=True,
    )
    poster_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    helper_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    completed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    actual_duration_minutes: Mapped[int] = mapped_column(default=0)
    reward_given: Mapped[str] = mapped_column(String(255), default="")
    reward_confirmed: Mapped[bool] = mapped_column(default=False)
    poster_confirmed: Mapped[bool] = mapped_column(default=False)
    helper_confirmed: Mapped[bool] = mapped_column(default=False)
    story_note: Mapped[str] = mapped_column(Text, default="")

    post: Mapped["HelpPost"] = relationship(default=None)
    poster: Mapped["Subscriber"] = relationship(
        foreign_keys=[poster_id], default=None
    )
    helper: Mapped["Subscriber"] = relationship(
        foreign_keys=[helper_id], default=None
    )
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="completed_task",
        default_factory=list,
        cascade="all, delete-orphan",
    )
    # Post-completion success-story photos (separate from the help post's own
    # photos, which illustrate the original request).
    completion_photos: Mapped[list["CompletedTaskPhoto"]] = relationship(
        back_populates="completed_task",
        default_factory=list,
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="CompletedTaskPhoto.display_order",
    )
    safety_reports: Mapped[list["SafetyReport"]] = relationship(
        back_populates="completed_task",
        default_factory=list,
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SafetyReport.created_at",
    )


class Review(Base):
    """Reciprocal 1-5 star review left after a completed task."""

    __tablename__ = "skillkind_review"
    __table_args__ = (
        UniqueConstraint(
            "completed_task_id", "reviewer_id", name="uq_review_task_reviewer"
        ),
        CheckConstraint(
            "category_one BETWEEN 1 AND 5",
            name="ck_review_category_one_range",
        ),
        CheckConstraint(
            "category_two BETWEEN 1 AND 5",
            name="ck_review_category_two_range",
        ),
        CheckConstraint(
            "category_three BETWEEN 1 AND 5",
            name="ck_review_category_three_range",
        ),
        CheckConstraint(
            "category_four BETWEEN 1 AND 5",
            name="ck_review_category_four_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    completed_task_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_completed_task.id", ondelete="CASCADE"),
        index=True,
    )
    reviewer_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    reviewee_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    direction: Mapped[str] = mapped_column(
        String(32), default=REVIEW_POSTER_TO_HELPER
    )
    # Rounded average of the four category scores, kept for compatibility.
    rating: Mapped[int] = mapped_column(default=5)
    category_one: Mapped[int] = mapped_column(
        default=REVIEW_CATEGORY_DEFAULT, server_default=sa_text("5")
    )
    category_two: Mapped[int] = mapped_column(
        default=REVIEW_CATEGORY_DEFAULT, server_default=sa_text("5")
    )
    category_three: Mapped[int] = mapped_column(
        default=REVIEW_CATEGORY_DEFAULT, server_default=sa_text("5")
    )
    category_four: Mapped[int] = mapped_column(
        default=REVIEW_CATEGORY_DEFAULT, server_default=sa_text("5")
    )
    comment: Mapped[str] = mapped_column(Text, default="")
    kindness_flag: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )

    completed_task: Mapped["CompletedTask"] = relationship(
        back_populates="reviews", default=None
    )
    reviewer: Mapped["Subscriber"] = relationship(
        foreign_keys=[reviewer_id], default=None
    )
    reviewee: Mapped["Subscriber"] = relationship(
        foreign_keys=[reviewee_id], default=None
    )


# ---------------------------------------------------------------------------
# Community forum (persistent, text-only discussions)
# ---------------------------------------------------------------------------


class CommunityTopic(Base):
    """A text-only community discussion started by a subscriber.

    Titles are capped at 200 characters in the schema; the long-form body word
    limit (5,000 words) is enforced in the UI layer. Check constraints reject
    empty or whitespace-only titles and bodies so blank posts can never persist.
    """

    __tablename__ = "skillkind_community_topic"
    __table_args__ = (
        CheckConstraint(
            "btrim(title) <> ''",
            name="ck_community_topic_title_not_blank",
        ),
        CheckConstraint(
            "char_length(title) <= 200",
            name="ck_community_topic_title_max_length",
        ),
        CheckConstraint(
            "btrim(body) <> ''",
            name="ck_community_topic_body_not_blank",
        ),
        CheckConstraint(
            f"subject_category IN ({_COMMUNITY_SUBJECTS_SQL})",
            name="ck_community_topic_subject_category",
        ),
        # Folder-style browsing of one pinned subject, newest first.
        Index(
            "ix_community_topic_subject_created",
            "subject_category",
            "created_at",
        ),
        # Newest-first feed listing.
        Index("ix_community_topic_created_at", "created_at"),
        # "My topics", newest first.
        Index(
            "ix_community_topic_author_created",
            "author_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    # Pinned discussion subject. Server default keeps existing rows valid by
    # filing them under `Other`.
    subject_category: Mapped[str] = mapped_column(
        String(COMMUNITY_SUBJECT_MAX_LENGTH),
        default=COMMUNITY_SUBJECT_OTHER,
        server_default=sa_text("'Other'"),
        index=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    author: Mapped["Subscriber"] = relationship(
        back_populates="community_topics",
        foreign_keys=[author_id],
        default=None,
    )
    comments: Mapped[list["CommunityComment"]] = relationship(
        back_populates="topic",
        default_factory=list,
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="CommunityComment.created_at",
    )


class CommunityComment(Base):
    """A text-only comment attached to a community topic.

    Deleting a topic removes its comments (database-level ON DELETE CASCADE plus
    ORM cascade). Blank bodies are rejected by a check constraint.
    """

    __tablename__ = "skillkind_community_comment"
    __table_args__ = (
        CheckConstraint(
            "btrim(body) <> ''",
            name="ck_community_comment_body_not_blank",
        ),
        # Chronological rendering of one topic's thread.
        Index(
            "ix_community_comment_topic_created",
            "topic_id",
            "created_at",
        ),
        # "My comments", newest first.
        Index(
            "ix_community_comment_author_created",
            "author_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_community_topic.id", ondelete="CASCADE"),
        index=True,
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    topic: Mapped["CommunityTopic"] = relationship(
        back_populates="comments", default=None
    )
    author: Mapped["Subscriber"] = relationship(
        back_populates="community_comments",
        foreign_keys=[author_id],
        default=None,
    )


# ---------------------------------------------------------------------------
# Completion success-story photos
# ---------------------------------------------------------------------------


class CompletedTaskPhoto(Base):
    """A photo uploaded after a task was completed (a success story image).

    Deliberately separate from `HelpPostPhoto`: those illustrate the original
    request, while these record the finished work and may be shared by either
    participant. `uploader_id` records which side added the photo so it can be
    attributed and removed by its owner.
    """

    __tablename__ = "skillkind_completed_task_photo"
    __table_args__ = (
        UniqueConstraint(
            "completed_task_id",
            "path",
            name="uq_completed_task_photo_task_path",
        ),
        CheckConstraint(
            "display_order >= 0",
            name="ck_completed_task_photo_order_non_negative",
        ),
        CheckConstraint(
            "btrim(path) <> ''",
            name="ck_completed_task_photo_path_not_blank",
        ),
        # Rendering one story's gallery in order.
        Index(
            "ix_completed_task_photo_task_order",
            "completed_task_id",
            "display_order",
        ),
        # "My uploaded story photos", newest first.
        Index(
            "ix_completed_task_photo_uploader_created",
            "uploader_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    completed_task_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_completed_task.id", ondelete="CASCADE"),
        index=True,
    )
    uploader_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    path: Mapped[str] = mapped_column(
        String(COMPLETED_TASK_PHOTO_PATH_MAX_LENGTH)
    )
    caption: Mapped[str] = mapped_column(
        String(255), default="", server_default=sa_text("''")
    )
    display_order: Mapped[int] = mapped_column(
        default=0, server_default=sa_text("0")
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )

    completed_task: Mapped["CompletedTask"] = relationship(
        back_populates="completion_photos", default=None
    )
    uploader: Mapped["Subscriber"] = relationship(
        back_populates="completed_task_photos",
        foreign_keys=[uploader_id],
        default=None,
    )


# ---------------------------------------------------------------------------
# Bad-experience (safety) reporting and admin risk review
# ---------------------------------------------------------------------------


class SafetyReport(Base):
    """A bad-experience report filed about the other participant in a task.

    One report per (completed task, reporter) pair, so a reporter cannot file
    duplicates about the same job; a check constraint prevents reporting
    oneself. The reporter / reported links are immutable in application code:
    only `status`, `reviewed_at`, `reviewed_by_id` and `admin_note` change once
    a report exists, which keeps the audit trail intact for admin review.
    """

    __tablename__ = "skillkind_safety_report"
    __table_args__ = (
        UniqueConstraint(
            "completed_task_id",
            "reporter_id",
            name="uq_safety_report_task_reporter",
        ),
        CheckConstraint(
            "reporter_id <> reported_id",
            name="ck_safety_report_not_self",
        ),
        CheckConstraint(
            "category IN ('rude_behaviour', 'abusive_language', "
            "'threats_or_violence', 'sexual_harassment', 'discrimination', "
            "'unsafe_conduct', 'fraud_or_theft', 'privacy_violation', "
            "'other')",
            name="ck_safety_report_category",
        ),
        CheckConstraint(
            "status IN ('open', 'reviewing', 'resolved', 'dismissed')",
            name="ck_safety_report_status",
        ),
        CheckConstraint(
            "reviewed_at IS NULL OR reviewed_at >= created_at",
            name="ck_safety_report_review_after_creation",
        ),
        # Admin queue: open reports first, oldest first within a status.
        Index(
            "ix_safety_report_status_created",
            "status",
            "created_at",
        ),
        # Risk profile for one subscriber: "how many reports, of what kind?"
        Index(
            "ix_safety_report_reported_created",
            "reported_id",
            "created_at",
        ),
        Index(
            "ix_safety_report_reported_status",
            "reported_id",
            "status",
        ),
        # "Have I already reported this job?" lookup.
        Index(
            "ix_safety_report_reporter_created",
            "reporter_id",
            "created_at",
        ),
        Index("ix_safety_report_category", "category"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    completed_task_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_completed_task.id", ondelete="CASCADE"),
        index=True,
    )
    # Immutable links: who reported, and who was reported.
    reporter_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    reported_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    category: Mapped[str] = mapped_column(
        String(32),
        default=SAFETY_CATEGORY_OTHER,
        server_default=sa_text("'other'"),
    )
    details: Mapped[str] = mapped_column(
        Text, default="", server_default=sa_text("''")
    )
    status: Mapped[str] = mapped_column(
        String(16),
        default=SAFETY_STATUS_OPEN,
        server_default=sa_text("'open'"),
        index=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    reviewed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    # Admin who handled the report. SET NULL keeps the report if that admin
    # account is ever deleted.
    reviewed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="SET NULL"),
        default=None,
        nullable=True,
        index=True,
    )
    admin_note: Mapped[str] = mapped_column(
        Text, default="", server_default=sa_text("''")
    )

    completed_task: Mapped["CompletedTask"] = relationship(
        back_populates="safety_reports", default=None
    )
    reporter: Mapped["Subscriber"] = relationship(
        back_populates="safety_reports_filed",
        foreign_keys=[reporter_id],
        default=None,
    )
    reported: Mapped["Subscriber"] = relationship(
        back_populates="safety_reports_received",
        foreign_keys=[reported_id],
        default=None,
    )
    reviewed_by: Mapped["Subscriber | None"] = relationship(
        foreign_keys=[reviewed_by_id], default=None
    )


# ---------------------------------------------------------------------------
# Recurring help requests, job check-ins and guided onboarding
# ---------------------------------------------------------------------------

RECURRENCE_DAILY = "daily"
RECURRENCE_WEEKLY = "weekly"
RECURRENCE_BIWEEKLY = "biweekly"
RECURRENCE_MONTHLY = "monthly"
RECURRENCE_CADENCES: list[str] = [
    RECURRENCE_DAILY,
    RECURRENCE_WEEKLY,
    RECURRENCE_BIWEEKLY,
    RECURRENCE_MONTHLY,
]
_RECURRENCE_CADENCES_SQL = ", ".join(f"'{v}'" for v in RECURRENCE_CADENCES)

RECURRENCE_LABELS: dict[str, str] = {
    RECURRENCE_DAILY: "Every day",
    RECURRENCE_WEEKLY: "Every week",
    RECURRENCE_BIWEEKLY: "Every two weeks",
    RECURRENCE_MONTHLY: "Every month",
}

SCHEDULE_STATUS_ACTIVE = "active"
SCHEDULE_STATUS_PAUSED = "paused"
SCHEDULE_STATUS_COMPLETED = "completed"
SCHEDULE_STATUSES: list[str] = [
    SCHEDULE_STATUS_ACTIVE,
    SCHEDULE_STATUS_PAUSED,
    SCHEDULE_STATUS_COMPLETED,
]
_SCHEDULE_STATUSES_SQL = ", ".join(f"'{v}'" for v in SCHEDULE_STATUSES)

# Maximum interval multiplier a member may pick ("every N cadences").
RECURRENCE_MAX_INTERVAL = 12
DEFAULT_SCHEDULE_TIMEZONE = "UTC"

CHECK_IN_STATUS_PENDING = "pending"
CHECK_IN_STATUS_COMPLETED = "completed"
CHECK_IN_STATUS_CANCELLED = "cancelled"
CHECK_IN_STATUSES: list[str] = [
    CHECK_IN_STATUS_PENDING,
    CHECK_IN_STATUS_COMPLETED,
    CHECK_IN_STATUS_CANCELLED,
]
_CHECK_IN_STATUSES_SQL = ", ".join(f"'{v}'" for v in CHECK_IN_STATUSES)

CHECK_IN_PROMPT_MAX_LENGTH = 200
CHECK_IN_NOTE_MAX_LENGTH = 500

# Legacy storage bounds, not current UI totals. Keep the existing database
# constraints unchanged; the UI has 12 setup screens and 10 tour steps.
ONBOARDING_FIRST_STEP = 1
ONBOARDING_LAST_STEP = 15
GUIDED_TOUR_FIRST_STEP = 0
GUIDED_TOUR_LAST_STEP = 7


class RecurringHelpSchedule(Base):
    """A repeating help request owned by one member.

    The schedule never replaces a help post: it points at a source HelpPost
    used as the template, and each due occurrence generates a fresh post that
    is recorded in `RecurringHelpOccurrence`. Weekday and month-day controls
    are optional and only meaningful for the weekly/biweekly and monthly
    cadences respectively; both are nullable so existing data (and simple
    daily schedules) need no values.
    """

    __tablename__ = "skillkind_recurring_help_schedule"
    __table_args__ = (
        CheckConstraint(
            f"cadence IN ({_RECURRENCE_CADENCES_SQL})",
            name="ck_recurring_schedule_cadence",
        ),
        CheckConstraint(
            f"status IN ({_SCHEDULE_STATUSES_SQL})",
            name="ck_recurring_schedule_status",
        ),
        CheckConstraint(
            f"interval_count BETWEEN 1 AND {RECURRENCE_MAX_INTERVAL}",
            name="ck_recurring_schedule_interval_range",
        ),
        CheckConstraint(
            "weekday IS NULL OR weekday BETWEEN 0 AND 6",
            name="ck_recurring_schedule_weekday_range",
        ),
        CheckConstraint(
            "month_day IS NULL OR month_day BETWEEN 1 AND 31",
            name="ck_recurring_schedule_month_day_range",
        ),
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name="ck_recurring_schedule_end_after_start",
        ),
        CheckConstraint(
            "occurrence_count >= 0",
            name="ck_recurring_schedule_occurrence_count_non_negative",
        ),
        CheckConstraint(
            "timezone_name <> ''",
            name="ck_recurring_schedule_timezone_present",
        ),
        # Owner listing: "my schedules, soonest first".
        Index(
            "ix_recurring_schedule_owner_next",
            "owner_id",
            "next_occurrence_at",
        ),
        Index(
            "ix_recurring_schedule_owner_status",
            "owner_id",
            "status",
        ),
        # Background processing: "which active schedules are due now?".
        Index(
            "ix_recurring_schedule_status_next",
            "status",
            "next_occurrence_at",
        ),
        # All schedules built from one template post.
        Index(
            "ix_recurring_schedule_source_post",
            "source_post_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    # Template post the generated occurrences copy their details from. Owned
    # data: deleting the template removes the schedule with it.
    source_post_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_help_post.id", ondelete="CASCADE"), index=True
    )
    cadence: Mapped[str] = mapped_column(
        String(16),
        default=RECURRENCE_WEEKLY,
        server_default=sa_text("'weekly'"),
        index=True,
    )
    # "Every N cadences" multiplier, e.g. cadence='weekly', interval_count=3.
    interval_count: Mapped[int] = mapped_column(
        default=1, server_default=sa_text("1")
    )
    # 0=Monday .. 6=Sunday for weekly/biweekly cadences.
    weekday: Mapped[int | None] = mapped_column(default=None, nullable=True)
    # 1..31 for the monthly cadence; clamped to the real month length in code.
    month_day: Mapped[int | None] = mapped_column(default=None, nullable=True)
    # Local time of day the occurrence should be created for, stored as HH:MM.
    start_time: Mapped[str] = mapped_column(
        String(16), default="", server_default=sa_text("''")
    )
    # IANA timezone the cadence is evaluated in (never blank).
    timezone_name: Mapped[str] = mapped_column(
        String(64),
        default=DEFAULT_SCHEDULE_TIMEZONE,
        server_default=sa_text("'UTC'"),
    )
    start_date: Mapped[datetime.date] = mapped_column(
        Date, default=None, server_default=func.current_date()
    )
    # Open-ended when NULL: the schedule keeps running until paused.
    end_date: Mapped[datetime.date | None] = mapped_column(
        Date, default=None, nullable=True
    )
    # Next moment a post should be generated. NULL once the schedule finished.
    next_occurrence_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True, index=True
    )
    last_occurrence_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    occurrence_count: Mapped[int] = mapped_column(
        default=0, server_default=sa_text("0")
    )
    status: Mapped[str] = mapped_column(
        String(16),
        default=SCHEDULE_STATUS_ACTIVE,
        server_default=sa_text("'active'"),
        index=True,
    )
    note: Mapped[str] = mapped_column(
        Text, default="", server_default=sa_text("''")
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    owner: Mapped["Subscriber"] = relationship(
        back_populates="recurring_help_schedules",
        foreign_keys=[owner_id],
        default=None,
    )
    source_post: Mapped["HelpPost"] = relationship(
        back_populates="recurring_schedules",
        foreign_keys=[source_post_id],
        default=None,
    )
    occurrences: Mapped[list["RecurringHelpOccurrence"]] = relationship(
        back_populates="schedule",
        default_factory=list,
        foreign_keys="RecurringHelpOccurrence.schedule_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RecurringHelpOccurrence.occurrence_at",
    )


class RecurringHelpOccurrence(Base):
    """One generated help post for one schedule occurrence.

    The (schedule, occurrence_at) pair is unique so a retried or concurrent
    generation pass can never create a duplicate post, and the generated post
    itself is unique so one post always belongs to at most one occurrence.
    """

    __tablename__ = "skillkind_recurring_help_occurrence"
    __table_args__ = (
        UniqueConstraint(
            "schedule_id",
            "occurrence_at",
            name="uq_recurring_occurrence_schedule_time",
        ),
        UniqueConstraint(
            "generated_post_id",
            name="uq_recurring_occurrence_generated_post",
        ),
        # Timeline of one schedule, newest last.
        Index(
            "ix_recurring_occurrence_schedule_time",
            "schedule_id",
            "occurrence_at",
        ),
        Index("ix_recurring_occurrence_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    schedule_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_recurring_help_schedule.id", ondelete="CASCADE"),
        index=True,
    )
    generated_post_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_help_post.id", ondelete="CASCADE"), index=True
    )
    # The scheduled moment this row satisfies (the idempotency key).
    occurrence_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=None, server_default=func.now()
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )

    schedule: Mapped["RecurringHelpSchedule"] = relationship(
        back_populates="occurrences",
        foreign_keys=[schedule_id],
        default=None,
    )
    generated_post: Mapped["HelpPost"] = relationship(
        back_populates="generated_occurrence",
        foreign_keys=[generated_post_id],
        default=None,
    )


class JobCheckIn(Base):
    """A scheduled check-in on an active job, agreed inside one thread.

    Created by one of the thread participants (poster or helper). The optional
    `client_key` gives callers an idempotency handle so a retried creation can
    never double-insert the same check-in.
    """

    __tablename__ = "skillkind_job_check_in"
    __table_args__ = (
        UniqueConstraint(
            "thread_id",
            "due_at",
            "prompt",
            name="uq_job_check_in_thread_due_prompt",
        ),
        UniqueConstraint(
            "thread_id",
            "client_key",
            name="uq_job_check_in_thread_client_key",
        ),
        CheckConstraint(
            f"status IN ({_CHECK_IN_STATUSES_SQL})",
            name="ck_job_check_in_status",
        ),
        CheckConstraint(
            "completed_at IS NULL OR status <> 'pending'",
            name="ck_job_check_in_completed_not_pending",
        ),
        CheckConstraint(
            "prompt <> ''",
            name="ck_job_check_in_prompt_present",
        ),
        # Thread timeline: every check-in for one conversation, in due order.
        Index("ix_job_check_in_thread_due", "thread_id", "due_at"),
        Index("ix_job_check_in_thread_status", "thread_id", "status"),
        # Reminder sweeps: "which pending check-ins are due?".
        Index("ix_job_check_in_status_due", "status", "due_at"),
        # A member's own upcoming check-ins.
        Index("ix_job_check_in_creator_due", "creator_id", "due_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    thread_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_message_thread.id", ondelete="CASCADE"),
        index=True,
    )
    creator_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    due_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=None, server_default=func.now()
    )
    # Short question shown to both sides, e.g. "Still on for 9am tomorrow?".
    prompt: Mapped[str] = mapped_column(
        String(CHECK_IN_PROMPT_MAX_LENGTH),
        default="",
        server_default=sa_text("''"),
    )
    note: Mapped[str] = mapped_column(
        String(CHECK_IN_NOTE_MAX_LENGTH),
        default="",
        server_default=sa_text("''"),
    )
    status: Mapped[str] = mapped_column(
        String(16),
        default=CHECK_IN_STATUS_PENDING,
        server_default=sa_text("'pending'"),
        index=True,
    )
    # Caller-supplied idempotency token; NULL rows are unconstrained.
    client_key: Mapped[str | None] = mapped_column(
        String(64), default=None, nullable=True
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    reminder_sent_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    thread: Mapped["MessageThread"] = relationship(
        back_populates="check_ins",
        foreign_keys=[thread_id],
        default=None,
    )
    creator: Mapped["Subscriber"] = relationship(
        back_populates="job_check_ins_created",
        foreign_keys=[creator_id],
        default=None,
    )


class OnboardingProgress(Base):
    """One row per subscriber tracking required onboarding and the tour.

    Absent for every pre-existing account: no backfill row is needed, and the
    app treats a missing row as "onboarding not started". Answers and the
    completed-step set are stored as compact JSON/text so new screens can be
    added without a schema change.
    """

    __tablename__ = "skillkind_onboarding_progress"
    __table_args__ = (
        UniqueConstraint(
            "subscriber_id", name="uq_onboarding_progress_subscriber"
        ),
        CheckConstraint(
            f"current_step BETWEEN {ONBOARDING_FIRST_STEP} "
            f"AND {ONBOARDING_LAST_STEP}",
            name="ck_onboarding_current_step_range",
        ),
        CheckConstraint(
            f"tour_current_step BETWEEN {GUIDED_TOUR_FIRST_STEP} "
            f"AND {GUIDED_TOUR_LAST_STEP}",
            name="ck_onboarding_tour_step_range",
        ),
        # Resume / gating lookups for partially onboarded members.
        Index(
            "ix_onboarding_progress_completed_step",
            "completed_at",
            "current_step",
        ),
        Index("ix_onboarding_progress_tour_completed", "tour_completed_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    subscriber_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    # The screen (1..12) the member must complete next.
    current_step: Mapped[int] = mapped_column(
        default=ONBOARDING_FIRST_STEP, server_default=sa_text("1")
    )
    # Normalized comma-separated list of finished step numbers, e.g. "1,2,3".
    completed_steps: Mapped[str] = mapped_column(
        String(120), default="", server_default=sa_text("''")
    )
    # JSON object of every answer captured across the tap-first screens
    # (profile basics, skills, languages, preferences). Text for portability.
    answers_json: Mapped[str] = mapped_column(
        Text, default="{}", server_default=sa_text("'{}'")
    )
    # JSON object of contextual permission choices (location, notifications,
    # photos), each recorded as granted / denied / skipped.
    permissions_json: Mapped[str] = mapped_column(
        Text, default="{}", server_default=sa_text("'{}'")
    )
    # Stamped once every one of the 12 screens is complete.
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    # Legacy 0..7 storage slot; 0 means "not started". The full UI tour step
    # is saved in answers_json["tour_step"] without changing this constraint.
    tour_current_step: Mapped[int] = mapped_column(
        default=GUIDED_TOUR_FIRST_STEP, server_default=sa_text("0")
    )
    tour_completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    subscriber: Mapped["Subscriber"] = relationship(
        back_populates="onboarding_progress",
        foreign_keys=[subscriber_id],
        default=None,
    )


# ---------------------------------------------------------------------------
# Private member blocking
# ---------------------------------------------------------------------------


class MemberBlock(Base):
    """One member privately blocking another member.

    Blocking is PRIVATE and DIRECTIONAL: a row records only that `blocker_id`
    chose to block `blocked_id`, and the blocked member is never told. The
    blocker sees the blocked member's content disappear from their own views.

    Communication checks, however, are SYMMETRIC: if a row exists in EITHER
    direction between two members, neither side may initiate or continue
    contact (help post offers, community replies, contact requests, job
    conversations, contact messages or non-contact messages). Only the member
    who created the row can remove it (unblock), which deletes the row.

    The unique (blocker, blocked) pair makes blocking idempotent, and a check
    constraint rejects self-blocking.
    """

    __tablename__ = "skillkind_member_block"
    __table_args__ = (
        UniqueConstraint(
            "blocker_id",
            "blocked_id",
            name="uq_member_block_blocker_blocked",
        ),
        CheckConstraint(
            "blocker_id <> blocked_id",
            name="ck_member_block_not_self",
        ),
        # "Who have I blocked?", newest first (private block list).
        Index(
            "ix_member_block_blocker_created",
            "blocker_id",
            "created_at",
        ),
        # Reverse lookup: "who has blocked this member?" — used by the symmetric
        # communication check without revealing anything to the blocked side.
        Index(
            "ix_member_block_blocked_created",
            "blocked_id",
            "created_at",
        ),
        # Direct pair existence probe in either direction.
        Index(
            "ix_member_block_blocked_blocker",
            "blocked_id",
            "blocker_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    blocker_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    blocked_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )

    blocker: Mapped["Subscriber"] = relationship(
        back_populates="blocks_created",
        foreign_keys=[blocker_id],
        default=None,
    )
    blocked: Mapped["Subscriber"] = relationship(
        back_populates="blocks_received",
        foreign_keys=[blocked_id],
        default=None,
    )


# ---------------------------------------------------------------------------
# Category search analytics (Premium request-success metrics)
# ---------------------------------------------------------------------------

# One row per category filter selection made by a signed-in member. These rows
# are the real source of "which categories are people searching for near here?"
# rankings shown in the Premium metrics section. Request VIEW counts stay on
# `HelpPost.view_count`, which remains the authoritative view metric.
CATEGORY_SEARCH_KEY_MAX_LENGTH = 48


class CategorySearchEvent(Base):
    """A single category filter selection recorded for Premium metrics.

    `subscriber_id` is nullable with ON DELETE SET NULL so the analytics history
    survives account deletion while no longer identifying the member. The
    optional coordinates are the searcher's approximate map centre at the time
    of the search, letting category rankings be scoped to a chosen radius.
    """

    __tablename__ = "skillkind_category_search_event"
    __table_args__ = (
        CheckConstraint(
            "btrim(category) <> ''",
            name="ck_category_search_event_category_not_blank",
        ),
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name="ck_category_search_event_latitude_range",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name="ck_category_search_event_longitude_range",
        ),
        # Ranking one category over a time window.
        Index(
            "ix_category_search_event_category_created",
            "category",
            "created_at",
        ),
        # Radius scans: bounding-box filter over rows that carry coordinates.
        Index(
            "ix_category_search_event_location_created",
            "latitude",
            "longitude",
            "created_at",
            postgresql_where=sa_text(
                "latitude IS NOT NULL AND longitude IS NOT NULL"
            ),
        ),
        # Recent-window sweeps that then group by category.
        Index(
            "ix_category_search_event_created_category",
            "created_at",
            "category",
        ),
        # "What has this member searched for?", newest first.
        Index(
            "ix_category_search_event_subscriber_created",
            "subscriber_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    category: Mapped[str] = mapped_column(
        String(CATEGORY_SEARCH_KEY_MAX_LENGTH), index=True
    )
    subscriber_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="SET NULL"),
        default=None,
        nullable=True,
        index=True,
    )
    latitude: Mapped[float | None] = mapped_column(
        Numeric(9, 6), default=None, nullable=True
    )
    longitude: Mapped[float | None] = mapped_column(
        Numeric(9, 6), default=None, nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=None,
        index=True,
    )

    subscriber: Mapped["Subscriber | None"] = relationship(
        foreign_keys=[subscriber_id], default=None
    )


# ---------------------------------------------------------------------------
# Password reset, non-contact messaging
# generalized content reports (schema only — no queries or UI yet).
# ---------------------------------------------------------------------------

# Password reset links follow the same discipline as email verification: only
# the SHA-256 hex digest of the emailed token is stored, and each row is
# single-use (`used_at`), with sibling rows invalidated on a fresh request.
PASSWORD_RESET_TOKEN_DIGEST_LENGTH = 64
PASSWORD_RESET_TOKEN_TTL_MINUTES = 60
PASSWORD_RESET_RESEND_COOLDOWN_SECONDS = 120
PASSWORD_RESET_MAX_SENDS_PER_DAY = 5

# Non-contact conversations: two members who are not contacts may still write
# to each other, and either side may keep replying.
NONCONTACT_STATUS_OPEN = "open"
NONCONTACT_STATUS_REPLIED = "replied"
NONCONTACT_STATUS_BLOCKED = "blocked"
NONCONTACT_STATUS_CLOSED = "closed"
NONCONTACT_CONVERSATION_STATUSES: list[str] = [
    NONCONTACT_STATUS_OPEN,
    NONCONTACT_STATUS_REPLIED,
    NONCONTACT_STATUS_BLOCKED,
    NONCONTACT_STATUS_CLOSED,
]
NONCONTACT_CONVERSATION_STATUS_LABELS: dict[str, str] = {
    NONCONTACT_STATUS_OPEN: "Awaiting reply",
    NONCONTACT_STATUS_REPLIED: "Replied",
    NONCONTACT_STATUS_BLOCKED: "Blocked",
    NONCONTACT_STATUS_CLOSED: "Closed",
}

# General member notifications (community, inbox and help activity).
NOTIFICATION_KIND_COMMUNITY_LIKE = "community_like"
NOTIFICATION_KIND_COMMUNITY_REPLY = "community_reply"
NOTIFICATION_KIND_INBOX_MESSAGE = "inbox_message"
NOTIFICATION_KIND_HELP_OFFER = "help_offer"
NOTIFICATION_KIND_HELP_CONFIRMED = "help_confirmed"
NOTIFICATION_KIND_SCHEDULE_PROPOSED = "schedule_proposed"
NOTIFICATION_KIND_SCHEDULE_CONFIRMED = "schedule_confirmed"
NOTIFICATION_KIND_SCHEDULE_DECLINED = "schedule_declined"
NOTIFICATION_KIND_DIRECT_HELP_REQUEST = "direct_help_request"
NOTIFICATION_KIND_REQUEST_ACCEPTED = "request_accepted"
NOTIFICATION_KIND_REQUEST_DECLINED = "request_declined"
NOTIFICATION_KIND_JOB_EXPIRED = "job_expired"
NOTIFICATION_KIND_JOB_RENEWED = "job_renewed"
NOTIFICATION_KIND_CANCELLATION_PROPOSED = "cancellation_proposed"
NOTIFICATION_KIND_CANCELLATION_ACCEPTED = "cancellation_accepted"
NOTIFICATION_KIND_CANCELLATION_DECLINED = "cancellation_declined"
NOTIFICATION_KIND_NO_SHOW_REPORTED = "no_show_reported"
NOTIFICATION_KIND_REQUESTS_IN_MY_FIELD = "requests_in_my_field"
# Existing schedule kinds remain the canonical reschedule notification values.
MEMBER_NOTIFICATION_KINDS: list[str] = [
    NOTIFICATION_KIND_COMMUNITY_LIKE,
    NOTIFICATION_KIND_COMMUNITY_REPLY,
    NOTIFICATION_KIND_INBOX_MESSAGE,
    NOTIFICATION_KIND_HELP_OFFER,
    NOTIFICATION_KIND_HELP_CONFIRMED,
    NOTIFICATION_KIND_SCHEDULE_PROPOSED,
    NOTIFICATION_KIND_SCHEDULE_CONFIRMED,
    NOTIFICATION_KIND_SCHEDULE_DECLINED,
    NOTIFICATION_KIND_DIRECT_HELP_REQUEST,
    NOTIFICATION_KIND_REQUEST_ACCEPTED,
    NOTIFICATION_KIND_REQUEST_DECLINED,
    NOTIFICATION_KIND_JOB_EXPIRED,
    NOTIFICATION_KIND_JOB_RENEWED,
    NOTIFICATION_KIND_CANCELLATION_PROPOSED,
    NOTIFICATION_KIND_CANCELLATION_ACCEPTED,
    NOTIFICATION_KIND_CANCELLATION_DECLINED,
    NOTIFICATION_KIND_NO_SHOW_REPORTED,
    NOTIFICATION_KIND_REQUESTS_IN_MY_FIELD,
]
MEMBER_NOTIFICATION_KIND_LABELS: dict[str, str] = {
    NOTIFICATION_KIND_COMMUNITY_LIKE: "Community like",
    NOTIFICATION_KIND_COMMUNITY_REPLY: "Community reply",
    NOTIFICATION_KIND_INBOX_MESSAGE: "New message",
    NOTIFICATION_KIND_HELP_OFFER: "Help offer",
    NOTIFICATION_KIND_HELP_CONFIRMED: "Help confirmed",
    NOTIFICATION_KIND_SCHEDULE_PROPOSED: "New time proposed",
    NOTIFICATION_KIND_SCHEDULE_CONFIRMED: "New time confirmed",
    NOTIFICATION_KIND_SCHEDULE_DECLINED: "New time declined",
    NOTIFICATION_KIND_DIRECT_HELP_REQUEST: "Direct help requested",
    NOTIFICATION_KIND_REQUEST_ACCEPTED: "Request accepted",
    NOTIFICATION_KIND_REQUEST_DECLINED: "Request declined",
    NOTIFICATION_KIND_JOB_EXPIRED: "Help request expired",
    NOTIFICATION_KIND_JOB_RENEWED: "Help request renewed",
    NOTIFICATION_KIND_CANCELLATION_PROPOSED: "Cancellation proposed",
    NOTIFICATION_KIND_CANCELLATION_ACCEPTED: "Cancellation confirmed",
    NOTIFICATION_KIND_CANCELLATION_DECLINED: "Cancellation declined",
    NOTIFICATION_KIND_NO_SHOW_REPORTED: "Private no-show report",
}
MEMBER_NOTIFICATION_KIND_ICONS: dict[str, str] = {
    NOTIFICATION_KIND_COMMUNITY_LIKE: "heart",
    NOTIFICATION_KIND_COMMUNITY_REPLY: "message-square",
    NOTIFICATION_KIND_INBOX_MESSAGE: "mail",
    NOTIFICATION_KIND_HELP_OFFER: "hand-helping",
    NOTIFICATION_KIND_HELP_CONFIRMED: "badge-check",
    NOTIFICATION_KIND_SCHEDULE_PROPOSED: "calendar-clock",
    NOTIFICATION_KIND_SCHEDULE_CONFIRMED: "calendar-check",
    NOTIFICATION_KIND_SCHEDULE_DECLINED: "calendar-x",
    NOTIFICATION_KIND_DIRECT_HELP_REQUEST: "hand-helping",
    NOTIFICATION_KIND_REQUEST_ACCEPTED: "badge-check",
    NOTIFICATION_KIND_REQUEST_DECLINED: "circle-x",
    NOTIFICATION_KIND_JOB_EXPIRED: "clock",
    NOTIFICATION_KIND_JOB_RENEWED: "refresh-cw",
    NOTIFICATION_KIND_CANCELLATION_PROPOSED: "circle-help",
    NOTIFICATION_KIND_CANCELLATION_ACCEPTED: "calendar-x",
    NOTIFICATION_KIND_CANCELLATION_DECLINED: "shield-check",
    NOTIFICATION_KIND_NO_SHOW_REPORTED: "shield-alert",
    NOTIFICATION_KIND_REQUESTS_IN_MY_FIELD: "hand-helping",
}
_MEMBER_NOTIFICATION_KINDS_SQL = ", ".join(
    f"'{kind}'" for kind in MEMBER_NOTIFICATION_KINDS
)

# Scheduled task email reminders: exactly two offsets before the due time.
REMINDER_OFFSET_24H = 1440
REMINDER_OFFSET_1H = 60
REMINDER_OFFSET_MINUTES: list[int] = [REMINDER_OFFSET_24H, REMINDER_OFFSET_1H]
REMINDER_OFFSET_LABELS: dict[int, str] = {
    REMINDER_OFFSET_24H: "24 hours before",
    REMINDER_OFFSET_1H: "1 hour before",
}

# Generalized unsafe-content reports (kept separate from the completed-task
# `SafetyReport`, whose behaviour is unchanged).
REPORT_TARGET_JOB_MESSAGE = "job_message"
REPORT_TARGET_PROFILE = "profile"
REPORT_TARGET_COMMUNITY_TOPIC = "community_topic"
REPORT_TARGET_COMMUNITY_COMMENT = "community_comment"
REPORT_TARGET_CONTACT_MESSAGE = "contact_message"
REPORT_TARGET_NONCONTACT_MESSAGE = "noncontact_message"
CONTENT_REPORT_TARGET_TYPES: list[str] = [
    REPORT_TARGET_PROFILE,
    REPORT_TARGET_COMMUNITY_TOPIC,
    REPORT_TARGET_COMMUNITY_COMMENT,
    REPORT_TARGET_CONTACT_MESSAGE,
    REPORT_TARGET_NONCONTACT_MESSAGE,
    REPORT_TARGET_JOB_MESSAGE,
]
CONTENT_REPORT_TARGET_LABELS: dict[str, str] = {
    REPORT_TARGET_JOB_MESSAGE: "Help request",
    REPORT_TARGET_PROFILE: "Profile",
    REPORT_TARGET_COMMUNITY_TOPIC: "Community topic",
    REPORT_TARGET_COMMUNITY_COMMENT: "Community comment",
    REPORT_TARGET_CONTACT_MESSAGE: "Direct message",
    REPORT_TARGET_NONCONTACT_MESSAGE: "Non-contact message",
}
_CONTENT_REPORT_TARGET_TYPES_SQL = ", ".join(
    f"'{target}'" for target in CONTENT_REPORT_TARGET_TYPES
)
_SAFETY_CATEGORIES_SQL = ", ".join(
    f"'{category}'" for category in SAFETY_REPORT_CATEGORIES
)
_SAFETY_STATUSES_SQL = ", ".join(
    f"'{status}'" for status in SAFETY_REPORT_STATUSES
)


# ---------------------------------------------------------------------------
# Saved discovery search alerts, help-post bookmarks, community events
# (schema only — no queries, state or UI in this pass).
# ---------------------------------------------------------------------------

SAVED_SEARCH_LABEL_MAX_LENGTH = 120
# SHA-256 hex digest of the normalized filter set, used to de-duplicate a saved
# search per subscriber without comparing every column.
SAVED_SEARCH_FINGERPRINT_LENGTH = 64
SAVED_SEARCH_KEYWORD_MAX_LENGTH = 200
SAVED_SEARCH_CATEGORY_TAGS_MAX_LENGTH = 255
SAVED_SEARCH_MAX_PER_SUBSCRIBER = 20

# Only these legacy values belong to the database event_type vocabulary.
EVENT_TYPE_GATHERING = "gathering"
EVENT_TYPE_TEAMWORK = "teamwork"
COMMUNITY_EVENT_TYPES: list[str] = [
    EVENT_TYPE_GATHERING,
    EVENT_TYPE_TEAMWORK,
]

# Application-level request categories, not database event_type values.
EVENT_REQUEST_CATEGORIES: list[str] = [
    "agriculture",
    "beach_cleanups",
    "festival_volunteers",
    "event_volunteers",
    "community_builds",
    "tree_planting",
    "playground_builds",
    "bioblitz",
    "disaster_relief",
    "historic_restorations",
    "construction",
    "cook",
    "labour",
    "media",
    "sports",
    "tourism",
    "spirituality",
    "first_aid",
    "other",
]
COMMUNITY_EVENT_TYPE_OPTIONS: list[str] = list(EVENT_REQUEST_CATEGORIES)
COMMUNITY_EVENT_TYPE_LABELS: dict[str, str] = {
    EVENT_TYPE_GATHERING: "Gathering",
    EVENT_TYPE_TEAMWORK: "Teamwork",
    "agriculture": "Agriculture",
    "beach_cleanups": "Beach Clean-Ups",
    "festival_volunteers": "Festival Volunteers",
    "event_volunteers": "Event Volunteers",
    "community_builds": "Community Builds",
    "tree_planting": "Tree Planting",
    "playground_builds": "Playground Builds",
    "bioblitz": "BioBlitz",
    "disaster_relief": "Disaster Relief",
    "historic_restorations": "Historic Restorations",
    "construction": "Construction",
    "cook": "Cook",
    "labour": "Labour",
    "media": "Media",
    "sports": "Sports",
    "tourism": "Tourism",
    "spirituality": "Spirituality",
    "first_aid": "First Aid",
    "other": "Other",
}
COMMUNITY_EVENT_TYPE_ICONS: dict[str, str] = {
    EVENT_TYPE_GATHERING: "party-popper",
    EVENT_TYPE_TEAMWORK: "users-round",
    "agriculture": "sprout",
    "beach_cleanups": "waves",
    "festival_volunteers": "music",
    "event_volunteers": "calendar-heart",
    "community_builds": "house",
    "tree_planting": "trees",
    "playground_builds": "blocks",
    "bioblitz": "bug",
    "disaster_relief": "hand-heart",
    "historic_restorations": "landmark",
    "construction": "hard-hat",
    "cook": "chef-hat",
    "labour": "hammer",
    "media": "camera",
    "sports": "trophy",
    "tourism": "compass",
    "spirituality": "flower-2",
    "first_aid": "heart-pulse",
    "other": "circle-ellipsis",
}
EVENT_REQUEST_CATEGORY_LABELS: dict[str, str] = {
    category: COMMUNITY_EVENT_TYPE_LABELS[category]
    for category in EVENT_REQUEST_CATEGORIES
}
EVENT_REQUEST_CATEGORY_ICONS: dict[str, str] = {
    category: COMMUNITY_EVENT_TYPE_ICONS[category]
    for category in EVENT_REQUEST_CATEGORIES
}

_COMMUNITY_EVENT_TYPES_SQL = ", ".join(
    f"'{kind}'" for kind in COMMUNITY_EVENT_TYPES
)

EVENT_STATUS_ACTIVE = "active"
EVENT_STATUS_CANCELLED = "cancelled"
EVENT_STATUS_COMPLETED = "completed"
COMMUNITY_EVENT_STATUSES: list[str] = [
    EVENT_STATUS_ACTIVE,
    EVENT_STATUS_CANCELLED,
    EVENT_STATUS_COMPLETED,
]
COMMUNITY_EVENT_STATUS_LABELS: dict[str, str] = {
    EVENT_STATUS_ACTIVE: "Active",
    EVENT_STATUS_CANCELLED: "Cancelled",
    EVENT_STATUS_COMPLETED: "Completed",
}
_COMMUNITY_EVENT_STATUSES_SQL = ", ".join(
    f"'{status}'" for status in COMMUNITY_EVENT_STATUSES
)

COMMUNITY_EVENT_TITLE_MAX_LENGTH = 160
COMMUNITY_EVENT_PLACE_NAME_MAX_LENGTH = 200
COMMUNITY_EVENT_DETAILS_MAX_WORDS = 2000
COMMUNITY_EVENT_MAX_CAPACITY = 500
DEFAULT_EVENT_CAPACITY = 1

# Join requests: a member asks the host to attend; the host confirms or
# declines, and the member may cancel their own request at any time.
EVENT_JOIN_PENDING = "pending"
EVENT_JOIN_CONFIRMED = "confirmed"
EVENT_JOIN_DECLINED = "declined"
EVENT_JOIN_CANCELLED = "cancelled"
EVENT_JOIN_STATUSES: list[str] = [
    EVENT_JOIN_PENDING,
    EVENT_JOIN_CONFIRMED,
    EVENT_JOIN_DECLINED,
    EVENT_JOIN_CANCELLED,
]
EVENT_JOIN_STATUS_LABELS: dict[str, str] = {
    EVENT_JOIN_PENDING: "Requested",
    EVENT_JOIN_CONFIRMED: "Confirmed",
    EVENT_JOIN_DECLINED: "Declined",
    EVENT_JOIN_CANCELLED: "Cancelled",
}
_EVENT_JOIN_STATUSES_SQL = ", ".join(
    f"'{status}'" for status in EVENT_JOIN_STATUSES
)
EVENT_JOIN_NOTE_MAX_LENGTH = 500


class SavedSearchAlert(Base):
    """A saved discovery search a member wants to be alerted about.

    Every filter the Discover screen exposes is stored in its own normalized
    column so alert matching can be expressed in SQL later. `fingerprint` is the
    SHA-256 hex digest of the normalized filter set, computed in app code, and
    is unique per subscriber so saving the same search twice is idempotent.
    """

    __tablename__ = "skillkind_saved_search_alert"
    __table_args__ = (
        UniqueConstraint(
            "subscriber_id",
            "fingerprint",
            name="uq_saved_search_alert_subscriber_fingerprint",
        ),
        CheckConstraint(
            "char_length(fingerprint) = 64",
            name="ck_saved_search_alert_fingerprint_sha256",
        ),
        CheckConstraint(
            "radius_km >= 0 AND radius_km <= 20000",
            name="ck_saved_search_alert_radius_range",
        ),
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name="ck_saved_search_alert_latitude_range",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name="ck_saved_search_alert_longitude_range",
        ),
        CheckConstraint(
            "min_duration_minutes >= 0",
            name="ck_saved_search_alert_min_duration_non_negative",
        ),
        CheckConstraint(
            "max_duration_minutes >= 0",
            name="ck_saved_search_alert_max_duration_non_negative",
        ),
        CheckConstraint(
            "max_duration_minutes = 0 OR min_duration_minutes = 0 "
            "OR max_duration_minutes >= min_duration_minutes",
            name="ck_saved_search_alert_duration_order",
        ),
        CheckConstraint(
            "match_count >= 0",
            name="ck_saved_search_alert_match_count_non_negative",
        ),
        # "My saved searches", newest first.
        Index(
            "ix_saved_search_alert_subscriber_created",
            "subscriber_id",
            "created_at",
        ),
        # Alert sweeps: only enabled searches, oldest checked first.
        Index(
            "ix_saved_search_alert_enabled_checked",
            "is_enabled",
            "last_checked_at",
            postgresql_where=sa_text("is_enabled = true"),
        ),
        Index(
            "ix_saved_search_alert_subscriber_enabled",
            "subscriber_id",
            "is_enabled",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    subscriber_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    # SHA-256 hex digest of the normalized filter set (computed in app code).
    fingerprint: Mapped[str] = mapped_column(
        String(SAVED_SEARCH_FINGERPRINT_LENGTH), index=True
    )
    label: Mapped[str] = mapped_column(
        String(SAVED_SEARCH_LABEL_MAX_LENGTH),
        default="",
        server_default=sa_text("''"),
    )
    # --- normalized filter fields -----------------------------------------
    keyword: Mapped[str] = mapped_column(
        String(SAVED_SEARCH_KEYWORD_MAX_LENGTH),
        default="",
        server_default=sa_text("''"),
    )
    # Comma-separated canonical category keys; empty means "any category".
    category_tags: Mapped[str] = mapped_column(
        String(SAVED_SEARCH_CATEGORY_TAGS_MAX_LENGTH),
        default="",
        server_default=sa_text("''"),
    )
    # Comma-separated reward keys; empty means "any reward".
    reward_types: Mapped[str] = mapped_column(
        String(255), default="", server_default=sa_text("''")
    )
    urgency: Mapped[str] = mapped_column(
        String(24), default="", server_default=sa_text("''")
    )
    city: Mapped[str] = mapped_column(
        String(120), default="", server_default=sa_text("''"), index=True
    )
    country: Mapped[str] = mapped_column(
        String(120), default="", server_default=sa_text("''")
    )
    latitude: Mapped[float | None] = mapped_column(
        Numeric(9, 6), default=None, nullable=True
    )
    longitude: Mapped[float | None] = mapped_column(
        Numeric(9, 6), default=None, nullable=True
    )
    radius_km: Mapped[int] = mapped_column(
        default=0, server_default=sa_text("0")
    )
    # 0 on either bound means "unbounded" on that side.
    min_duration_minutes: Mapped[int] = mapped_column(
        default=0, server_default=sa_text("0")
    )
    max_duration_minutes: Mapped[int] = mapped_column(
        default=0, server_default=sa_text("0")
    )
    # Comma-separated language codes; empty means "any language".
    languages: Mapped[str] = mapped_column(
        String(255), default="", server_default=sa_text("''")
    )
    verified_only: Mapped[bool] = mapped_column(
        default=False, server_default=sa_text("false")
    )
    with_photos_only: Mapped[bool] = mapped_column(
        default=False, server_default=sa_text("false")
    )
    # --- alert bookkeeping -------------------------------------------------
    is_enabled: Mapped[bool] = mapped_column(
        default=True, server_default=sa_text("true"), index=True
    )
    notify_by_email: Mapped[bool] = mapped_column(
        default=True, server_default=sa_text("true")
    )
    match_count: Mapped[int] = mapped_column(
        default=0, server_default=sa_text("0")
    )
    last_match_help_post_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_help_post.id", ondelete="SET NULL"),
        default=None,
        nullable=True,
    )
    last_checked_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    last_notified_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    subscriber: Mapped["Subscriber"] = relationship(
        foreign_keys=[subscriber_id], default=None
    )


class HelpPostBookmark(Base):
    """A member bookmarking a help request so they can find it again.

    Exactly one bookmark per (subscriber, help post) pair, which makes saving
    idempotent; unsaving deletes the row. A member cannot usefully bookmark
    their own request, but that is left to app code rather than a constraint
    (the two ids live in different tables).
    """

    __tablename__ = "skillkind_help_post_bookmark"
    __table_args__ = (
        UniqueConstraint(
            "subscriber_id",
            "help_post_id",
            name="uq_help_post_bookmark_subscriber_post",
        ),
        # "My bookmarks", newest first.
        Index(
            "ix_help_post_bookmark_subscriber_created",
            "subscriber_id",
            "created_at",
        ),
        # "How many members saved this request?"
        Index(
            "ix_help_post_bookmark_post_created",
            "help_post_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    subscriber_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    help_post_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_help_post.id", ondelete="CASCADE"), index=True
    )
    note: Mapped[str] = mapped_column(
        String(255), default="", server_default=sa_text("''")
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )

    subscriber: Mapped["Subscriber"] = relationship(
        foreign_keys=[subscriber_id], default=None
    )
    help_post: Mapped["HelpPost"] = relationship(
        foreign_keys=[help_post_id], default=None
    )


class CommunityEvent(Base):
    """A community gathering or teamwork event hosted by a subscriber.

    Only APPROXIMATE public place fields are stored: `place_name`, city and
    country plus a coarse latitude/longitude the host chose to publish. No exact
    address is ever kept here — the host shares that privately with confirmed
    attendees.
    """

    __tablename__ = "skillkind_community_event"
    __table_args__ = (
        CheckConstraint(
            f"event_type IN ({_COMMUNITY_EVENT_TYPES_SQL})",
            name="ck_community_event_type",
        ),
        CheckConstraint(
            f"status IN ({_COMMUNITY_EVENT_STATUSES_SQL})",
            name="ck_community_event_status",
        ),
        CheckConstraint(
            "btrim(title) <> ''",
            name="ck_community_event_title_not_blank",
        ),
        CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at >= starts_at",
            name="ck_community_event_time_order",
        ),
        CheckConstraint(
            "capacity >= 0 AND capacity <= 500",
            name="ck_community_event_capacity_range",
        ),
        CheckConstraint(
            "confirmed_count >= 0",
            name="ck_community_event_confirmed_count_non_negative",
        ),
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name="ck_community_event_latitude_range",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name="ck_community_event_longitude_range",
        ),
        # Upcoming-events feed: active events by start time.
        Index(
            "ix_community_event_status_starts",
            "status",
            "starts_at",
        ),
        # "Events I host", soonest first.
        Index(
            "ix_community_event_host_starts",
            "host_id",
            "starts_at",
        ),
        Index(
            "ix_community_event_host_created",
            "host_id",
            "created_at",
        ),
        Index(
            "ix_community_event_type_starts",
            "event_type",
            "starts_at",
        ),
        # Map / area browsing over events that published a coarse point.
        Index(
            "ix_community_event_location_starts",
            "latitude",
            "longitude",
            "starts_at",
            postgresql_where=sa_text(
                "latitude IS NOT NULL AND longitude IS NOT NULL"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    host_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(24),
        default=EVENT_TYPE_GATHERING,
        server_default=sa_text("'gathering'"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(COMMUNITY_EVENT_TITLE_MAX_LENGTH))
    details: Mapped[str] = mapped_column(
        Text, default="", server_default=sa_text("''")
    )
    photo_paths: Mapped[str] = mapped_column(
        Text, default="[]", server_default=sa_text("'[]'"), nullable=True
    )
    reward_details: Mapped[str] = mapped_column(
        Text, default="", server_default=sa_text("''"), nullable=True
    )
    # PUBLIC approximate place only — never an exact address.
    place_name: Mapped[str] = mapped_column(
        String(COMMUNITY_EVENT_PLACE_NAME_MAX_LENGTH),
        default="",
        server_default=sa_text("''"),
    )
    city: Mapped[str] = mapped_column(
        String(120), default="", server_default=sa_text("''"), index=True
    )
    country: Mapped[str] = mapped_column(
        String(120), default="", server_default=sa_text("''")
    )
    latitude: Mapped[float | None] = mapped_column(
        Numeric(9, 6), default=None, nullable=True
    )
    longitude: Mapped[float | None] = mapped_column(
        Numeric(9, 6), default=None, nullable=True
    )
    starts_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True, index=True
    )
    ends_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    # 0 means "no limit".
    capacity: Mapped[int] = mapped_column(
        default=DEFAULT_EVENT_CAPACITY, server_default=sa_text("1")
    )
    # Denormalised confirmed attendee tally so a card renders without a count.
    confirmed_count: Mapped[int] = mapped_column(
        default=0, server_default=sa_text("0")
    )
    status: Mapped[str] = mapped_column(
        String(16),
        default=EVENT_STATUS_ACTIVE,
        server_default=sa_text("'active'"),
        index=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    cancelled_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    host: Mapped["Subscriber"] = relationship(
        foreign_keys=[host_id], default=None
    )
    join_requests: Mapped[list["EventJoinRequest"]] = relationship(
        back_populates="event",
        default_factory=list,
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="EventJoinRequest.created_at",
    )


class EventJoinRequest(Base):
    """A member asking to attend a community event.

    One row per (event, member): re-requesting reuses the row by moving `status`
    back to pending. `host_id` is denormalised from the event so the host's
    "requests to review" queue needs no join, and a check constraint stops a
    host requesting to join their own event.
    """

    __tablename__ = "skillkind_event_join_request"
    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "member_id",
            name="uq_event_join_request_event_member",
        ),
        CheckConstraint(
            f"status IN ({_EVENT_JOIN_STATUSES_SQL})",
            name="ck_event_join_request_status",
        ),
        CheckConstraint(
            "host_id <> member_id",
            name="ck_event_join_request_host_not_member",
        ),
        CheckConstraint(
            "responded_at IS NULL OR responded_at >= created_at",
            name="ck_event_join_request_response_after_creation",
        ),
        # Host review queue: pending requests across an event, oldest first.
        Index(
            "ix_event_join_request_event_status_created",
            "event_id",
            "status",
            "created_at",
        ),
        Index(
            "ix_event_join_request_host_status_created",
            "host_id",
            "status",
            "created_at",
        ),
        # "Events I joined / requested", newest first.
        Index(
            "ix_event_join_request_member_created",
            "member_id",
            "created_at",
        ),
        Index(
            "ix_event_join_request_member_status",
            "member_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_community_event.id", ondelete="CASCADE"),
        index=True,
    )
    member_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    # Denormalised host for fast "requests awaiting my response" lookups.
    host_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(16),
        default=EVENT_JOIN_PENDING,
        server_default=sa_text("'pending'"),
        index=True,
    )
    # Optional note the attendee sends with their request.
    note: Mapped[str] = mapped_column(
        String(EVENT_JOIN_NOTE_MAX_LENGTH),
        default="",
        server_default=sa_text("''"),
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    responded_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    confirmed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    declined_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    cancelled_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    event: Mapped["CommunityEvent"] = relationship(
        back_populates="join_requests", default=None
    )
    member: Mapped["Subscriber"] = relationship(
        foreign_keys=[member_id], default=None
    )
    host: Mapped["Subscriber"] = relationship(
        foreign_keys=[host_id], default=None
    )


class PasswordResetToken(Base):
    """A one-time password reset link issued to a subscriber.

    Only the SHA-256 hex digest of the token is stored, so a database leak
    cannot be replayed. `used_at` marks redemption (single-use, enforced in app
    code) and `invalidated_at` retires any sibling row when a fresh link is
    requested or the password changes by another route. Request metadata keeps
    per-subscriber and per-origin throttling possible without a second table.
    """

    __tablename__ = "skillkind_password_reset_token"
    __table_args__ = (
        UniqueConstraint("token_digest", name="uq_password_reset_token_digest"),
        CheckConstraint(
            "char_length(token_digest) = 64",
            name="ck_password_reset_token_digest_sha256",
        ),
        CheckConstraint(
            "expires_at > created_at",
            name="ck_password_reset_token_expiry_after_creation",
        ),
        CheckConstraint(
            "send_attempts >= 0",
            name="ck_password_reset_token_send_attempts_non_negative",
        ),
        # Throttling / invalidation: the live tokens for one subscriber.
        Index(
            "ix_password_reset_token_subscriber_created",
            "subscriber_id",
            "created_at",
        ),
        # "Is this link still usable?" plus expiry sweeps.
        Index(
            "ix_password_reset_token_used_expires",
            "used_at",
            "expires_at",
        ),
        Index(
            "ix_password_reset_token_email_created",
            "email",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    subscriber_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    # SHA-256 hex digest of the single-use token. Never the plaintext token.
    token_digest: Mapped[str] = mapped_column(
        String(PASSWORD_RESET_TOKEN_DIGEST_LENGTH), index=True
    )
    # Address the link was sent to, so an address change invalidates it.
    email: Mapped[str] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=None
    )
    sent_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    used_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    invalidated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    send_attempts: Mapped[int] = mapped_column(
        default=0, server_default=sa_text("0")
    )
    last_attempt_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    provider_message_id: Mapped[str] = mapped_column(
        String(120), default="", server_default=sa_text("''")
    )
    last_error: Mapped[str] = mapped_column(
        String(255), default="", server_default=sa_text("''")
    )
    requested_ip: Mapped[str] = mapped_column(
        String(64), default="", server_default=sa_text("''"), index=True
    )
    requested_user_agent: Mapped[str] = mapped_column(
        String(255), default="", server_default=sa_text("''")
    )
    consumed_ip: Mapped[str] = mapped_column(
        String(64), default="", server_default=sa_text("''")
    )

    subscriber: Mapped["Subscriber"] = relationship(
        back_populates="password_reset_tokens", default=None
    )


class NonContactConversation(Base):
    """A message thread between two members who are not contacts.

    Exactly one row exists per unordered pair of distinct subscribers. The
    initiator (`initiator_id`, the searching member who wrote first) and the
    `recipient_id` are stored explicitly, and a functional unique index over
    `least(...)`/`greatest(...)` guarantees the reversed pair cannot also be
    created. Replies are always allowed while the two remain non-contacts.
    """

    __tablename__ = "skillkind_noncontact_conversation"
    __table_args__ = (
        UniqueConstraint(
            "initiator_id",
            "recipient_id",
            name="uq_noncontact_conversation_pair",
        ),
        CheckConstraint(
            "initiator_id <> recipient_id",
            name="ck_noncontact_conversation_not_self",
        ),
        CheckConstraint(
            "status IN ('open', 'replied', 'blocked', 'closed')",
            name="ck_noncontact_conversation_status",
        ),
        CheckConstraint(
            "message_count >= 0",
            name="ck_noncontact_conversation_message_count_non_negative",
        ),
        # One conversation per unordered pair, in either direction.
        Index(
            "uq_noncontact_conversation_unordered_pair",
            sa_text("least(initiator_id, recipient_id)"),
            sa_text("greatest(initiator_id, recipient_id)"),
            unique=True,
        ),
        # Inbox listings for either participant, newest activity first.
        Index(
            "ix_noncontact_conversation_initiator_last",
            "initiator_id",
            "last_message_at",
        ),
        Index(
            "ix_noncontact_conversation_recipient_last",
            "recipient_id",
            "last_message_at",
        ),
        Index(
            "ix_noncontact_conversation_status_last",
            "status",
            "last_message_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    initiator_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(24),
        default=NONCONTACT_STATUS_OPEN,
        server_default=sa_text("'open'"),
        index=True,
    )
    subject: Mapped[str] = mapped_column(
        String(200), default="", server_default=sa_text("''")
    )
    is_open: Mapped[bool] = mapped_column(
        default=True, server_default=sa_text("true")
    )
    # Denormalised preview so an inbox renders without an aggregate query.
    message_count: Mapped[int] = mapped_column(
        default=0, server_default=sa_text("0")
    )
    last_message_preview: Mapped[str] = mapped_column(
        String(255), default="", server_default=sa_text("''")
    )
    last_message_sender_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="SET NULL"),
        default=None,
        nullable=True,
    )
    last_message_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    closed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    blocked_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    blocked_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="SET NULL"),
        default=None,
        nullable=True,
    )

    initiator: Mapped["Subscriber"] = relationship(
        foreign_keys=[initiator_id], default=None
    )
    recipient: Mapped["Subscriber"] = relationship(
        foreign_keys=[recipient_id], default=None
    )
    messages: Mapped[list["NonContactMessage"]] = relationship(
        back_populates="conversation",
        default_factory=list,
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="NonContactMessage.created_at",
    )


class NonContactMessage(Base):
    """A single message inside a non-contact conversation."""

    __tablename__ = "skillkind_noncontact_message"
    __table_args__ = (
        CheckConstraint(
            "sender_id <> recipient_id",
            name="ck_noncontact_message_not_self",
        ),
        CheckConstraint(
            "btrim(body) <> ''",
            name="ck_noncontact_message_body_not_blank",
        ),
        # Chronological rendering of one conversation.
        Index(
            "ix_noncontact_message_conversation_created",
            "conversation_id",
            "created_at",
        ),
        # Unread badge counts for the recipient.
        Index(
            "ix_noncontact_message_recipient_read",
            "recipient_id",
            "read_at",
        ),
        Index(
            "ix_noncontact_message_sender_created",
            "sender_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_noncontact_conversation.id", ondelete="CASCADE"),
        index=True,
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    read_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    conversation: Mapped["NonContactConversation"] = relationship(
        back_populates="messages", default=None
    )
    sender: Mapped["Subscriber"] = relationship(
        foreign_keys=[sender_id], default=None
    )
    recipient: Mapped["Subscriber"] = relationship(
        foreign_keys=[recipient_id], default=None
    )


class MemberNotification(Base):
    """A general in-app notification for one member.

    Covers community likes and replies, inbox messages and help activity. The
    optional source identifiers describe what triggered the notification so it
    can deep-link and be de-duplicated in app code via
    (recipient, kind, source ids, actor).
    """

    __tablename__ = "skillkind_member_notification"
    __table_args__ = (
        CheckConstraint(
            f"kind IN ({_MEMBER_NOTIFICATION_KINDS_SQL})",
            name="ck_member_notification_kind",
        ),
        CheckConstraint(
            "btrim(title) <> ''",
            name="ck_member_notification_title_not_blank",
        ),
        CheckConstraint(
            "actor_id IS NULL OR actor_id <> recipient_id",
            name="ck_member_notification_actor_not_recipient",
        ),
        # Newest-first notification list for one member.
        Index(
            "ix_member_notification_recipient_created",
            "recipient_id",
            "created_at",
        ),
        # Unread counter badge.
        Index(
            "ix_member_notification_recipient_unread",
            "recipient_id",
            "is_read",
            postgresql_where=sa_text("is_read = false"),
        ),
        Index(
            "ix_member_notification_recipient_kind_unread",
            "recipient_id",
            "kind",
            "is_read",
        ),
        # De-duplication lookup for a repeated source event.
        Index(
            "ix_member_notification_dedupe",
            "recipient_id",
            "kind",
            "community_topic_id",
            "community_comment_id",
            "help_post_id",
            "actor_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(
        Text, default="", server_default=sa_text("''")
    )
    # Who caused the notification, when known. SET NULL keeps the notice if
    # that account is later deleted.
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="SET NULL"),
        default=None,
        nullable=True,
        index=True,
    )
    # Optional source entities (exactly the ones relevant to `kind`).
    community_topic_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_community_topic.id", ondelete="CASCADE"),
        default=None,
        nullable=True,
        index=True,
    )
    community_comment_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_community_comment.id", ondelete="CASCADE"),
        default=None,
        nullable=True,
        index=True,
    )
    help_post_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_help_post.id", ondelete="CASCADE"),
        default=None,
        nullable=True,
        index=True,
    )
    contact_link_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_contact_link.id", ondelete="CASCADE"),
        default=None,
        nullable=True,
        index=True,
    )
    noncontact_conversation_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_noncontact_conversation.id", ondelete="CASCADE"),
        default=None,
        nullable=True,
        index=True,
    )
    # Free-form deep link target resolved by the UI layer later.
    target_route: Mapped[str] = mapped_column(
        String(255), default="", server_default=sa_text("''")
    )
    is_read: Mapped[bool] = mapped_column(
        default=False, server_default=sa_text("false")
    )
    read_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )

    recipient: Mapped["Subscriber"] = relationship(
        back_populates="notifications",
        foreign_keys=[recipient_id],
        default=None,
    )
    actor: Mapped["Subscriber | None"] = relationship(
        foreign_keys=[actor_id], default=None
    )


class TaskReminderDelivery(Base):
    """One emailed reminder for a scheduled task, at one offset.

    The unique (help post, recipient, offset) key is the duplicate-send guard:
    a row is inserted before sending, so a second attempt for the same reminder
    conflicts instead of emailing twice. `sent_at` confirms delivery and the
    provider / error columns record the Resend outcome for retries.
    """

    __tablename__ = "skillkind_task_reminder_delivery"
    __table_args__ = (
        UniqueConstraint(
            "help_post_id",
            "recipient_id",
            "offset_minutes",
            name="uq_task_reminder_post_recipient_offset",
        ),
        CheckConstraint(
            "offset_minutes IN (1440, 60)",
            name="ck_task_reminder_offset_minutes",
        ),
        CheckConstraint(
            "attempts >= 0",
            name="ck_task_reminder_attempts_non_negative",
        ),
        # Due-reminder sweeps: unsent reminders whose due time has arrived.
        Index(
            "ix_task_reminder_due_unsent",
            "scheduled_send_at",
            postgresql_where=sa_text("sent_at IS NULL"),
        ),
        Index(
            "ix_task_reminder_recipient_sent",
            "recipient_id",
            "sent_at",
        ),
        Index(
            "ix_task_reminder_post_offset",
            "help_post_id",
            "offset_minutes",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    help_post_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_help_post.id", ondelete="CASCADE"), index=True
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    # 1440 (24 hours before) or 60 (1 hour before).
    offset_minutes: Mapped[int] = mapped_column(default=REMINDER_OFFSET_24H)
    email: Mapped[str] = mapped_column(
        String(255), default="", server_default=sa_text("''")
    )
    # The task time this reminder refers to, and when it should go out.
    task_starts_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    scheduled_send_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    sent_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    attempts: Mapped[int] = mapped_column(
        default=0, server_default=sa_text("0")
    )
    last_attempt_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    provider_message_id: Mapped[str] = mapped_column(
        String(120), default="", server_default=sa_text("''")
    )
    last_error: Mapped[str] = mapped_column(
        String(255), default="", server_default=sa_text("''")
    )
    last_error_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )

    help_post: Mapped["HelpPost"] = relationship(default=None)
    recipient: Mapped["Subscriber"] = relationship(
        foreign_keys=[recipient_id], default=None
    )


class ContentReport(Base):
    """A report about unsafe content anywhere in the app.

    Deliberately separate from `SafetyReport` (which stays tied to completed
    tasks and is untouched). A polymorphic `target_type` / `target_id` pair
    covers profiles, community topics and comments, and both direct and
    non-contact messages; `reported_id` records the subscriber behind the
    content when it is known. One report per (reporter, target type, target id)
    prevents duplicates, and only the moderation columns change afterwards.
    """

    __tablename__ = "skillkind_content_report"
    __table_args__ = (
        UniqueConstraint(
            "reporter_id",
            "target_type",
            "target_id",
            name="uq_content_report_reporter_target",
        ),
        CheckConstraint(
            f"target_type IN ({_CONTENT_REPORT_TARGET_TYPES_SQL})",
            name="ck_content_report_target_type",
        ),
        CheckConstraint(
            "target_id > 0",
            name="ck_content_report_target_id_positive",
        ),
        CheckConstraint(
            "reported_id IS NULL OR reported_id <> reporter_id",
            name="ck_content_report_not_self",
        ),
        CheckConstraint(
            f"category IN ({_SAFETY_CATEGORIES_SQL})",
            name="ck_content_report_category",
        ),
        CheckConstraint(
            f"status IN ({_SAFETY_STATUSES_SQL})",
            name="ck_content_report_status",
        ),
        CheckConstraint(
            "reviewed_at IS NULL OR reviewed_at >= created_at",
            name="ck_content_report_review_after_creation",
        ),
        # Admin queue: open reports first, oldest first within a status.
        Index(
            "ix_content_report_status_created",
            "status",
            "created_at",
        ),
        # All reports about one piece of content.
        Index(
            "ix_content_report_target",
            "target_type",
            "target_id",
        ),
        # Risk profile for one subscriber.
        Index(
            "ix_content_report_reported_created",
            "reported_id",
            "created_at",
        ),
        Index(
            "ix_content_report_reported_status",
            "reported_id",
            "status",
        ),
        # "Have I already reported this?" lookup.
        Index(
            "ix_content_report_reporter_created",
            "reporter_id",
            "created_at",
        ),
        Index("ix_content_report_category", "category"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    reporter_id: Mapped[int] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="CASCADE"), index=True
    )
    # The subscriber behind the reported content, when it can be resolved.
    reported_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="SET NULL"),
        default=None,
        nullable=True,
        index=True,
    )
    target_type: Mapped[str] = mapped_column(
        String(32),
        default=REPORT_TARGET_PROFILE,
        server_default=sa_text("'profile'"),
        index=True,
    )
    # Primary key of the reported row in the table named by `target_type`. Kept
    # as a plain integer (no FK) so one table can cover every target type.
    target_id: Mapped[int] = mapped_column(default=0)
    # Short human-readable snapshot of what was reported, for moderation after
    # the original content may have been edited or deleted.
    target_excerpt: Mapped[str] = mapped_column(
        String(500), default="", server_default=sa_text("''")
    )
    category: Mapped[str] = mapped_column(
        String(32),
        default=SAFETY_CATEGORY_OTHER,
        server_default=sa_text("'other'"),
    )
    details: Mapped[str] = mapped_column(
        Text, default="", server_default=sa_text("''")
    )
    status: Mapped[str] = mapped_column(
        String(16),
        default=SAFETY_STATUS_OPEN,
        server_default=sa_text("'open'"),
        index=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=None
    )
    reviewed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    reviewed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("skillkind_subscriber.id", ondelete="SET NULL"),
        default=None,
        nullable=True,
        index=True,
    )
    admin_note: Mapped[str] = mapped_column(
        Text, default="", server_default=sa_text("''")
    )
    admin_note_updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    reporter: Mapped["Subscriber"] = relationship(
        back_populates="content_reports_filed",
        foreign_keys=[reporter_id],
        default=None,
    )
    reported: Mapped["Subscriber | None"] = relationship(
        back_populates="content_reports_received",
        foreign_keys=[reported_id],
        default=None,
    )
    reviewed_by: Mapped["Subscriber | None"] = relationship(
        foreign_keys=[reviewed_by_id], default=None
    )
