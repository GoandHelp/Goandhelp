from app.models import LANGUAGE_OPTIONS


REQUEST_COUNT_KEYS: tuple[str, ...] = (
    "{count} upcoming jobs",
    "{count} Confirmed job",
    "{count} Confirmed jobs",
    "{count} Confirmed helper",
    "{count} Confirmed helpers",
    "{count} Event",
    "{count} Events",
    "{count} Hosted event",
    "{count} Hosted events",
    "{count} Help request",
    "{count} Help requests",
    "{count} Search alerts",
    "{count} search alert",
    "{count} search alerts",
    "{count} Bookmarked help request",
    "{count} Bookmarked help requests",
    "{count} Offer to help you",
    "{count} Offers to help you",
    "{count} Request for your help",
    "{count} Requests for your help",
    "Get ready to help others",
    "People ready to help you",
    "Requests you have already posted",
    "Join many helping hands",
    "Manage helpers for your event",
    "Get notified with matching help requests",
    "Help requests you bookmarked in map or list view.",
    "{count} help given",
    "{count} help received",
    "Helped {count} time",
    "Helped {count} times",
    "Received help {count} time",
    "Received help {count} times",
    "{count} Requested",
    "{count} Open",
    "{count} Upcoming",
    "{count} people required",
    "{rating} out of 5 stars; {count} reviews",
    "Offered {date}",
)


REQUEST_COUNT_CATALOGS: dict[str, dict[str, str]] = {
    code: {source: source for source in REQUEST_COUNT_KEYS}
    for code, _label in LANGUAGE_OPTIONS
    if code != "en"
}
