"""Local job discovery: browse nearby open help posts, accept them, open a thread."""

import logging
import math
import re
from decimal import Decimal
from app.countries import supported_currency
from typing import TypedDict

import reflex as rx
from app.avatars import animal_avatar
from sqlalchemy import text

from app.components.openfreemap import MapMarker, ViewportPoint
from app.filter_categories import (
    FILTER_CATEGORIES,
    FilterCategory,
    category_label,
    expand_category_tokens,
)
from app.location_privacy import post_member_approximate, profile_approximate
from app.reward_display import reward_display
from app.member_blocks import (
    BLOCK_UNAVAILABLE_MESSAGE,
    are_members_blocked,
    not_blocked_author_sql,
)
from app.membership import ACTIVE_POST_CLAUSE
from app.models import (
    CATEGORY_LABELS,
    CATEGORY_OTHER,
    HELP_DURATION_LABELS,
    help_duration_label,
)
from app.skill_categories import (
    categories_overlap,
    category_color,
    category_icon_name,
    category_ink,
    category_labels,
    post_categories,
    primary_category,
    split_categories,
)
from app.states.auth_state import AuthState
from app.states.membership_state import MembershipState

# Modes that count as "this member opted in to appearing on the map". Legacy
# `live` rows are included so those helpers do not vanish, but every published
# point — for every mode — goes through the land-safe 0.5–1 km offset. No exact
# profile coordinate is ever serialized.
VISIBLE_LOCATION_SQL = "('approximate', 'live')"

LAST_ONLINE_INTERVALS: dict[str, str] = {
    "today": "1 day",
    "week": "7 days",
    "month": "30 days",
}

LANGUAGE_FILTER_CODES: list[str] = [
    "english",
    "spanish",
    "french",
    "portuguese",
    "german",
    "italian",
    "arabic",
    "hindi",
    "chinese",
    "japanese",
]

# Free, non-premium travel radius. The slider runs from 0 (Any distance) to
# 500 km in 5 km steps, and applies to both Give and Get mode.
DISTANCE_MIN_KM = 0
DISTANCE_MAX_KM = 500
DISTANCE_STEP_KM = 5
DEFAULT_DISTANCE_KM = 25

# Bounded dense-map path: one explicit safety cap for signed-in discovery
# result rows (help requests and willing helpers alike). Hundreds of matching
# pins can be represented at once while server memory, payload size and marker
# reconciliation work all stay bounded. Count queries are unaffected.
DISCOVERY_RESULT_CAP = 100


def clamp_distance_km(value: str | int | float) -> int:
    """Snap any value onto a 5 km step inside 0-500. 0 means Any distance."""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0
    if not math.isfinite(parsed) or parsed <= 0:
        return 0
    stepped = int(round(parsed / DISTANCE_STEP_KM)) * DISTANCE_STEP_KM
    return max(DISTANCE_MIN_KM, min(DISTANCE_MAX_KM, stepped))


# Give = choose a job and give help. Get = find a person to get help from.
MODE_GIVE = "give"
MODE_GET = "get"
VIEW_MAP = "map"
VIEW_LIST = "list"


def _avatar_image_url(avatar_path: str, avatar_seed: str) -> str:
    """Uploaded profile photo when stored, otherwise the deterministic avatar."""
    if avatar_path:
        return f"/_upload/{avatar_path}"
    return animal_avatar(avatar_seed)


REWARD_LABELS: dict[str, str] = {
    "lunch": "Lunch",
    "dinner": "Dinner",
    "accommodation": "Accommodation",
    "guided_tours": "Guided tours",
    "workshops": "Workshops",
    "lessons": "Lessons",
    "other": "Other",
}

DURATION_LABELS: dict[int, str] = HELP_DURATION_LABELS


class DirectRequest(TypedDict):
    """One of my own currently active help requests, for the direct ask."""

    id: int
    title: str
    categories: list[str]
    category_label: str


class FilterSummaryItem(TypedDict):
    source: str
    value: str
    localize_value: bool


class DiscoveryPost(TypedDict):
    id: int
    title: str
    description: str
    category: str
    category_label: str
    categories: list[str]
    category_chips: list[str]
    reward_type: str
    reward_label: str
    reward_details: str
    allow_price_quote: bool
    allow_duration_estimate: bool
    reward_currency: str
    location_name: str
    city: str
    country: str
    location: str
    scheduled: str
    scheduled_full: str
    duration_label: str
    urgency: str
    created: str
    poster_id: int
    poster_name: str
    poster_avatar_seed: str
    poster_verified: bool
    poster_headline: str
    poster_city: str
    poster_languages: str
    poster_skills: str
    poster_rating: float
    poster_reviews: int
    poster_image: str
    applicant_count: int
    photos: list[str]
    my_status: str
    lng: float
    lat: float
    has_map_point: bool


class ListPostGroup(TypedDict):
    poster_id: int
    poster_name: str
    count_label: str
    post: DiscoveryPost
    ids: list[int]
    posts: list[DiscoveryPost]


EMPTY_POST: DiscoveryPost = {
    "has_map_point": True,
    "id": 0,
    "title": "",
    "description": "",
    "category": "",
    "category_label": "",
    "categories": [],
    "category_chips": [],
    "reward_type": "",
    "reward_label": "",
    "reward_details": "",
    "allow_price_quote": False,
    "allow_duration_estimate": False,
    "reward_currency": "USD",
    "location_name": "",
    "city": "",
    "country": "",
    "location": "",
    "scheduled": "",
    "scheduled_full": "",
    "duration_label": "",
    "urgency": "",
    "created": "",
    "poster_id": 0,
    "poster_name": "",
    "poster_avatar_seed": "",
    "poster_verified": False,
    "poster_headline": "",
    "poster_city": "",
    "poster_languages": "",
    "poster_skills": "",
    "poster_rating": 0.0,
    "poster_reviews": 0,
    "poster_image": "",
    "applicant_count": 0,
    "photos": [],
    "my_status": "none",
    "lng": 0.0,
    "lat": 0.0,
}


class HelperProfile(TypedDict):
    id: int
    name: str
    avatar_seed: str
    username: str
    handle: str
    headline: str
    city: str
    languages: str
    skills: str
    categories: list[str]
    category_chips: list[str]
    skill_chips: list[str]
    primary_category: str
    availability: str
    avatar_path: str
    image_url: str
    help_mode: str
    mode_label: str
    rating: float
    reviews: int
    tasks_helped: int
    tasks_received: int
    kindness: int
    joined: str
    lng: float
    lat: float


EMPTY_HELPER: HelperProfile = {
    "id": 0,
    "name": "",
    "avatar_seed": "",
    "username": "",
    "handle": "",
    "headline": "",
    "city": "",
    "languages": "",
    "skills": "",
    "categories": [],
    "category_chips": [],
    "skill_chips": [],
    "primary_category": CATEGORY_OTHER,
    "availability": "",
    "avatar_path": "",
    "image_url": "",
    "help_mode": "",
    "mode_label": "",
    "rating": 0.0,
    "reviews": 0,
    "tasks_helped": 0,
    "tasks_received": 0,
    "kindness": 0,
    "joined": "",
    "lng": 0.0,
    "lat": 0.0,
}

EMPTY_CATEGORY_COUNTS: dict[str, int] = {
    "craftwork": 0,
    "labour": 0,
    "construction": 0,
    "workshop": 0,
    "teaching": 0,
    "healthcare": 0,
    "babysitter": 0,
    "carer": 0,
    "other": 0,
}


def inline_recipient_name(name: str) -> str:
    """Collapse only an exact repeated multi-word full name for display."""
    midpoint = len(name) // 2
    first = name[:midpoint]
    if (
        len(name) % 2 == 1
        and name[midpoint : midpoint + 1] == " "
        and first == name[midpoint + 1 :]
        and len(first.split()) >= 2
    ):
        return first
    return name


class DiscoveryState(rx.State):
    posts: list[DiscoveryPost] = []
    selected_post: DiscoveryPost = EMPTY_POST
    category_counts: dict[str, int] = EMPTY_CATEGORY_COUNTS
    open_total: int = 0

    map_mode: str = MODE_GIVE
    view_mode: str = VIEW_MAP
    map_center: list[float] = [10.0, 46.5]
    map_zoom: float = 3.6
    helpers: list[HelperProfile] = []
    selected_helper: HelperProfile = EMPTY_HELPER
    helper_total: int = 0
    visible_post_ids: list[int] = []
    visible_helper_ids: list[int] = []
    viewport_ready: bool = False
    _field_priority_post_ids: list[int] = []
    _field_priority_owner: str = ""
    map_pulse_post_ids: list[int] = []

    @rx.var
    def viewport_points(self) -> list[ViewportPoint]:
        return [
            {"id": f"p{post['id']}", "lat": post["lat"], "lng": post["lng"]}
            for post in self.posts
            if post.get("has_map_point", True)
        ] + [
            {
                "id": f"h{helper['id']}",
                "lat": helper["lat"],
                "lng": helper["lng"],
            }
            for helper in self.helpers
        ]

    @rx.var
    def visible_posts(self) -> list[DiscoveryPost]:
        if self._field_priority_post_ids and self.view_mode == VIEW_LIST:
            return sorted(
                [
                    post
                    for post in self.posts
                    if post["id"] in self._field_priority_post_ids
                    or post["id"] in self.visible_post_ids
                ],
                key=lambda post: (
                    post["id"] not in self._field_priority_post_ids
                ),
            )
        return (
            [post for post in self.posts if post["id"] in self.visible_post_ids]
            if self.viewport_ready
            else []
        )

    @rx.var
    def visible_helpers(self) -> list[HelperProfile]:
        return (
            [
                helper
                for helper in self.helpers
                if helper["id"] in self.visible_helper_ids
            ]
            if self.viewport_ready
            else []
        )

    @rx.event
    async def update_visible_points(self, ids: list[str]):
        from app.states.onboarding_state import OnboardingState
        from app.states.profile_state import ProfileState

        auth = await self.get_state(AuthState)
        onboarding = await self.get_state(OnboardingState)
        profile = await self.get_state(ProfileState)
        if (
            not auth.is_signed_in
            or onboarding.needs_onboarding
            or not profile.on_map
        ):
            return
        if not isinstance(ids, list):
            return
        post_ids = {post["id"] for post in self.posts}
        helper_ids = {helper["id"] for helper in self.helpers}
        self.visible_post_ids = sorted(
            {
                int(value[1:])
                for value in ids
                if isinstance(value, str)
                and re.fullmatch(r"p[1-9][0-9]*", value)
                and int(value[1:]) in post_ids
            }
        )
        self.visible_helper_ids = sorted(
            {
                int(value[1:])
                for value in ids
                if isinstance(value, str)
                and re.fullmatch(r"h[1-9][0-9]*", value)
                and int(value[1:]) in helper_ids
            }
        )
        self.viewport_ready = True

    category_filter: str = "all"
    reward_filter: str = "all"
    city_filter: str = ""

    # Free distance / travel-radius filter, applied in both modes. 0 = Any.
    distance_km: int = 0
    distance_min_km: int = DISTANCE_MIN_KM
    distance_max_km: int = DISTANCE_MAX_KM
    distance_step_km: int = DISTANCE_STEP_KM
    # Seeded once from the member's saved travel radius.
    distance_initialized: bool = True
    distance_warning: bool = False
    # Bumped whenever the radius is written by anything other than the slider,
    # so the uncontrolled range input re-mounts on its new default value.
    distance_reset_token: int = 0

    # Multi-select Help Filters category checklist (OR-combined in SQL).
    category_filters: list[str] = []
    category_list_open: bool = False
    filter_category_options: list[FilterCategory] = FILTER_CATEGORIES
    # Premium advanced search disclosure.
    advanced_expanded: bool = False

    # Give-mode marker grouping: several requests from one poster collapse into
    # a single profile-photo marker.
    group_poster_id: int = 0

    # Premium advanced filters (ignored unless the member is premium).
    last_online_filter: str = "any"
    rating_min: int = 0
    rating_max: int = 100
    nationality_filter: str = ""
    language_filters: list[str] = []

    last_online_options: list[dict[str, str]] = [
        {"value": "any", "label": "Any time"},
        {"value": "today", "label": "Online today"},
        {"value": "week", "label": "Online this week"},
        {"value": "month", "label": "Online this month"},
    ]

    language_options: list[str] = LANGUAGE_FILTER_CODES

    loading_count: int = 0

    @rx.var
    def is_loading(self) -> bool:
        return self.loading_count > 0

    filter_panel_open: bool = False
    error: str = ""
    success: str = ""

    thread_id: int = 0
    thread_with: str = ""
    thread_note: str = ""

    # ------------------------------------------------------------------
    # Two-step "Offer help" draft (nothing is written until Send)
    # ------------------------------------------------------------------
    offer_open: bool = False
    offer_draft: str = ""
    offer_price: str = ""
    offer_hours: str = "0"
    offer_minutes: str = "0"
    offer_period_count: str = "1"
    offer_period_unit: str = "days"
    map_pulse_post_id: int = 0
    map_pulse_token: int = 0

    @staticmethod
    def _quote_allowed(types: str, legacy: str, value, details: str) -> bool:
        rewards = [
            part.strip().lower() for part in (types or legacy).split(",")
        ]
        return (
            "money" in rewards
            and value == 0
            and "helper quote requested" in details.lower()
        )

    @staticmethod
    def _normalized_offer_price(price: str) -> str:
        normalized = price.strip()
        if not re.fullmatch(r"[0-9]{1,8}", normalized) or int(normalized) <= 0:
            raise ValueError("Give a positive whole-number price quote.")
        return normalized

    @staticmethod
    def _offer_quote_lines(
        post: DiscoveryPost,
        price: str,
        hours: str,
        minutes: str,
        period_count: str = "1",
        period_unit: str = "days",
    ) -> str:
        lines: list[str] = []
        if post.get("allow_price_quote", False):
            normalized = DiscoveryState._normalized_offer_price(price)
            lines.append(
                f"Price quote: {Decimal(normalized):f} {supported_currency(post.get('reward_currency', 'USD'))}"
            )
        if post.get("allow_duration_estimate", False):
            if not re.fullmatch(r"[0-9]{1,3}", hours or "") or not re.fullmatch(
                r"[0-9]{1,2}", minutes or ""
            ):
                raise ValueError("Enter whole numbers for hours and minutes.")
            h, m = int(hours), int(minutes)
            if h > 10 or m not in range(0, 60, 5):
                raise ValueError(
                    "Choose 0–10 hours and minutes in 5-minute steps."
                )
            if h * 60 + m <= 0:
                raise ValueError(
                    "Enter at least one minute for your duration estimate."
                )
            if not re.fullmatch(
                r"[1-9][0-9]{0,2}", period_count or ""
            ) or period_unit not in ("days", "weeks", "months"):
                raise ValueError(
                    "Choose 1–999 days, weeks or months for your estimate."
                )
            count = int(period_count)
            unit = period_unit[:-1] if count == 1 else period_unit
            lines.append(
                f"Duration estimate: {h} hours {m} minutes for {count} {unit}"
            )
        return "\n".join(lines)

    @rx.var
    def offer_validation(self) -> str:
        try:
            self._offer_quote_lines(
                self.selected_post,
                self.offer_price,
                self.offer_hours,
                self.offer_minutes,
                self.offer_period_count,
                self.offer_period_unit,
            )
        except ValueError as error:
            return str(error)
        return (
            ""
            if 5 <= len(self.offer_draft.strip()) <= 2000
            else "Write a message of 5–2000 characters."
        )

    @rx.var
    def offer_can_send(self) -> bool:
        return not self.is_sending_offer and not self.offer_validation

    @rx.event
    def set_offer_price(self, value: str):
        try:
            self.offer_price = DiscoveryState._normalized_offer_price(value)
        except ValueError:
            self.offer_price = value[:32]

    @rx.event
    def set_offer_price_number(self, value: float):
        self.offer_price = (
            str(int(value))
            if isinstance(value, (float, int))
            and math.isfinite(value)
            and float(value).is_integer()
            and value > 0
            else ""
        )

    @rx.event
    def set_offer_hours(self, value: str):
        self.offer_hours = value if value in {str(i) for i in range(11)} else ""

    @rx.event
    def set_offer_minutes(self, value: str):
        self.offer_minutes = (
            value if value in {str(i) for i in range(0, 60, 5)} else ""
        )

    @rx.event
    def set_offer_period_count(self, value: str):
        self.offer_period_count = value[:8]

    @rx.event
    def set_offer_period_unit(self, value: str):
        self.offer_period_unit = (
            value if value in ("days", "weeks", "months") else "days"
        )

    is_sending_offer: bool = False

    # ------------------------------------------------------------------
    # Direct help request from a helper's card (poster side)
    # ------------------------------------------------------------------
    direct_open: bool = False
    direct_requests: list[DirectRequest] = []
    direct_post_id: int = 0
    direct_draft: str = ""
    direct_warning: str = ""
    direct_notice: str = ""
    is_loading_direct: bool = False
    is_sending_direct: bool = False

    # Set by the top world search so the next board load opens that result.
    pending_post_id: int = 0
    pending_helper_id: int = 0

    category_options: list[dict[str, str]] = [
        {"value": "all", "label": "All categories"},
        {"value": "craftwork", "label": "Craftwork"},
        {"value": "labour", "label": "Labour"},
        {"value": "construction", "label": "Construction"},
        {"value": "workshop", "label": "Workshop"},
        {"value": "teaching", "label": "Teaching"},
        {"value": "healthcare", "label": "Healthcare"},
        {"value": "babysitter", "label": "Babysitter"},
        {"value": "carer", "label": "Carer"},
        {"value": "other", "label": "Other"},
    ]

    reward_filter_options: list[dict[str, str]] = [
        {"value": "all", "label": "Any reward"},
        {"value": "money", "label": "Money"},
        {"value": "lunch", "label": "Lunch"},
        {"value": "dinner", "label": "Dinner"},
        {"value": "accommodation", "label": "Accommodation"},
        {"value": "guided_tours", "label": "Guided tours"},
        {"value": "workshops", "label": "Workshops"},
        {"value": "lessons", "label": "Lessons"},
        {"value": "other", "label": "Other"},
    ]

    category_chips: list[dict[str, str]] = [
        {"value": "craftwork", "label": "Craftwork"},
        {"value": "labour", "label": "Labour"},
        {"value": "construction", "label": "Construction"},
        {"value": "workshop", "label": "Workshop"},
        {"value": "teaching", "label": "Teaching"},
        {"value": "healthcare", "label": "Healthcare"},
        {"value": "babysitter", "label": "Babysitter"},
        {"value": "carer", "label": "Carer"},
        {"value": "other", "label": "Other"},
    ]

    @rx.var
    def is_give_mode(self) -> bool:
        """Give: open jobs posted by people who need help."""
        return self.map_mode == MODE_GIVE

    @rx.var
    def is_list_view(self) -> bool:
        return self.view_mode == VIEW_LIST

    @rx.var
    def show_jobs(self) -> bool:
        has_task_category = any(
            value != "events" for value in self.category_filters
        )
        return self.map_mode == MODE_GIVE and (
            not self.category_filters or has_task_category
        )

    @rx.var
    def show_helpers(self) -> bool:
        has_task_category = any(
            value != "events" for value in self.category_filters
        )
        return self.map_mode == MODE_GET and (
            not self.category_filters or has_task_category
        )

    @rx.var
    def show_events(self) -> bool:
        return "events" in self.category_filters or (
            not self.category_filters and self.map_mode == MODE_GIVE
        )

    @rx.var
    def events_only(self) -> bool:
        return self.category_filters == ["events"]

    @rx.var
    def has_selection(self) -> bool:
        return self.selected_post["id"] > 0

    @rx.var
    def has_helper_selection(self) -> bool:
        return self.selected_helper["id"] > 0

    @rx.var
    def drawer_open(self) -> bool:
        return self.selected_post["id"] > 0 or self.selected_helper["id"] > 0

    @rx.event
    def show_post_on_map(self, post_id: int):
        """Use only the already published, land-safe point of a loaded request."""
        post = next(
            (item for item in self.posts if item["id"] == post_id), None
        )
        if (
            post is None
            or not post.get("has_map_point", True)
            or not math.isfinite(post["lat"])
            or not math.isfinite(post["lng"])
        ):
            return
        self.map_mode = MODE_GIVE
        self.view_mode = VIEW_MAP
        self.selected_helper = EMPTY_HELPER
        self.selected_post = EMPTY_POST
        self.group_poster_id = 0
        self.map_center = [post["lng"], post["lat"]]
        self.map_zoom = 12.0
        self.map_pulse_post_ids = []
        self.map_pulse_post_id = post_id
        self.map_pulse_token += 1
        self.filter_panel_open = False
        self.error = ""
        self.success = ""

    @rx.var
    def job_map_markers(self) -> list[MapMarker]:
        pulse_post_ids = getattr(self, "map_pulse_post_ids", [])
        if self.posts:
            counts: dict[int, int] = {}
            for post in self.posts:
                if not post.get("has_map_point", True):
                    continue
                counts[post["poster_id"]] = counts.get(post["poster_id"], 0) + 1
            markers: list[MapMarker] = []
            grouped: list[int] = []
            # A grouped pin uses an on-screen request's public point when available.
            ordered_posts = sorted(
                self.posts,
                key=lambda post: (
                    post["id"] != self.map_pulse_post_id
                    and post["id"] not in pulse_post_ids,
                    post["id"] not in self.visible_post_ids,
                ),
            )
            for post in ordered_posts:
                if not post.get("has_map_point", True):
                    continue
                category = primary_category(
                    post["categories"] or [post["category"]]
                )
                poster_id = post["poster_id"]
                if counts.get(poster_id, 0) > 1:
                    if poster_id in grouped:
                        continue
                    grouped.append(poster_id)
                    markers.append(
                        {
                            "id": f"g{poster_id}",
                            "lng": post["lng"],
                            "lat": post["lat"],
                            # Name kept for aria-label / title only.
                            "label": post["poster_name"],
                            "kind": "job",
                            "icon": category_icon_name(category),
                            "color": category_color(category),
                            "ink": category_ink(category),
                            "selected": poster_id == self.group_poster_id
                            or (
                                self.selected_post["id"] > 0
                                and poster_id == self.selected_post["poster_id"]
                            ),
                            "pulse_token": self.map_pulse_token
                            if any(
                                (
                                    item["id"] == self.map_pulse_post_id
                                    or item["id"] in pulse_post_ids
                                )
                                and item["poster_id"] == poster_id
                                for item in self.posts
                            )
                            else 0,
                        }
                    )
                    continue
                markers.append(
                    {
                        "id": f"p{post['id']}",
                        "lng": post["lng"],
                        "lat": post["lat"],
                        "label": post["title"],
                        "kind": "job",
                        "icon": category_icon_name(category),
                        "color": category_color(category),
                        "ink": category_ink(category),
                        "selected": post["id"] == self.selected_post["id"],
                        "pulse_token": self.map_pulse_token
                        if post["id"] == self.map_pulse_post_id
                        or post["id"] in pulse_post_ids
                        else 0,
                    }
                )
            return sorted(
                markers, key=lambda marker: bool(marker.get("pulse_token"))
            )
        return []

    @rx.var
    def helper_map_markers(self) -> list[MapMarker]:
        return [
            {
                "id": f"h{helper['id']}",
                "lng": helper["lng"],
                "lat": helper["lat"],
                "label": helper["name"],
                "kind": "helper",
                "icon": category_icon_name(helper["primary_category"]),
                "color": category_color(helper["primary_category"]),
                "image_url": helper["image_url"],
                "selected": helper["id"] == self.selected_helper["id"],
            }
            for helper in self.helpers
        ]

    # ------------------------------------------------------------------
    # Grouped poster marker → in-app list of that poster's requests
    @rx.var
    def map_markers(self) -> list[MapMarker]:
        return (
            self.job_map_markers
            if self.map_mode == MODE_GIVE
            else self.helper_map_markers
        )

    @rx.var
    def home_map_markers(self) -> list[MapMarker]:
        jobs, helpers = self.job_map_markers, self.helper_map_markers
        combined: list[MapMarker] = []
        seen: set[str] = set()
        for index in range(max(len(jobs), len(helpers))):
            for dataset in (jobs, helpers):
                if index < len(dataset) and dataset[index]["id"] not in seen:
                    combined.append(dataset[index])
                    seen.add(dataset[index]["id"])
                    if len(combined) == 100:
                        return combined
        return combined

    # ------------------------------------------------------------------
    # Grouped poster marker
    @rx.var
    def list_post_groups(self) -> list[ListPostGroup]:
        groups: dict[int, list[DiscoveryPost]] = {}
        for post in self.visible_posts:
            groups.setdefault(post["poster_id"], []).append(post)
        return [
            {
                "poster_id": poster_id,
                "poster_name": posts[0]["poster_name"],
                "count_label": f"{len(posts)} open request{'s' if len(posts) != 1 else ''}",
                "post": next(
                    (
                        post
                        for post in posts
                        if post["id"] == self.selected_post["id"]
                    ),
                    posts[0],
                ),
                "ids": [post["id"] for post in posts],
                "posts": posts,
            }
            for poster_id, posts in groups.items()
        ]

    @rx.var
    def selected_poster_requests(self) -> list[DiscoveryPost]:
        return [
            post
            for post in self.visible_posts
            if post["poster_id"] == self.selected_post["poster_id"]
        ]

    @rx.var
    def group_open(self) -> bool:
        return self.group_poster_id > 0

    @rx.var
    def group_posts(self) -> list[DiscoveryPost]:
        return [
            post
            for post in self.posts
            if post["poster_id"] == self.group_poster_id
            and post["id"] in self.visible_post_ids
        ]

    @rx.var
    def group_poster_post(self) -> DiscoveryPost:
        return self.group_posts[0] if self.group_posts else EMPTY_POST

    @rx.var
    def group_poster_name(self) -> str:
        for post in self.posts:
            if post["poster_id"] == self.group_poster_id:
                return post["poster_name"]
        return ""

    @rx.var
    def group_count_label(self) -> str:
        count = len(self.group_posts)
        if count == 1:
            return "1 open request"
        return f"{count} open requests"

    @rx.event
    def open_poster_group(self, poster_id: int):
        self.map_pulse_post_id = 0
        self.map_mode = MODE_GIVE
        self.selected_helper = EMPTY_HELPER
        self.group_poster_id = poster_id
        self.selected_post
        self.error = ""
        self.success = ""

    @rx.event
    def close_poster_group(self):
        self.group_poster_id = 0

    @rx.event
    def select_post_from_group(self, post_id: int):
        self.group_poster_id = 0
        return DiscoveryState.select_post(post_id)

    @rx.event
    def select_marker(self, marker_id: str):
        raw = str(marker_id)
        body = raw[1:]
        if raw.startswith("e") and body.isdigit():
            from app.states.event_state import EventState

            self.selected_post = EMPTY_POST
            self.selected_helper = EMPTY_HELPER
            self.group_poster_id = 0
            return EventState.select_event(int(body))
        if raw.startswith("g") and body.isdigit():
            return DiscoveryState.open_poster_group(int(body))
        if raw.startswith("p") and body.isdigit():
            return DiscoveryState.select_post(int(body))
        if raw.startswith("h") and body.isdigit():
            return DiscoveryState.select_helper(int(body))
        if not raw.isdigit():
            return None
        if self.map_mode == MODE_GIVE:
            return DiscoveryState.select_post(int(raw))
        return DiscoveryState.select_helper(int(raw))

    # ------------------------------------------------------------------
    # Map gestures close the transient overlays
    # ------------------------------------------------------------------

    @rx.event
    async def handle_map_interaction(self):
        """Dismiss map utilities and the helper passport, not job details."""
        from app.states.world_search_state import WorldSearchState
        from app.states.notification_state import NotificationState
        from app.states.profile_state import ProfileState

        self.filter_panel_open = False
        self.category_list_open = False
        self.selected_helper = dict(EMPTY_HELPER)
        self._reset_direct_composer()
        self.is_loading_direct = False
        search = await self.get_state(WorldSearchState)
        search.expanded = False
        notifications = await self.get_state(NotificationState)
        notifications.panel_open = False
        profile = await self.get_state(ProfileState)
        profile.settings_open = False

    @rx.var
    def filters_active(self) -> bool:
        return (
            len(self.category_filters) > 0
            or self.reward_filter != "all"
            or self.city_filter.strip() != ""
            or self.distance_active
            or self.advanced_active
        )

    @rx.var
    def distance_active(self) -> bool:
        """A finite radius applies to help requests and to helpers alike."""
        return self.distance_km > 0

    @rx.var
    def distance_fill(self) -> str:
        return f"{max(0, min(500, self.distance_km)) / 5:.1f}%"

    @rx.var
    def distance_label(self) -> str:
        """Compact value shown beside the slider's own label."""
        if self.distance_km <= 0:
            return "Any"
        if self.distance_km >= DISTANCE_MAX_KM:
            return f"{DISTANCE_MAX_KM}+ km"
        return f"{self.distance_km} km"

    async def _accept_distance(self, value: float) -> bool:
        from app.states.profile_state import ProfileState

        distance = clamp_distance_km(value)
        profile = await self.get_state(ProfileState)
        auth = await self.get_state(AuthState)
        valid = False
        if (
            profile.location_mode == "approximate"
            and auth.subscriber_id.isdigit()
        ):
            lat, lng, _ = await self._viewer_point(int(auth.subscriber_id))
            valid = lat is not None and lng is not None
        self.distance_initialized = True
        if distance > 0 and not valid:
            self.distance_km = 0
            self.distance_reset_token += 1
            self.distance_warning = True
            return False
        self.distance_km = distance
        self.distance_warning = False
        self.error = ""
        self.success = ""
        return True

    @rx.event
    async def set_distance_filter(self, value: float):
        await self._accept_distance(value)
        return DiscoveryState.refresh_board

    @rx.event
    async def commit_distance_filter(self, value: float):
        previous = self.distance_km
        accepted = await self._accept_distance(value)
        if not accepted or previous != self.distance_km:
            return DiscoveryState.refresh_board

    @rx.var
    def category_summary_label(self) -> str:
        if not self.category_filters:
            return "All categories"
        if len(self.category_filters) == 1:
            return category_label(self.category_filters[0])
        return f"{len(self.category_filters)} categories selected"

    @rx.var
    def advanced_active(self) -> bool:
        return (
            self.last_online_filter != "any"
            or self.rating_min > 0
            or self.rating_max < 100
            or self.nationality_filter.strip() != ""
            or len(self.language_filters) > 0
        )

    @rx.var
    def rating_range_label(self) -> str:
        return f"Rating {self.rating_min}–{self.rating_max}%"

    @rx.var
    def active_filter_summary(self) -> list[str]:
        """Human-readable chips describing every filter in force."""
        summary: list[str] = []
        for value in self.category_filters:
            summary.append(f"Category: {category_label(value)}")
        if self.reward_filter != "all":
            summary.append(
                f"Reward: {REWARD_LABELS.get(self.reward_filter, 'Money' if self.reward_filter == 'money' else self.reward_filter)}"
            )
        if self.city_filter.strip():
            summary.append(f"Place: {self.city_filter.strip()}")
        if self.last_online_filter != "any":
            labels = {
                "today": "Online today",
                "week": "Online this week",
                "month": "Online this month",
            }
            summary.append(labels.get(self.last_online_filter, "Last online"))
        if self.rating_min > 0 or self.rating_max < 100:
            summary.append(f"Rating {self.rating_min}–{self.rating_max}%")
        if self.nationality_filter.strip():
            summary.append(f"Nationality: {self.nationality_filter.strip()}")
        for language in self.language_filters:
            summary.append(f"Speaks {language.title()}")
        return summary

    @rx.var
    def active_filter_summary_items(self) -> list[FilterSummaryItem]:
        """Display-only localized templates with untouched member-entered values."""
        summary: list[FilterSummaryItem] = []
        for value in self.category_filters:
            summary.append(
                {
                    "source": "Category: {value}",
                    "value": category_label(value),
                    "localize_value": True,
                }
            )
        if self.reward_filter != "all":
            summary.append(
                {
                    "source": "Reward: {value}",
                    "value": REWARD_LABELS.get(
                        self.reward_filter,
                        "Money"
                        if self.reward_filter == "money"
                        else self.reward_filter,
                    ),
                    "localize_value": True,
                }
            )
        if self.city_filter.strip():
            summary.append(
                {
                    "source": "Place: {value}",
                    "value": self.city_filter,
                    "localize_value": False,
                }
            )
        if self.last_online_filter != "any":
            labels = {
                "today": "Online today",
                "week": "Online this week",
                "month": "Online this month",
            }
            summary.append(
                {
                    "source": labels.get(
                        self.last_online_filter, "Last online"
                    ),
                    "value": "",
                    "localize_value": False,
                }
            )
        if self.rating_min > 0 or self.rating_max < 100:
            summary.append(
                {
                    "source": "Rating {value}%",
                    "value": f"{self.rating_min}–{self.rating_max}",
                    "localize_value": False,
                }
            )
        if self.nationality_filter.strip():
            summary.append(
                {
                    "source": "Nationality: {value}",
                    "value": self.nationality_filter,
                    "localize_value": False,
                }
            )
        for language in self.language_filters:
            summary.append(
                {
                    "source": "Speaks {value}",
                    "value": language.title(),
                    "localize_value": True,
                }
            )
        return summary

    def _advanced_clause(
        self,
        premium: bool,
        profile_alias: str,
        person_alias: str,
        rating_column: str,
    ) -> tuple[str, dict[str, str | int]]:
        """Parameterised SQL for the premium filters, or nothing when free."""
        clause = ""
        params: dict[str, str | int] = {}
        if not premium:
            return clause, params
        interval = LAST_ONLINE_INTERVALS.get(self.last_online_filter, "")
        if interval:
            clause += (
                f" AND {person_alias}.last_seen_at IS NOT NULL"
                f" AND {person_alias}.last_seen_at >= now() - INTERVAL '{interval}'"
            )
        if self.rating_min > 0 or self.rating_max < 100:
            clause += (
                f" AND (COALESCE({profile_alias}.{rating_column}, 0) * 20)"
                " BETWEEN :rating_min AND :rating_max"
            )
            params["rating_min"] = int(self.rating_min)
            params["rating_max"] = int(self.rating_max)
        nationality = self.nationality_filter.strip().lower()
        if nationality:
            clause += (
                f" AND LOWER(COALESCE({profile_alias}.nationality, ''))"
                " LIKE :nationality"
            )
            params["nationality"] = f"%{nationality}%"
        languages = [
            lang.strip().lower()
            for lang in self.language_filters
            if lang.strip()
        ]
        if languages:
            pieces: list[str] = []
            for index, language in enumerate(languages):
                key = f"language_{index}"
                pieces.append(
                    f"LOWER(COALESCE({profile_alias}.languages, '')) LIKE :{key}"
                )
                params[key] = f"%{language}%"
            clause += " AND (" + " OR ".join(pieces) + ")"
        return clause, params

    async def _viewer_point(
        self, sid: int
    ) -> tuple[float | None, float | None, int]:
        """The viewer's PRIVATE stored point + saved radius, server-side only.

        The coordinates are only ever used as bound SQL parameters; they are
        never written into state and never serialized to the browser.
        """
        member_lat: float | None = None
        member_lng: float | None = None
        saved_radius = 0
        try:
            async with rx.asession() as asession:
                own = (
                    await asession.execute(
                        text(
                            """
                            SELECT latitude, longitude,
                                   COALESCE(travel_radius_km, 0)
                            FROM skillkind_profile
                            WHERE subscriber_id = :sid
                            """
                        ),
                        {"sid": int(sid)},
                    )
                ).first()
            if own is not None:
                if own[0] is not None and own[1] is not None:
                    lat_value = float(own[0])
                    lng_value = float(own[1])
                    if -90.0 <= lat_value <= 90.0 and (
                        -180.0 <= lng_value <= 180.0
                    ):
                        member_lat, member_lng = lat_value, lng_value
                saved_radius = int(own[2] or 0)
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Could not read your saved location: {e}")
        return member_lat, member_lng, saved_radius

    async def _premium_now(self) -> bool:
        membership = await self.get_state(MembershipState)
        return membership.is_premium

    async def _require_premium(self) -> bool:
        """Premium gate. The paywall opens with no upgrade-reason box."""
        membership = await self.get_state(MembershipState)
        if membership.is_premium:
            return True
        membership.paywall_open = True
        membership.upgrade_reason = ""
        membership.error = ""
        return False

    @rx.event
    def toggle_advanced_expanded(self):
        self.advanced_expanded = not self.advanced_expanded

    @rx.event
    def toggle_category_list(self):
        self.category_list_open = not self.category_list_open

    @rx.event
    async def toggle_category_choice(self, value: str):
        newly_selected = value not in self.category_filters
        if newly_selected:
            self.category_filters = [*self.category_filters, value]
        else:
            self.category_filters = [
                item for item in self.category_filters if item != value
            ]
        self.error = ""
        self.success = ""
        sid = (await self.get_state(AuthState)).subscriber_id
        # Only a real, newly chosen category from a signed-in member is logged.
        if newly_selected and value and value != "all" and sid.isdigit():
            try:
                async with rx.asession() as asession:
                    await asession.execute(
                        text(
                            """
                            INSERT INTO skillkind_category_search_event
                                (category, subscriber_id, latitude, longitude,
                                 created_at)
                            SELECT :category, :sid, pr.latitude, pr.longitude,
                                   now()
                            FROM (SELECT 1) AS anchor
                            LEFT JOIN skillkind_profile pr
                                   ON pr.subscriber_id = :sid
                            """
                        ),
                        {"category": value[:48], "sid": int(sid)},
                    )
                    await asession.commit()
            except Exception as e:  # noqa: BLE001
                logging.exception(f"Could not record a category search: {e}")
        return DiscoveryState.refresh_board

    @rx.event
    def clear_category_choices(self):
        self.category_filters = []
        return DiscoveryState.refresh_board

    @rx.event
    async def set_last_online(self, value: str):
        if not await self._require_premium():
            return None
        self.last_online_filter = (
            value if value in ("any", "today", "week", "month") else "any"
        )
        return DiscoveryState.refresh_board

    @rx.event
    async def set_rating_min(self, value: float):
        if not await self._require_premium():
            return None
        try:
            parsed = int(round(float(value)))
        except (TypeError, ValueError):
            parsed = 0
        self.rating_min = max(0, min(parsed, self.rating_max))
        return DiscoveryState.refresh_board

    @rx.event
    async def set_rating_max(self, value: float):
        if not await self._require_premium():
            return None
        try:
            parsed = int(round(float(value)))
        except (TypeError, ValueError):
            parsed = 100
        self.rating_max = min(100, max(parsed, self.rating_min))
        return DiscoveryState.refresh_board

    @rx.event
    async def set_nationality_filter(self, value: str):
        if not await self._require_premium():
            return None
        self.nationality_filter = value[:120]
        return DiscoveryState.refresh_board

    @rx.event
    async def toggle_language_filter(self, value: str):
        if not await self._require_premium():
            return None
        if value in self.language_filters:
            self.language_filters = [
                lang for lang in self.language_filters if lang != value
            ]
        else:
            self.language_filters = [*self.language_filters, value]
        return DiscoveryState.refresh_board

    @rx.event
    async def open_advanced_paywall(self):
        await self._require_premium()

    def _row_to_post(
        self, row, photos: list[str], allow_unmapped: bool = False
    ) -> DiscoveryPost | None:
        post_id = int(row[0])
        poster_avatar_seed_value = str(row[16] or "")
        poster_avatar = str(row[30] or "")
        categories = post_categories(
            str(row[32] or "") if len(row) > 32 else "", str(row[3] or "")
        )
        category = primary_category(categories)
        reward = str(row[4] or "")
        reward_types = str(row[34] or "") if len(row) > 34 else reward
        amount = Decimal(str(row[35] or 0)) if len(row) > 35 else Decimal(0)
        currency = (
            supported_currency(str(row[36] or "")) if len(row) > 36 else "USD"
        )
        quote_requested = self._quote_allowed(
            reward_types, reward, amount, str(row[5] or "")
        )
        reward_label = reward_display(
            reward, reward_types, amount, currency, str(row[5] or "")
        )
        place = str(row[6] or "")
        city = str(row[7] or "")
        country = str(row[8] or "")
        duration = int(row[10]) if row[10] is not None else 60
        # Every request is public only as an approximate area: the typed
        # street address is never serialized, whatever the stored mode says
        # (including legacy `place` rows).
        where = (
            ", ".join([p for p in [city, country] if p]) or "Approximate area"
        )
        public_place = ""
        post_lng = None if row[26] is None else float(row[26])
        post_lat = None if row[25] is None else float(row[25])
        poster_mode = str(row[29] or "hidden")
        poster_lat = None if row[27] is None else float(row[27])
        poster_lng = None if row[28] is None else float(row[28])
        # Never exact: every request point is offset 0.5–1 km onto land before
        # it is serialized, and every profile fallback point 0.5–1 km.
        lat: float | None = None
        lng: float | None = None
        if post_lat is not None and post_lng is not None:
            offset = post_member_approximate(post_id, post_lat, post_lng)
            if offset is not None:
                lat, lng = offset
        elif poster_lat is not None and poster_lng is not None:
            # Legacy `live` counts as an opted-in approximate source only.
            if poster_mode in ("approximate", "live", "fixed"):
                offset = profile_approximate(
                    int(row[14]), poster_lat, poster_lng
                )
                if offset is not None:
                    lat, lng = offset
        has_map_point = lat is not None and lng is not None
        if not has_map_point and not allow_unmapped:
            return None
        return {
            "has_map_point": has_map_point,
            "id": post_id,
            "title": str(row[1]),
            "description": str(row[2] or ""),
            "category": category,
            "category_label": CATEGORY_LABELS.get(
                category, category.replace("_", " ").title()
            ),
            "categories": categories,
            "category_chips": category_labels(categories),
            "reward_type": reward,
            "reward_label": reward_label,
            "reward_details": str(row[5] or ""),
            "allow_price_quote": quote_requested,
            "allow_duration_estimate": duration == 0,
            "reward_currency": currency,
            "location_name": public_place,
            "city": city,
            "country": country,
            "location": where,
            "scheduled": row[9].strftime("%b %d · %H:%M")
            if row[9] is not None
            else "Time to agree",
            "scheduled_full": row[9].strftime("%A, %b %d %Y at %H:%M")
            if row[9] is not None
            else "Time still to agree",
            "duration_label": help_duration_label(duration),
            "urgency": str(row[11] or "flexible"),
            "created": row[13].strftime("%b %d, %Y")
            if row[13] is not None
            else "",
            "poster_id": int(row[14]),
            "poster_name": str(row[15] or "A neighbour"),
            "poster_avatar_seed": poster_avatar_seed_value,
            "poster_verified": bool(row[33]) if len(row) > 33 else False,
            "poster_headline": str(row[17] or ""),
            "poster_city": str(row[18] or ""),
            "poster_languages": str(row[19] or ""),
            "poster_skills": str(row[20] or ""),
            "poster_rating": float(row[21] or 0),
            "poster_reviews": int(row[22] or 0),
            "poster_image": _avatar_image_url(
                poster_avatar, poster_avatar_seed_value
            ),
            "applicant_count": int(row[23] or 0),
            "photos": photos,
            "my_status": str(row[24] or "none"),
            "lng": lng if lng is not None else 0.0,
            "lat": lat if lat is not None else 0.0,
        }

    @rx.event
    def set_map_mode(self, value: str):
        self.map_mode = value if value in (MODE_GIVE, MODE_GET) else MODE_GIVE
        self.error = ""
        self.success = ""
        self.selected_post = EMPTY_POST
        self.selected_helper = EMPTY_HELPER
        self._reset_offer_draft()
        self._reset_direct_composer()
        self.group_poster_id = 0
        self.thread_id = 0
        self.thread_with = ""
        self.thread_note = ""
        return DiscoveryState.refresh_board

    @rx.event
    def set_view_mode(self, value: str):
        next_mode = value if value in (VIEW_MAP, VIEW_LIST) else VIEW_MAP
        self.map_pulse_post_id = 0
        self.view_mode = next_mode
        return DiscoveryState.refresh_board

    @rx.event
    def focus_post(self, post_id: int):
        """Open a searched job: Give mode, map view, unfiltered board."""
        self.map_mode = MODE_GIVE
        self.view_mode = VIEW_MAP
        self.category_filters = []
        self.reward_filter = "all"
        self.city_filter = ""
        self.selected_helper = EMPTY_HELPER
        self.group_poster_id = 0
        self.pending_post_id = post_id
        self.error = ""
        self.success = ""
        return DiscoveryState.load_jobs

    @rx.event
    def focus_helper(self, helper_id: int):
        """Open a searched person: Get mode, map view, unfiltered board."""
        self.map_mode = MODE_GET
        self.view_mode = VIEW_MAP
        self.category_filters = []
        self.city_filter = ""
        self.selected_post = EMPTY_POST
        self.group_poster_id = 0
        self.pending_helper_id = helper_id
        self.error = ""
        self.success = ""
        return DiscoveryState.load_helpers

    @rx.event
    def focus_place(self, place: str):
        """Filter the map around a searched city or country."""
        self.view_mode = VIEW_MAP
        self.city_filter = place
        self.selected_post = EMPTY_POST
        self.selected_helper = EMPTY_HELPER
        self.error = ""
        self.success = ""
        return DiscoveryState.refresh_board

    @rx.event
    def refresh_board(self):
        from app.states.event_state import EventState

        yield EventState.load_events
        yield DiscoveryState.load_jobs
        yield DiscoveryState.load_helpers

    @rx.event
    def select_helper(self, helper_id: int):
        return DiscoveryState.open_member_profile(helper_id)

    @rx.event
    async def open_member_profile(self, member_id: int):
        auth = await self.get_state(AuthState)
        self.selected_helper = dict(EMPTY_HELPER)
        if (
            not auth.is_signed_in
            or not auth.subscriber_id.isdigit()
            or member_id <= 0
        ):
            return
        try:
            async with rx.asession() as session:
                row = (
                    (
                        await session.execute(
                            text(f"""
                    SELECT s.id, s.display_name, s.help_mode, s.joined_at,
                           COALESCE(pr.username, '') AS username,
                           COALESCE(pr.headline, '') AS headline,
                           COALESCE(pr.current_city, '') AS city,
                           COALESCE(pr.languages, '') AS languages,
                           COALESCE(pr.skills, '') AS skills,
                           COALESCE(pr.preferred_categories, '') AS categories,
                           COALESCE(pr.availability_note, '') AS availability,
                           COALESCE(pr.avatar_path, '') AS avatar_path,
                           COALESCE(pr.helper_rating_avg, 0) AS rating,
                           COALESCE(pr.helper_rating_count, 0) AS reviews,
                           COALESCE(pr.tasks_helped_count, 0) AS tasks_helped,
                           COALESCE(pr.tasks_received_count, 0) AS tasks_received
                    FROM skillkind_subscriber s
                    LEFT JOIN skillkind_profile pr ON pr.subscriber_id = s.id
                    WHERE s.id = :member_id AND s.is_active = TRUE
                      AND {not_blocked_author_sql("s.id")}
                    LIMIT 1
                """),
                            {
                                "member_id": member_id,
                                "sid": int(auth.subscriber_id),
                            },
                        )
                    )
                    .mappings()
                    .first()
                )
            if row is None:
                return rx.toast("This member profile is unavailable.")
            categories = split_categories(str(row["categories"]))
            seed = f"member-{member_id}"
            helper: HelperProfile = dict(EMPTY_HELPER)
            helper.update(
                {
                    "id": member_id,
                    "name": str(row["display_name"] or "Member"),
                    "avatar_seed": seed,
                    "username": str(row["username"]),
                    "handle": f"@{row['username']}" if row["username"] else "",
                    "headline": str(row["headline"]),
                    "city": str(row["city"]),
                    "languages": str(row["languages"]),
                    "skills": str(row["skills"]),
                    "categories": categories,
                    "category_chips": category_labels(categories),
                    "skill_chips": [
                        s.strip()
                        for s in str(row["skills"]).split(",")
                        if s.strip()
                    ][:12],
                    "primary_category": primary_category(categories),
                    "availability": str(row["availability"]),
                    "avatar_path": str(row["avatar_path"]),
                    "image_url": _avatar_image_url(
                        str(row["avatar_path"]), seed
                    ),
                    "help_mode": str(row["help_mode"] or ""),
                    "rating": float(row["rating"]),
                    "reviews": int(row["reviews"]),
                    "tasks_helped": int(row["tasks_helped"]),
                    "tasks_received": int(row["tasks_received"]),
                    "joined": row["joined_at"].strftime("%b %d, %Y")
                    if row["joined_at"]
                    else "",
                }
            )
            from app.states.event_state import EventState

            events = await self.get_state(EventState)
            events.selected_event = []
            self.selected_post = dict(EMPTY_POST)
            self.selected_helper = helper
            self.group_poster_id = 0
            self.filter_panel_open = False
            self._reset_direct_composer()
            self._reset_offer_draft()
            self.error = ""
            self.success = ""
        except Exception as e:
            logging.exception(f"Error: {e}")
            return rx.toast(
                "We couldn't open this member profile. Please try again."
            )

    # ------------------------------------------------------------------
    # "Offer help": an editable draft, sent only when the member confirms
    # ------------------------------------------------------------------

    def _reset_offer_draft(self):
        self.offer_open = False
        self.offer_draft = ""
        self.offer_price = ""
        self.offer_hours = "0"
        self.offer_minutes = "0"
        self.offer_period_count = "1"
        self.offer_period_unit = "days"
        self.is_sending_offer = False

    def _reset_direct_composer(self):
        self.direct_open = False
        self.direct_requests = []
        self.direct_post_id = 0
        self.direct_draft = ""
        self.direct_warning = ""
        self.direct_notice = ""
        self.is_sending_direct = False

    @rx.event
    async def open_offer_draft(self):
        """Compose the offer message. Nothing is written to the database yet."""
        post = self.selected_post
        if post["id"] <= 0:
            return
        auth = await self.get_state(AuthState)
        self.error = ""
        self.success = ""
        self._reset_offer_draft()
        self.offer_open = True
        self.offer_draft = (
            f"Dear {post['poster_name']}, I am offering my help to your "
            f"request {post['title']}. Yours, {auth.display_name}."
        )

    @rx.event
    def set_offer_draft(self, value: str):
        self.offer_draft = value[:2000]

    @rx.event
    def cancel_offer_draft(self):
        self._reset_offer_draft()

    @rx.event(background=True)
    async def send_offer(self):
        try:
            async for event in self._send_offer():
                yield event
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = "We couldn't send your offer. Your draft is still here; please try again."
        finally:
            async with self:
                self.is_sending_offer = False

    async def _send_offer(self):
        """Persist the drafted message as the application pitch + first message."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            post = self.selected_post
            if self.is_sending_offer:
                return
            body = self.offer_draft.strip()
            draft_body = body
            price, hours, minutes, period_count, period_unit = (
                self.offer_price,
                self.offer_hours,
                self.offer_minutes,
                self.offer_period_count,
                self.offer_period_unit,
            )
        problem = ""
        if not sid.isdigit():
            problem = "Your session expired — please sign in again."
        elif post["id"] <= 0:
            problem = "Pick a job on the board first."
        elif len(body) < 5:
            problem = "Write a short message before you send it."
        elif len(body) > 2000:
            problem = "Keep your message under 2000 characters."
        quote_lines = ""
        try:
            quote_lines = self._offer_quote_lines(
                post, price, hours, minutes, period_count, period_unit
            )
        except ValueError as error:
            problem = str(error)
        if problem:
            async with self:
                self.error = problem
                self.success = ""
            return
        excerpt = (
            f"{body[: max(0, 253 - len(quote_lines))]}\n\n{quote_lines}"
            if quote_lines
            else body[:255]
        )
        body = f"{body}\n\n{quote_lines}" if quote_lines else body
        async with self:
            self.is_sending_offer = True
            self.error = ""
            self.success = ""

        post_id = int(post["id"])
        poster_id = int(post["poster_id"])
        title = post["title"]

        async with rx.asession() as asession:
            still_open = (
                await asession.execute(
                    text(
                        """
                        SELECT status, author_id, title, GREATEST(COALESCE(helpers_needed, 1), 1),
                               COALESCE(reward_types, ''), reward_type,
                               COALESCE(reward_value, 0), COALESCE(reward_details, ''),
                               COALESCE(duration_minutes, 60), COALESCE(reward_currency, 'USD')
                        FROM skillkind_help_post
                        WHERE id = :post_id
                          AND (expires_at IS NULL OR expires_at > now())
                          AND NOT EXISTS (SELECT 1 FROM skillkind_completed_task ct WHERE ct.post_id = :post_id)
                        FOR UPDATE
                        """
                    ),
                    {"post_id": post_id},
                )
            ).first()
            if still_open is None or str(still_open[0]) != "open":
                async with self:
                    self.is_sending_offer = False
                    self.error = "That job was just taken — try another one on the board."
                yield DiscoveryState.load_jobs
                return
            authoritative_post = dict(post)
            authoritative_post["allow_price_quote"] = self._quote_allowed(
                str(still_open[4]),
                str(still_open[5]),
                still_open[6],
                str(still_open[7]),
            )
            authoritative_post["allow_duration_estimate"] = (
                int(still_open[8]) == 0
            )
            authoritative_post["reward_currency"] = supported_currency(
                str(still_open[9])
            )
            try:
                quote_lines = self._offer_quote_lines(
                    authoritative_post,
                    price,
                    hours,
                    minutes,
                    period_count,
                    period_unit,
                )
            except ValueError as e:
                await asession.rollback()
                async with self:
                    self.error = str(e)
                    self.success = ""
                    self.is_sending_offer = False
                    if self.selected_post["id"] == post_id:
                        self.selected_post = authoritative_post
                return
            body = (
                f"{draft_body}\n\n{quote_lines}" if quote_lines else draft_body
            )
            excerpt = body[:255]
            poster_id = int(still_open[1])
            title = str(still_open[2])
            accepted_count = (
                await asession.execute(
                    text("""
                SELECT COUNT(*) FROM skillkind_job_application
                WHERE post_id = :pid AND status = 'accepted'
            """),
                    {"pid": post_id},
                )
            ).scalar_one()
            if poster_id == int(sid) or int(accepted_count or 0) >= int(
                still_open[3]
            ):
                await asession.rollback()
                async with self:
                    self.is_sending_offer = False
                    self.error = "This request has no available helper places, or is your own request."
                yield DiscoveryState.load_jobs
                return
            # Symmetric block check inside the same session, immediately
            # before any write to the job/thread/message tables.
            if await are_members_blocked(asession, int(sid), poster_id):
                await asession.rollback()
                async with self:
                    self.is_sending_offer = False
                    self.offer_open = False
                    self.error = BLOCK_UNAVAILABLE_MESSAGE
                yield DiscoveryState.load_jobs
                return
            existing = (
                await asession.execute(
                    text(
                        """
                        SELECT id, status FROM skillkind_job_application
                        WHERE post_id = :post_id AND helper_id = :sid
                        """
                    ),
                    {"post_id": post_id, "sid": int(sid)},
                )
            ).first()
            if existing is not None and str(existing[1]) == "accepted":
                await asession.rollback()
                async with self:
                    self.is_sending_offer = False
                    self.error = "You are already confirmed for this request. Use Inbox to discuss details."
                return
            if existing is None:
                await asession.execute(
                    text(
                        """
                        INSERT INTO skillkind_job_application
                            (post_id, helper_id, pitch, status, responded_at)
                        VALUES
                            (:post_id, :sid, :pitch, 'pending', NULL)
                        """
                    ),
                    {"post_id": post_id, "sid": int(sid), "pitch": body},
                )
            else:
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_job_application
                        SET status = 'pending', pitch = :pitch,
                            responded_at = NULL
                        WHERE id = :app_id
                        """
                    ),
                    {"pitch": body, "app_id": int(existing[0])},
                )
            await asession.execute(
                text("""
                INSERT INTO skillkind_member_notification
                    (recipient_id, kind, title, body, actor_id, help_post_id, target_route)
                VALUES (:poster, 'help_offer', :title, :body, :sid, :pid, 'help')
            """),
                {
                    "poster": poster_id,
                    "title": "New offer of help",
                    "body": excerpt,
                    "sid": int(sid),
                    "pid": post_id,
                },
            )
            thread_id = await self._thread_for(
                asession, post_id, poster_id, int(sid), title
            )
            await asession.execute(
                text(
                    """
                    INSERT INTO skillkind_message (thread_id, sender_id, body)
                    VALUES (:thread_id, :sid, :body)
                    """
                ),
                {"thread_id": thread_id, "sid": int(sid), "body": body},
            )
            await asession.commit()

        async with self:
            self.is_sending_offer = False
            self._reset_offer_draft()
            self.thread_id = thread_id
            self.thread_with = inline_recipient_name(post["poster_name"])
            self.thread_note = body
            self.success = f"Your offer is on its way to {post['poster_name']}."
        yield rx.toast(
            f"Offer sent to {post['poster_name']}.",
            duration=4000,
        )
        yield DiscoveryState.load_jobs

    async def _thread_for(
        self,
        asession,
        post_id: int,
        poster_id: int,
        helper_id: int,
        subject: str,
    ) -> int:
        """Reuse the (post, helper) thread when it exists, else create it."""
        row = (
            await asession.execute(
                text(
                    """
                    SELECT id FROM skillkind_message_thread
                    WHERE post_id = :post_id AND helper_id = :helper_id
                    """
                ),
                {"post_id": post_id, "helper_id": helper_id},
            )
        ).first()
        if row is not None:
            thread_id = int(row[0])
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_message_thread
                    SET last_message_at = now(), is_archived = FALSE
                    WHERE id = :thread_id
                    """
                ),
                {"thread_id": thread_id},
            )
            return thread_id
        created = (
            await asession.execute(
                text(
                    """
                    INSERT INTO skillkind_message_thread
                        (post_id, poster_id, helper_id, subject,
                         is_archived, last_message_at)
                    VALUES
                        (:post_id, :poster_id, :helper_id, :subject,
                         FALSE, now())
                    RETURNING id
                    """
                ),
                {
                    "post_id": post_id,
                    "poster_id": poster_id,
                    "helper_id": helper_id,
                    "subject": subject[:200],
                },
            )
        ).first()
        return int(created[0])

    # ------------------------------------------------------------------
    # "Request help directly": only for a helpee with a live open request
    # ------------------------------------------------------------------

    @rx.var
    def has_direct_requests(self) -> bool:
        return len(self.direct_requests) > 0

    @rx.var
    def direct_can_send(self) -> bool:
        return self.direct_post_id > 0 and len(self.direct_draft.strip()) >= 5

    @rx.event
    def close_direct_help(self):
        self._reset_direct_composer()

    @rx.event
    async def go_to_ask_for_help(self):
        from app.states.profile_state import ProfileState
        from app.states.help_hub_state import HelpHubState

        self._reset_direct_composer()
        self.is_loading_direct = False
        self.selected_helper = dict(EMPTY_HELPER)
        profile = await self.get_state(ProfileState)
        profile.active_tab = "help"
        hub = await self.get_state(HelpHubState)
        hub.form_open = True

    @rx.event(background=True)
    async def open_direct_help(self):
        """Freshly query my active requests every time the composer opens."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            helper = self.selected_helper
            self._reset_direct_composer()
            self.direct_open = True
            self.is_loading_direct = True
            self.error = ""
            self.success = ""
        if not sid.isdigit() or helper["id"] <= 0:
            async with self:
                self.is_loading_direct = False
                self.direct_notice = (
                    "Your session expired — please sign in again."
                )
            return
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT p.id, p.title, p.category,
                               COALESCE(p.category_tags, '')
                        FROM skillkind_help_post p
                        WHERE p.author_id = :sid
                          AND p.status = 'open'
                          AND (SELECT COUNT(*) FROM skillkind_job_application ca WHERE ca.post_id = p.id AND ca.status = 'accepted') < GREATEST(COALESCE(p.helpers_needed, 1), 1)
                          AND (p.expires_at IS NULL OR p.expires_at > now())
                          AND NOT EXISTS (
                              SELECT 1 FROM skillkind_completed_task ct
                              WHERE ct.post_id = p.id
                          )
                        ORDER BY p.created_at DESC
                        LIMIT 30
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).all()
        requests: list[DirectRequest] = []
        for row in rows:
            categories = post_categories(str(row[3] or ""), str(row[2] or ""))
            requests.append(
                {
                    "id": int(row[0]),
                    "title": str(row[1] or "Help needed"),
                    "categories": categories,
                    "category_label": ", ".join(category_labels(categories)),
                }
            )
        async with self:
            if (
                not self.direct_open
                or self.selected_helper["id"] != helper["id"]
            ):
                return
            self.direct_requests = requests
            self.is_loading_direct = False
            if not requests:
                self.direct_notice = (
                    "You need an active help request before you can ask a "
                    "helper directly. Post one from Ask for Help and then "
                    "come back to this profile."
                )

    @rx.event
    async def select_direct_request(self, value: str):
        """Pick which of my requests to ask about, and draft the message."""
        raw = str(value or "").strip()
        if not raw.isdigit():
            self.direct_post_id = 0
            self.direct_draft = ""
            self.direct_warning = ""
            return
        post_id = int(raw)
        chosen = [r for r in self.direct_requests if r["id"] == post_id]
        if not chosen:
            self.direct_post_id = 0
            self.direct_draft = ""
            self.direct_warning = ""
            return
        request = chosen[0]
        helper = self.selected_helper
        self.direct_post_id = post_id
        self.direct_warning = (
            ""
            if categories_overlap(request["categories"], helper["categories"])
            else "Make sure this person has the skills and knowledge required for this job"
        )
        auth = await self.get_state(AuthState)
        self.direct_draft = (
            f"Dear {helper['name']}, I have seen your profile and am asking "
            f"for your help to {request['title']}. Yours, "
            f"{auth.display_name}."
        )

    @rx.event
    def set_direct_draft(self, value: str):
        self.direct_draft = value[:2000]

    @rx.event(background=True)
    async def send_direct_help(self):
        try:
            async for event in self._send_direct_help():
                yield event
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = "We couldn't send your request. Please try again."
        finally:
            async with self:
                self.is_sending_direct = False

    async def _send_direct_help(self):
        """Create or reuse the thread and insert the opening message."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            if self.is_sending_direct:
                return
            helper = self.selected_helper
            post_id = int(self.direct_post_id)
            body = self.direct_draft.strip()
            chosen = [
                r
                for r in self.direct_requests
                if r["id"] == self.direct_post_id
            ]
            title = chosen[0]["title"] if chosen else ""
        problem = ""
        if not sid.isdigit():
            problem = "Your session expired — please sign in again."
        elif helper["id"] <= 0:
            problem = "Open a helper's profile first."
        elif post_id <= 0:
            problem = "Choose which of your help requests this is about."
        elif len(body) < 5:
            problem = "Write a short message before you send it."
        elif len(body) > 2000:
            problem = "Keep your message under 2000 characters."
        if problem:
            async with self:
                self.error = problem
                self.success = ""
            return
        async with self:
            self.is_sending_direct = True
            self.error = ""
            self.success = ""
        async with rx.asession() as asession:
            still_active = (
                await asession.execute(
                    text(
                        """
                        SELECT p.status FROM skillkind_help_post p
                        WHERE p.id = :post_id AND p.author_id = :sid
                          AND p.status = 'open'
                          AND (p.expires_at IS NULL OR p.expires_at > now())
                          AND (SELECT COUNT(*) FROM skillkind_job_application ca WHERE ca.post_id = p.id AND ca.status = 'accepted') < GREATEST(COALESCE(p.helpers_needed, 1), 1)
                        FOR UPDATE OF p
                        """
                    ),
                    {"post_id": post_id, "sid": int(sid)},
                )
            ).first()
            if still_active is None or str(still_active[0]) not in (
                "open",
                "matched",
            ):
                async with self:
                    self.is_sending_direct = False
                    self.error = (
                        "That request is no longer active — choose another one."
                    )
                yield DiscoveryState.open_direct_help
                return
            if await are_members_blocked(asession, int(sid), int(helper["id"])):
                await asession.rollback()
                async with self:
                    self.is_sending_direct = False
                    self._reset_direct_composer()
                    self.selected_helper = EMPTY_HELPER
                    self.error = BLOCK_UNAVAILABLE_MESSAGE
                return
            thread_id = await self._thread_for(
                asession, post_id, int(sid), int(helper["id"]), title
            )
            await asession.execute(
                text(
                    """
                    INSERT INTO skillkind_message (thread_id, sender_id, body)
                    VALUES (:thread_id, :sid, :body)
                    """
                ),
                {"thread_id": thread_id, "sid": int(sid), "body": body},
            )
            # The direct ask becomes a real pending application for that
            # helper, so they can Accept or Decline it from their Inbox. An
            # already accepted application is never downgraded.
            existing_app = (
                await asession.execute(
                    text(
                        """
                        SELECT id, status FROM skillkind_job_application
                        WHERE post_id = :post_id AND helper_id = :helper
                        """
                    ),
                    {"post_id": post_id, "helper": int(helper["id"])},
                )
            ).first()
            if existing_app is None:
                await asession.execute(
                    text(
                        """
                        INSERT INTO skillkind_job_application
                            (post_id, helper_id, pitch, status)
                        VALUES (:post_id, :helper, :pitch, 'pending')
                        """
                    ),
                    {
                        "post_id": post_id,
                        "helper": int(helper["id"]),
                        "pitch": body[:2000],
                    },
                )
            elif str(existing_app[1] or "") != "accepted":
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_job_application
                        SET status = 'pending', pitch = :pitch,
                            responded_at = NULL
                        WHERE id = :app_id
                        """
                    ),
                    {"pitch": body[:2000], "app_id": int(existing_app[0])},
                )
            await asession.execute(
                text(
                    """
                    INSERT INTO skillkind_member_notification
                        (recipient_id, kind, title, body, actor_id,
                         help_post_id, target_route)
                    VALUES (:helper, 'inbox_message', :title, :body,
                            :sid, :pid, '')
                    """
                ),
                {
                    "helper": int(helper["id"]),
                    "sid": int(sid),
                    "pid": post_id,
                    "title": f"A direct request for your help: {title}"[:200],
                    "body": body[:255],
                },
            )
            await asession.commit()
        async with self:
            self.is_sending_direct = False
            self._reset_direct_composer()
            self.thread_id = thread_id
            self.thread_with = inline_recipient_name(helper["name"])
            self.thread_note = body
            self.success = f"Your request is on its way to {helper['name']}."
        yield rx.toast(
            f"Request sent to {helper['name']}.",
            duration=4000,
        )

    @rx.event(background=True)
    async def load_helpers(self):
        async with self:
            self.loading_count += 1
        try:
            await self._load_helpers()
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = "Helpers could not be loaded. Please try again."
        finally:
            async with self:
                self.loading_count = max(0, self.loading_count - 1)

    async def _load_helpers(self):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            chosen_categories = list(self.category_filters)
            city = self.city_filter.strip()
            selected_id = self.pending_helper_id or self.selected_helper["id"]
            self.pending_helper_id = 0
            distance_km = int(self.distance_km)
            distance_seeded = self.distance_initialized
            premium = await self._premium_now()
            advanced_clause, advanced_params = self._advanced_clause(
                premium, "pr", "s", "helper_rating_avg"
            )
        if not sid.isdigit():
            async with self:
                self.helpers = []
                self.selected_helper = EMPTY_HELPER
                self.helper_total = 0
            return
        async with self:
            self.error = ""

        member_lat, member_lng, saved_radius = await self._viewer_point(
            int(sid)
        )
        if not distance_seeded:
            distance_km = (
                clamp_distance_km(saved_radius)
                if saved_radius > 0
                else DEFAULT_DISTANCE_KM
            )
            async with self:
                self.distance_km = distance_km
                self.distance_initialized = True
                self.distance_reset_token += 1

        if distance_km > 0 and (member_lat is None or member_lng is None):
            # Never silently widen a distance search to the whole world.
            async with self:
                self.helpers = []
                self.selected_helper = EMPTY_HELPER
                self.helper_total = 0
            return

        # Only members who opted in to sharing, with real stored coordinates,
        # appear on member maps and in member search. The stored numbers are
        # used privately for distance filtering only — every published point
        # is the deterministic land-safe approximate offset.
        where = (
            "WHERE s.is_active = TRUE AND s.id <> :sid "
            f"AND COALESCE(pr.location_mode, 'hidden') IN {VISIBLE_LOCATION_SQL} "
            "AND COALESCE(pr.show_location, FALSE) = TRUE "
            "AND pr.latitude IS NOT NULL AND pr.longitude IS NOT NULL "
            # Directional hiding: members this viewer blocked never appear.
            f"AND {not_blocked_author_sql('s.id')}"
        )
        params: dict[str, str | int | float] = {"sid": int(sid)}
        where += advanced_clause
        params.update(advanced_params)
        if (
            distance_km > 0
            and member_lat is not None
            and member_lng is not None
        ):
            # Parameterized great-circle (Haversine / spherical law of cosines)
            # distance in kilometres, computed entirely in the database from
            # the viewer's private point to the helper's stored point.
            where += (
                " AND (6371.0 * acos(LEAST(1.0, GREATEST(-1.0,"
                " sin(radians(:member_lat))"
                " * sin(radians(CAST(pr.latitude AS DOUBLE PRECISION)))"
                " + cos(radians(:member_lat))"
                " * cos(radians(CAST(pr.latitude AS DOUBLE PRECISION)))"
                " * cos(radians(CAST(pr.longitude AS DOUBLE PRECISION))"
                " - radians(:member_lng))"
                " )))) <= :max_distance_km"
            )
            params["member_lat"] = float(member_lat)
            params["member_lng"] = float(member_lng)
            params["max_distance_km"] = float(distance_km)
        category_tokens = expand_category_tokens(chosen_categories)
        if category_tokens:
            # Token-wise match against the helper's stored multi-select set, so
            # "carer" never matches "carer_assistant" style neighbours by luck.
            pieces: list[str] = []
            for index, token in enumerate(category_tokens):
                key = f"pref_cat_{index}"
                pieces.append(
                    "(',' || LOWER(REPLACE("
                    "COALESCE(pr.preferred_categories, ''), ' ', ''))"
                    f" || ',') LIKE :{key}"
                )
                params[key] = f"%,{token},%"
            where += " AND (" + " OR ".join(pieces) + ")"
        if city:
            where += " AND LOWER(COALESCE(pr.current_city, '')) LIKE :city"
            params["city"] = f"%{city.lower()}%"

        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT s.id, s.display_name, CONCAT('member-', s.id), s.help_mode,
                               COALESCE(pr.headline, ''),
                               COALESCE(pr.current_city, ''),
                               COALESCE(pr.languages, ''),
                               COALESCE(pr.skills, ''),
                               COALESCE(pr.availability_note, ''),
                               COALESCE(pr.avatar_path, ''),
                               COALESCE(pr.helper_rating_avg, 0),
                               COALESCE(pr.helper_rating_count, 0),
                               COALESCE(pr.tasks_helped_count, 0),
                               COALESCE(pr.kindness_points, 0),
                               s.joined_at,
                               pr.latitude, pr.longitude,
                               COALESCE(pr.location_mode, 'hidden'),
                               COALESCE(pr.username, ''),
                               COALESCE(pr.preferred_categories, ''),
                               COALESCE(pr.tasks_received_count, 0)
                        FROM skillkind_subscriber s
                        LEFT JOIN skillkind_profile pr ON pr.subscriber_id = s.id
                        {where}
                        ORDER BY COALESCE(pr.kindness_points, 0) DESC,
                                 s.joined_at DESC
                        LIMIT {DISCOVERY_RESULT_CAP}
                        """
                    ),
                    params,
                )
            ).all()
            total_row = (
                await asession.execute(
                    text(
                        f"""
                        SELECT COUNT(*)
                        FROM skillkind_subscriber s
                        LEFT JOIN skillkind_profile pr
                               ON pr.subscriber_id = s.id
                        {where}
                        """
                    ),
                    params,
                )
            ).first()

        loaded: list[HelperProfile] = []
        for r in rows:
            helper_id = int(r[0])
            mode = str(r[3] or "both")
            source_lat = float(r[15])
            source_lng = float(r[16])
            # Legacy `live` rows are treated as opted-in approximate sources:
            # the helper stays visible, but only ever 0.5–1 km away.
            offset = profile_approximate(helper_id, source_lat, source_lng)
            if offset is None:
                # No land-safe 0.5–1 km point: leave this helper off the map
                # rather than risk an exact or sea placement.
                continue
            lat, lng = offset
            avatar_path = str(r[9] or "")
            avatar_seed = str(r[2] or "")
            handle = str(r[18] or "")
            helper_categories = split_categories(str(r[19] or ""))
            skills_text = str(r[7] or "")
            loaded.append(
                {
                    "id": helper_id,
                    "name": str(r[1] or "A neighbour"),
                    "avatar_seed": avatar_seed,
                    "username": handle,
                    "handle": f"@{handle}" if handle else "",
                    "headline": str(r[4] or ""),
                    "city": str(r[5] or ""),
                    "languages": str(r[6] or ""),
                    "skills": skills_text,
                    "categories": helper_categories,
                    "category_chips": category_labels(helper_categories),
                    "skill_chips": [
                        part.strip()
                        for part in skills_text.split(",")
                        if part.strip()
                    ][:12],
                    "primary_category": primary_category(helper_categories),
                    "availability": str(r[8] or ""),
                    "avatar_path": avatar_path,
                    "image_url": _avatar_image_url(avatar_path, avatar_seed),
                    "help_mode": mode,
                    "mode_label": "Can offer help"
                    if mode == "offer_help"
                    else "Helps & receives",
                    "rating": float(r[10] or 0),
                    "reviews": int(r[11] or 0),
                    "tasks_helped": int(r[12] or 0),
                    "tasks_received": int(r[20] or 0) if len(r) > 20 else 0,
                    "kindness": int(r[13] or 0),
                    "joined": r[14].strftime("%b %d, %Y")
                    if r[14] is not None
                    else "",
                    "lng": lng,
                    "lat": lat,
                }
            )
        async with self:
            self.helpers = loaded
            self.helper_total = int(total_row[0] or 0) if total_row else 0
            match = [h for h in loaded if h["id"] == selected_id]
            if match and self.selected_helper["id"] == selected_id:
                self.selected_helper = match[0]

    @rx.event
    def set_category_filter(self, value: str):
        self.category_filter = value
        self.error = ""
        self.success = ""
        return DiscoveryState.refresh_board

    @rx.event
    def set_reward_filter(self, value: str):
        self.reward_filter = value
        self.error = ""
        self.success = ""
        return DiscoveryState.refresh_board

    @rx.event
    def set_city_filter(self, value: str):
        self.city_filter = value
        return DiscoveryState.refresh_board

    @rx.event
    def pick_category(self, value: str):
        self.category_filter = "all" if self.category_filter == value else value
        return DiscoveryState.refresh_board

    @rx.event
    def clear_filters(self):
        self.distance_warning = False
        self.category_filter
        self.category_filters = []
        self.reward_filter = "all"
        self.city_filter = ""
        # Clearing filters means every distance, explicitly.
        self.distance_km = 0
        self.distance_initialized = True
        self.distance_reset_token += 1
        self.last_online_filter = "any"
        self.rating_min = 0
        self.rating_max = 100
        self.nationality_filter = ""
        self.language_filters = []
        return DiscoveryState.refresh_board

    @rx.event
    async def toggle_filter_panel(self):
        from app.states.notification_state import NotificationState
        from app.states.profile_state import ProfileState
        from app.states.world_search_state import WorldSearchState

        opening = not self.filter_panel_open
        if opening:
            (await self.get_state(NotificationState)).panel_open = False
            (await self.get_state(ProfileState)).settings_open = False
            (await self.get_state(WorldSearchState)).expanded = False
        self.filter_panel_open = opening

    @rx.event
    def close_filters(self):
        self.filter_panel_open = False
        self.category_list_open = False

    @rx.event
    async def select_post(self, post_id: int):
        """Select the loaded post at once, then count the view separately."""
        self.map_pulse_post_id = 0
        if self.view_mode == VIEW_LIST and self.selected_post["id"] == post_id:
            self.clear_selection()
            self.error = ""
            self.success = ""
            return
        self.map_mode = MODE_GIVE
        self.selected_helper = EMPTY_HELPER
        self.error
        self.success = ""
        self._reset_offer_draft()
        self.thread_id = 0
        self.thread_note = ""
        self.error = ""
        self.group_poster_id = 0
        match = [post for post in self.posts if post["id"] == post_id]
        self.selected_post = match[0] if match else EMPTY_POST
        author_id = int(self.selected_post["poster_id"] or 0)
        viewer = (await self.get_state(AuthState)).subscriber_id
        # Flush the selection to the browser before touching the database.
        yield
        if not match or not viewer.isdigit() or int(viewer) == author_id:
            return
        try:
            async with rx.asession() as asession:
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_help_post
                        SET view_count = COALESCE(view_count, 0) + 1
                        WHERE id = :pid AND author_id <> :sid
                        """
                    ),
                    {"pid": int(post_id), "sid": int(viewer)},
                )
                await asession.commit()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Could not record a request view: {e}")

    @rx.event
    async def open_shared_post(self, post_id: int):
        auth = await self.get_state(AuthState)
        if not auth.is_signed_in or not auth.subscriber_id.isdigit():
            return
        sid = int(auth.subscriber_id)
        try:
            async with rx.asession() as session:
                row = (
                    await session.execute(
                        text("""
                    SELECT p.id, p.title, p.description, p.category,
                           p.reward_type, p.reward_details, '', p.city, p.country,
                           p.scheduled_for, p.duration_minutes, p.urgency, p.status,
                           p.created_at, s.id, s.display_name, CONCAT('member-', s.id),
                           COALESCE(pr.headline, ''), COALESCE(pr.current_city, ''),
                           COALESCE(pr.languages, ''), COALESCE(pr.skills, ''),
                           COALESCE(pr.traveller_rating_avg, 0),
                           COALESCE(pr.traveller_rating_count, 0),
                           (SELECT COUNT(*) FROM skillkind_job_application a WHERE a.post_id = p.id),
                           COALESCE((SELECT a.status FROM skillkind_job_application a
                               WHERE a.post_id = p.id AND a.helper_id = :sid LIMIT 1), 'none'),
                           p.latitude, p.longitude, pr.latitude, pr.longitude,
                           COALESCE(pr.location_mode, 'hidden'), COALESCE(pr.avatar_path, ''),
                           COALESCE(p.location_mode, 'approximate'), COALESCE(p.category_tags, ''),
                           COALESCE(s.is_verified, FALSE),
                                                          COALESCE(p.reward_types, ''), COALESCE(p.reward_value, 0),
                                                          COALESCE(p.reward_currency, 'USD')
                    FROM skillkind_help_post p
                    JOIN skillkind_subscriber s ON s.id = p.author_id
                    LEFT JOIN skillkind_profile pr ON pr.subscriber_id = s.id
                    WHERE p.id = :pid AND p.status = 'open' AND s.is_active = TRUE
                      AND NOT EXISTS (SELECT 1 FROM skillkind_completed_task ct WHERE ct.post_id = p.id)
                      AND (p.expires_at IS NULL OR p.expires_at > now())
                      AND (SELECT COUNT(*) FROM skillkind_job_application a
                           WHERE a.post_id = p.id AND a.status = 'accepted')
                          < GREATEST(COALESCE(p.helpers_needed, 1), 1)
                    LIMIT 1
                """),
                        {"pid": post_id, "sid": sid},
                    )
                ).first()
                if row is None or await are_members_blocked(
                    session, sid, int(row[14])
                ):
                    return rx.toast(
                        "That shared request is unavailable. Explore other requests on the map."
                    )
                photos = (
                    await session.execute(
                        text("""
                    SELECT path FROM skillkind_help_post_photo
                    WHERE help_post_id = :pid ORDER BY display_order LIMIT 20
                """),
                        {"pid": post_id},
                    )
                ).all()
            post = self._row_to_post(row, [str(photo[0]) for photo in photos])
            if post is None:
                self.selected_post = EMPTY_POST
                return
            self.selected_post = post
            self.view_mode = VIEW_MAP
            self.map_mode = MODE_GIVE
            self.selected_helper = EMPTY_HELPER
            self.group_poster_id = 0
            self.map_center = [
                self.selected_post["lng"],
                self.selected_post["lat"],
            ]
            self.map_zoom = 10.0
            self._reset_offer_draft()
        except Exception as e:
            logging.exception(f"Error: {e}")
            return rx.toast(
                "We couldn't open that shared request. Please try again."
            )

    @rx.event
    def clear_selection(self):
        self.map_pulse_post_id = 0
        self.selected_post = EMPTY_POST
        self.selected_helper = EMPTY_HELPER
        self._reset_offer_draft()
        self._reset_direct_composer()
        self.group_poster_id = 0
        self.thread_id = 0
        self.thread_with = ""
        self.thread_note = ""

    @rx.event(background=True)
    async def load_jobs(self):
        async with self:
            self.loading_count += 1
        try:
            async for event in self._load_jobs():
                yield event
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = "Requests could not be loaded. Please try again."
        finally:
            async with self:
                self.loading_count = max(0, self.loading_count - 1)

    async def _load_jobs(self):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            chosen_categories = list(self.category_filters)
            reward = self.reward_filter
            city = self.city_filter.strip()
            selected_id = self.pending_post_id or self.selected_post["id"]
            self.pending_post_id = 0
            distance_km = int(self.distance_km)
            distance_seeded = self.distance_initialized
            list_mode = self.view_mode == VIEW_LIST
            priority_ids = (
                list(self._field_priority_post_ids)
                if self._field_priority_owner == sid
                else []
            )
            premium = await self._premium_now()
            advanced_clause, advanced_params = self._advanced_clause(
                premium, "pr", "s", "traveller_rating_avg"
            )
        if not sid.isdigit():
            async with self:
                self.posts = []
                self.selected_post = EMPTY_POST
                self.category_counts = EMPTY_CATEGORY_COUNTS
                self.open_total = 0
            return
        async with self:
            self.error = ""

        # The member's own point stays in this event handler: it is only ever
        # used as a bound SQL parameter and never written into state.
        member_lat, member_lng, saved_radius = await self._viewer_point(
            int(sid)
        )

        if not distance_seeded:
            distance_km = (
                clamp_distance_km(saved_radius)
                if saved_radius > 0
                else DEFAULT_DISTANCE_KM
            )
            async with self:
                self.distance_km = distance_km
                self.distance_initialized = True
                self.distance_reset_token += 1

        missing_viewer_point = distance_km > 0 and (
            member_lat is None or member_lng is None
        )

        safety_where = (
            "WHERE p.status = 'open' AND s.is_active = TRUE "
            "AND NOT EXISTS (SELECT 1 FROM skillkind_completed_task ct WHERE ct.post_id = p.id) "
            "AND (SELECT COUNT(*) FROM skillkind_job_application ca WHERE ca.post_id = p.id AND ca.status = 'accepted') < GREATEST(COALESCE(p.helpers_needed, 1), 1) "
            f"AND {ACTIVE_POST_CLAUSE} "
            # Directional hiding: authors this viewer blocked never appear.
            f"AND {not_blocked_author_sql('p.author_id')}"
        )
        owned_where = f"{safety_where} AND p.author_id = :sid"
        where = f"{safety_where} AND p.author_id <> :sid"
        # A missing private origin must never widen external discovery.
        if missing_viewer_point:
            where = f"{where} AND FALSE"
        params: dict[str, str | int | float] = {"sid": int(sid)}
        where += advanced_clause
        params.update(advanced_params)
        if (
            distance_km > 0
            and member_lat is not None
            and member_lng is not None
        ):
            # Parameterized great-circle (Haversine / spherical law of cosines)
            # distance in kilometres, computed entirely in the database.
            where += (
                " AND p.latitude IS NOT NULL AND p.longitude IS NOT NULL"
                " AND (6371.0 * acos(LEAST(1.0, GREATEST(-1.0,"
                " sin(radians(:member_lat))"
                " * sin(radians(CAST(p.latitude AS DOUBLE PRECISION)))"
                " + cos(radians(:member_lat))"
                " * cos(radians(CAST(p.latitude AS DOUBLE PRECISION)))"
                " * cos(radians(CAST(p.longitude AS DOUBLE PRECISION))"
                " - radians(:member_lng))"
                " )))) <= :max_distance_km"
            )
            params["member_lat"] = float(member_lat)
            params["member_lng"] = float(member_lng)
            params["max_distance_km"] = float(distance_km)
        category_tokens = expand_category_tokens(chosen_categories)
        if category_tokens:
            # A request matches when ANY of its category tags matches, with the
            # legacy single `category` column covering rows saved before tags.
            pieces: list[str] = []
            for index, token in enumerate(category_tokens):
                exact_key = f"job_cat_{index}"
                tag_key = f"job_tag_{index}"
                pieces.append(
                    f"(p.category = :{exact_key}"
                    " OR (',' || LOWER(REPLACE(COALESCE(p.category_tags, ''),"
                    f" ' ', '')) || ',') LIKE :{tag_key})"
                )
                params[exact_key] = token
                params[tag_key] = f"%,{token},%"
            where += " AND (" + " OR ".join(pieces) + ")"
        if reward == "money" or reward in REWARD_LABELS:
            where += (
                " AND (p.reward_type = :reward"
                " OR (',' || LOWER(REPLACE(COALESCE(p.reward_types, ''),"
                " ' ', '')) || ',') LIKE :reward_token)"
            )
            params["reward"] = reward
            params["reward_token"] = f"%,{reward},%"
        if city:
            where += " AND LOWER(p.city) LIKE :city"
            params["city"] = f"%{city.lower()}%"

        # List mode surfaces premium posts first, then newest; map mode keeps
        # the existing urgency/schedule ordering.
        order_by = (
            "p.premium_priority DESC, p.created_at DESC"
            if list_mode
            else (
                "CASE p.urgency WHEN 'urgent' THEN 0 WHEN 'soon' THEN 1 "
                "ELSE 2 END, p.scheduled_for ASC NULLS LAST, "
                "p.created_at DESC"
            )
        )
        select_sql = """
                        SELECT p.id, p.title, p.description, p.category,
                               p.reward_type, p.reward_details, p.location_name,
                               p.city, p.country, p.scheduled_for,
                               p.duration_minutes, p.urgency, p.status, p.created_at,
                               s.id, s.display_name, CONCAT('member-', s.id),
                               COALESCE(pr.headline, ''),
                               COALESCE(pr.current_city, ''),
                               COALESCE(pr.languages, ''),
                               COALESCE(pr.skills, ''),
                               COALESCE(pr.traveller_rating_avg, 0),
                               COALESCE(pr.traveller_rating_count, 0),
                               (SELECT COUNT(*) FROM skillkind_job_application a
                                 WHERE a.post_id = p.id),
                               COALESCE((SELECT a2.status FROM skillkind_job_application a2
                                 WHERE a2.post_id = p.id AND a2.helper_id = :sid
                                 LIMIT 1), 'none'),
                               p.latitude, p.longitude,
                               pr.latitude, pr.longitude,
                               COALESCE(pr.location_mode, 'hidden'),
                               COALESCE(pr.avatar_path, ''),
                               COALESCE(p.location_mode, 'approximate'),
                               COALESCE(p.category_tags, ''),
                               COALESCE(s.is_verified, FALSE),
                               COALESCE(p.reward_types, ''), COALESCE(p.reward_value, 0),
                               COALESCE(p.reward_currency, 'USD')
                        FROM skillkind_help_post p
                        JOIN skillkind_subscriber s ON s.id = p.author_id
                        LEFT JOIN skillkind_profile pr ON pr.subscriber_id = s.id
                        """
        async with rx.asession() as asession:
            priority_rows = []
            if priority_ids:
                priority_rows = (
                    await asession.execute(
                        text(f"""
                    {select_sql} {safety_where} AND p.id=ANY(:priority_ids)
                      AND EXISTS (SELECT 1 FROM skillkind_member_notification n
                          WHERE n.recipient_id=:sid AND n.help_post_id=p.id AND n.kind='requests_in_my_field')
                      AND NOT EXISTS (SELECT 1 FROM skillkind_member_block b
                          WHERE b.blocker_id=p.author_id AND b.blocked_id=:sid)
                    ORDER BY p.created_at DESC LIMIT {DISCOVERY_RESULT_CAP}
                """),
                        {"sid": int(sid), "priority_ids": priority_ids},
                    )
                ).all()
            owned_rows = (
                await asession.execute(
                    text(
                        f"{select_sql} {owned_where} ORDER BY {order_by} LIMIT {DISCOVERY_RESULT_CAP}"
                    ),
                    {"sid": int(sid)},
                )
            ).all()
            external_rows = (
                (
                    await asession.execute(
                        text(
                            f"{select_sql} {where} ORDER BY {order_by} LIMIT {DISCOVERY_RESULT_CAP}"
                        ),
                        params,
                    )
                ).all()
                if not missing_viewer_point
                else []
            )
            rows = []
            seen: set[int] = set()
            for row in [*priority_rows, *owned_rows, *external_rows]:
                post_id = int(row[0])
                if post_id in seen:
                    continue
                seen.add(post_id)
                # Unusable locations must not consume the bounded map slots.
                if self._row_to_post(row, [], post_id in priority_ids) is None:
                    continue
                rows.append(row)
                if len(rows) >= DISCOVERY_RESULT_CAP:
                    break
            count_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT category, COUNT(*)
                        FROM skillkind_help_post p
                        JOIN skillkind_subscriber s ON s.id = p.author_id
                        WHERE p.status = 'open' AND p.author_id <> :sid
                          AND s.is_active = TRUE
                          AND NOT EXISTS (SELECT 1 FROM skillkind_completed_task ct WHERE ct.post_id = p.id)
                                                  AND (SELECT COUNT(*) FROM skillkind_job_application ca WHERE ca.post_id = p.id AND ca.status = 'accepted') < GREATEST(COALESCE(p.helpers_needed, 1), 1)
                          AND (p.expires_at IS NULL OR p.expires_at > now())
                          AND NOT EXISTS (
                              SELECT 1 FROM skillkind_member_block mb
                              WHERE mb.blocker_id = :sid
                                AND mb.blocked_id = p.author_id
                          )
                        GROUP BY p.category
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).all()
            if missing_viewer_point:
                count_rows = []
            post_ids = [int(row[0]) for row in rows]
            photo_map: dict[int, list[str]] = {
                post_id: [] for post_id in post_ids
            }
            if post_ids:
                photo_params: dict[str, int] = {
                    f"photo_post_{index}": post_id
                    for index, post_id in enumerate(post_ids)
                }
                photo_placeholders = ", ".join(
                    f":photo_post_{index}" for index in range(len(post_ids))
                )
                photo_rows = (
                    await asession.execute(
                        text(
                            f"""
                            SELECT help_post_id, path
                            FROM skillkind_help_post_photo
                            WHERE help_post_id IN ({photo_placeholders})
                            ORDER BY help_post_id, display_order
                            """
                        ),
                        photo_params,
                    )
                ).all()
                for photo_row in photo_rows:
                    photo_map[int(photo_row[0])].append(str(photo_row[1]))

        loaded = [
            post
            for r in rows
            if (
                post := self._row_to_post(
                    r, photo_map.get(int(r[0]), []), int(r[0]) in priority_ids
                )
            )
            is not None
        ]
        counts = dict(EMPTY_CATEGORY_COUNTS)
        total = 0
        for r in count_rows:
            key = str(r[0] or "")
            value = int(r[1] or 0)
            total += value
            if key in counts:
                counts[key] = value
        async with self:
            if (await self.get_state(AuthState)).subscriber_id != sid:
                return
            self._field_priority_post_ids = [
                post["id"] for post in loaded if post["id"] in priority_ids
            ]
            self.posts = loaded
            self.category_counts = counts
            self.open_total = total
            match = [p for p in loaded if p["id"] == selected_id]
            self.selected_post = match[0] if match else EMPTY_POST
        # Bookmark state is loaded with the board so the list, the map and the
        # detail drawer always show the same filled / unfilled tabs.
        from app.states.bookmark_state import BookmarkState

        yield BookmarkState.load_bookmarks
        from app.states.help_share_state import HelpShareState

        yield HelpShareState.resolve
