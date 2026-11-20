"""Privacy-safe guest previews with approximate request locations."""

import asyncio
import hashlib
import logging
import re
from typing import Any, TypedDict

import reflex as rx
from sqlalchemy import text
from sqlalchemy.exc import InterfaceError, OperationalError

from app.components.openfreemap import MapMarker
from app.location_privacy import post_guest_approximate, profile_approximate
from app.filter_categories import (
    FILTER_CATEGORIES,
    FilterCategory,
    expand_category_tokens,
    category_label,
)
from app.models import HELP_MODE_OFFER, HELP_MODE_BOTH, TASK_CATEGORIES
from app.reward_display import REWARD_LABELS

PAGE_SIZE = 100
MAX_DB_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 0.25
MAX_QUERY_LENGTH = 160
GUEST_CATEGORIES: list[FilterCategory] = [
    item for item in FILTER_CATEGORIES if item["value"] in TASK_CATEGORIES
]
GUEST_REWARDS: list[dict[str, str]] = [
    {"value": "all", "label": "Any reward"},
    {"value": "money", "label": "Money"},
    *[{"value": code, "label": label} for code, label in REWARD_LABELS.items()],
]


class GuestJob(TypedDict):
    code: str
    title: str
    description: str
    lng: float
    lat: float


class GuestHelper(TypedDict):
    code: str
    lat: float
    lng: float


GuestRow = tuple[int, str, str, float | None, float | None]
GuestHelperRow = tuple[int, float | None, float | None]


def _reference_code(post_id: int) -> str:
    digest = hashlib.sha256(f"goandhelp-ref::{post_id}".encode()).hexdigest()
    return digest


def _public_job(row: GuestRow) -> GuestJob | None:
    post_id, title, description, latitude, longitude = row
    point = post_guest_approximate(post_id, latitude, longitude)
    if point is None:
        return None
    return {
        "code": _reference_code(post_id),
        "title": title.strip() or "Help needed",
        "description": description[:100],
        "lat": point[0],
        "lng": point[1],
    }


def _helper_reference_code(subscriber_id: int) -> str:
    digest = hashlib.sha256(
        f"goandhelp-helper-ref::{subscriber_id}".encode()
    ).hexdigest()
    return f"helper:{digest}"


def _public_helper(row: GuestHelperRow) -> GuestHelper | None:
    subscriber_id, latitude, longitude = row
    point = profile_approximate(subscriber_id, latitude, longitude)
    if point is None:
        return None
    return {
        "code": _helper_reference_code(subscriber_id),
        "lat": point[0],
        "lng": point[1],
    }


def guest_preview_query(
    mode: str = "give",
    query: str = "",
    categories: list[str] | None = None,
    reward: str = "all",
) -> tuple[str, dict[str, str | int]]:
    """Build a read-only statement; all visitor values are bound parameters."""
    params: dict[str, str | int] = {"page_size": PAGE_SIZE}
    keyword = query.strip()[:MAX_QUERY_LENGTH]
    tokens = expand_category_tokens(
        [value for value in (categories or []) if value in TASK_CATEGORIES]
    )
    clauses: list[str] = []
    if mode == "get":
        sql = """
            SELECT s.id, pr.latitude, pr.longitude
            FROM skillkind_subscriber s
            JOIN skillkind_profile pr ON pr.subscriber_id = s.id
            WHERE s.is_active = TRUE
              AND s.help_mode IN (:offer_mode, :both_mode)
              AND COALESCE(pr.show_location, FALSE) = TRUE
              AND pr.location_mode IN ('approximate', 'live', 'fixed')
              AND pr.latitude BETWEEN -90 AND 90
              AND pr.longitude BETWEEN -180 AND 180
        """
        params.update(offer_mode=HELP_MODE_OFFER, both_mode=HELP_MODE_BOTH)
        if keyword:
            clauses.append(
                "AND (pr.current_city ILIKE :keyword ESCAPE '\\' OR pr.nationality ILIKE :keyword ESCAPE '\\' OR pr.preferred_categories ILIKE :keyword ESCAPE '\\')"
            )
        category_column = "COALESCE(pr.preferred_categories, '')"
        order = "ORDER BY s.id DESC LIMIT :page_size"
    else:
        sql = """
            SELECT p.id, p.title, LEFT(COALESCE(p.description, ''), 100), p.latitude, p.longitude
            FROM skillkind_help_post p
            JOIN skillkind_subscriber s ON s.id = p.author_id
            WHERE p.status = 'open' AND s.is_active = TRUE
              AND (SELECT COUNT(*) FROM skillkind_job_application ca
                   WHERE ca.post_id = p.id AND ca.status = 'accepted')
                  < GREATEST(COALESCE(p.helpers_needed, 1), 1)
              AND (p.expires_at IS NULL OR p.expires_at > now())
              AND NOT EXISTS (SELECT 1 FROM skillkind_completed_task ct WHERE ct.post_id = p.id)
              AND p.location_mode IN ('approximate', 'place', 'live', 'fixed')
              AND p.latitude BETWEEN -90 AND 90
              AND p.longitude BETWEEN -180 AND 180
        """
        if keyword:
            clauses.append(
                "AND (p.title ILIKE :keyword ESCAPE '\\' OR p.city ILIKE :keyword ESCAPE '\\' OR p.country ILIKE :keyword ESCAPE '\\')"
            )
        category_column = "concat_ws(',', p.category, p.category_tags)"
        if reward == "money" or reward in REWARD_LABELS:
            clauses.append(
                "AND (p.reward_type = :reward OR (',' || LOWER(REPLACE(COALESCE(p.reward_types, ''), ' ', '')) || ',') LIKE :reward_token)"
            )
            params.update(reward=reward, reward_token=f"%,{reward},%")
        order = "ORDER BY p.id DESC LIMIT :page_size"
    if keyword:
        escaped = (
            keyword.replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )
        params["keyword"] = f"%{escaped}%"
    if tokens:
        alternatives = "|".join(re.escape(token) for token in tokens)
        params["categories"] = (
            f"(^|[,;|[:space:]])({alternatives})($|[,;|[:space:]])"
        )
        clauses.append(f"AND {category_column} ~* :categories")
    return "\n".join([sql, *clauses, order]), params


async def fetch_guest_preview(
    mode: str = "give",
    query: str = "",
    categories: list[str] | None = None,
    reward: str = "all",
) -> tuple[list[GuestJob], list[GuestHelper]]:
    """Fetch at most 100 private rows, then publish only safe projections."""
    sql, params = guest_preview_query(mode, query, categories, reward)
    for attempt in range(1, MAX_DB_ATTEMPTS + 1):
        try:
            async with rx.asession() as session:
                rows = (await session.execute(text(sql), params)).all()
            break
        except (OperationalError, InterfaceError):
            if attempt == MAX_DB_ATTEMPTS:
                raise
            logging.warning(
                "Retrying guest map preview (%s/%s)", attempt, MAX_DB_ATTEMPTS
            )
            await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)
        except RuntimeError as error:
            unavailable = any(
                phrase in str(error).lower()
                for phrase in (
                    "database is not initialized",
                    "database not initialized",
                    "database is unavailable",
                    "database unavailable",
                    "temporarily unavailable",
                )
            )
            if not unavailable or attempt == MAX_DB_ATTEMPTS:
                raise
            await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)
    jobs: list[GuestJob] = []
    helpers: list[GuestHelper] = []
    for row in rows:
        if mode == "get":
            helper = await asyncio.to_thread(
                _public_helper, (int(row[0]), row[1], row[2])
            )
            if helper is not None:
                helpers.append(helper)
        else:
            job = await asyncio.to_thread(
                _public_job,
                (
                    int(row[0]),
                    str(row[1] or ""),
                    str(row[2] or ""),
                    row[3],
                    row[4],
                ),
            )
            if job is not None:
                jobs.append(job)
    return jobs, helpers


class GuestMapState(rx.State):
    """Transient guest filters and privacy-safe public map projections."""

    jobs: list[GuestJob] = []
    helpers: list[GuestHelper] = []
    category_filters: list[str] = []
    category_list_open: bool = False
    reward_filter: str = "all"
    _preview_generation: int = 0
    open_total: int = 0
    is_loading: bool = True
    loaded: bool = False
    load_message: str = ""
    wall_open: bool = False
    wall_reason: str = ""
    preview_title: str = ""
    preview_description: str = ""
    search_expanded: bool = False
    search_query: str = ""
    # Map-only even if a client forges a list-view value.
    view_mode: str = "map"
    browse_mode: str = "give"
    map_center: list[float] = [10.0, 46.5]
    map_zoom: float = 3.6

    @rx.var
    def has_jobs(self) -> bool:
        return len(self.jobs) > 0

    @rx.var
    def is_list_view(self) -> bool:
        return False

    @rx.var
    def filter_category_options(self) -> list[FilterCategory]:
        return GUEST_CATEGORIES

    @rx.var
    def reward_filter_options(self) -> list[dict[str, str]]:
        return GUEST_REWARDS

    @rx.var
    def category_summary_label(self) -> str:
        return (
            category_label(self.category_filters[0])
            if self.category_filters
            else "All categories"
        )

    @rx.var
    def filters_active(self) -> bool:
        return bool(
            self.search_query
            or self.category_filters
            or self.reward_filter != "all"
        )

    @rx.var
    def map_markers(self) -> list[MapMarker]:
        """Only server-obfuscated public points reach the map."""
        if self.browse_mode == "get":
            return [
                {
                    "id": helper["code"],
                    "lng": helper["lng"],
                    "lat": helper["lat"],
                    "label": "Give help",
                    "kind": "helper",
                    "selected": False,
                    "icon": "hand-helping",
                    "color": "#fba922",
                    "image_url": "",
                }
                for helper in self.helpers
            ]
        return [
            {
                "id": job["code"],
                "lng": job["lng"],
                "lat": job["lat"],
                "label": job["title"],
                "kind": "job",
                "selected": False,
                "icon": "hand-helping",
                "color": "#fba922",
                "image_url": "",
            }
            for job in self.jobs
        ]

    @rx.var
    async def localized_map_markers(self) -> list[MapMarker]:
        from app.interface_i18n import translate
        from app.states.auth_state import AuthState

        auth = await self.get_state(AuthState)
        language = auth.preferred_language
        return [
            {
                **marker,
                "label": translate(language, "Give help")
                if marker["kind"] == "helper"
                else marker["label"],
            }
            for marker in self.map_markers
        ]

    @rx.event
    def set_view_mode(self, mode: str):
        self.view_mode = "map"

    @rx.event
    def expand_search(self):
        self.search_expanded = True

    @rx.event
    def collapse_search(self):
        self.search_expanded = False
        self.category_list_open = False

    @rx.event
    def set_search_query(self, value: str):
        self.search_query = value.strip()[:MAX_QUERY_LENGTH]
        self._invalidate_preview()
        yield GuestMapState.load_preview

    def _invalidate_preview(self):
        self._preview_generation += 1
        self.jobs = []
        self.helpers = []
        self.open_total = 0
        self.is_loading = True
        self.load_message = ""

    @rx.event
    def submit_search(self, form_data: dict[str, Any]):
        self.search_query = str(form_data.get("guest_search", "")).strip()[
            :MAX_QUERY_LENGTH
        ]
        self._invalidate_preview()
        yield GuestMapState.load_preview

    @rx.event
    def set_browse_mode(self, mode: str):
        self.browse_mode = "get" if mode == "get" else "give"
        self.view_mode = "map"
        self.preview_title = ""
        self.preview_description = ""
        self._invalidate_preview()
        yield GuestMapState.load_preview

    @rx.event
    def toggle_category_list(self):
        self.category_list_open = not self.category_list_open

    @rx.event
    def toggle_category_choice(self, value: str):
        if value not in TASK_CATEGORIES:
            return
        if value in self.category_filters:
            self.category_filters.remove(value)
        else:
            self.category_filters.append(value)
        self._invalidate_preview()
        yield GuestMapState.load_preview

    @rx.event
    def clear_category_choices(self):
        self.category_filters = []
        self._invalidate_preview()
        yield GuestMapState.load_preview

    @rx.event
    def set_reward_filter(self, value: str):
        if self.browse_mode == "get" or value not in {
            item["value"] for item in GUEST_REWARDS
        }:
            return
        self.reward_filter = value
        self._invalidate_preview()
        yield GuestMapState.load_preview

    @rx.event
    def clear_filters(self):
        self.search_query = ""
        self.category_filters = []
        self.category_list_open = False
        self.reward_filter = "all"
        self.view_mode = "map"
        self._invalidate_preview()
        yield GuestMapState.load_preview

    @rx.event
    def go_to_map(self):
        self.open_join_prompt()

    @rx.event
    def select_give(self):
        yield GuestMapState.set_browse_mode("give")

    @rx.event
    def open_get_wall(self):
        self.wall_open = True
        self.wall_reason = (
            "Browsing helpers is members-only: helper profiles, photos and "
            "contact details are never shown to guests. Sign up and confirm "
            "your email to meet neighbours who offer a hand."
        )

    @rx.event
    def open_join_prompt(self):
        """Sign-in / join prompt used by every guest-gated action."""
        self.search_expanded = False
        self.wall_open = True
        self.wall_reason = "Browse job titles as a visitor. Join or sign in to unlock job details."

    @rx.event
    def gate_distance_filter(self, value: str):
        yield rx.call_script(
            "const slider = document.getElementById('gah-guest-distance'); if (slider) slider.value = '0';"
        )
        if value != "0":
            yield GuestMapState.open_join_prompt

    @rx.event
    def open_wall(self, reason: str):
        self.wall_open = True
        self.wall_reason = reason

    @rx.event
    def open_wall_for_marker(self, marker_id: str):
        self.preview_title = ""
        self.preview_description = ""
        self.open_join_prompt()
        if self.browse_mode == "get":
            return
        for job in self.jobs:
            if job["code"] == marker_id:
                self.preview_title = job["title"]
                self.preview_description = job["description"][:100]
                self.wall_reason = "Sign up or login to Search for jobs, people or places around the world"
                break

    @rx.event
    def open_search_wall(self):
        self.search_expanded = False
        self.wall_open = True
        self.wall_reason = (
            "Sign up or login to Search for jobs, people or places around "
            "the world"
        )

    @rx.event
    def submit_member_search(self, form_data: dict[str, Any]):
        typed = str(
            form_data.get("member_search")
            or form_data.get("member_search_desktop")
            or ""
        ).strip()
        if typed:
            self.search_query = typed
        self.open_search_wall()

    @rx.event
    def close_wall(self):
        self.wall_open = False
        self.wall_reason = ""
        self.preview_title = ""
        self.preview_description = ""

    @rx.event(background=True)
    async def load_preview(self):
        """Discard stale searches and recheck identity before publishing."""
        from app.states.auth_state import AuthState

        async with self:
            auth = await self.get_state(AuthState)
            self._preview_generation += 1
            generation = self._preview_generation
            if auth.subscriber_id.isdigit() and auth.email != "":
                self.jobs = []
                self.helpers = []
                self.open_total = 0
                self.is_loading = False
                self.loaded = True
                self.load_message = ""
                return
            mode = self.browse_mode
            query = self.search_query
            categories = list(self.category_filters)
            reward = self.reward_filter
            self.is_loading = True
            self.load_message = ""

        jobs: list[GuestJob] = []
        helpers: list[GuestHelper] = []
        message = ""
        try:
            jobs, helpers = await fetch_guest_preview(
                mode, query, categories, reward
            )
        except (OperationalError, InterfaceError, RuntimeError):
            logging.exception("Guest map preview temporarily unavailable")
            message = "Map preview is temporarily unavailable."
        except Exception:
            logging.exception("Guest map preview could not be loaded")
            message = "Map preview could not be loaded."

        async with self:
            auth = await self.get_state(AuthState)
            if auth.subscriber_id.isdigit() and auth.email != "":
                self.jobs = []
                self.helpers = []
                self.open_total = 0
                self.is_loading = False
                self.loaded = True
                self.load_message = ""
                return
            if generation != self._preview_generation:
                return
            self.jobs = jobs
            self.helpers = helpers
            self.open_total = len(jobs) + len(helpers)
            self.is_loading = False
            self.loaded = True
            self.load_message = message
        from app.states.help_share_state import HelpShareState

        yield HelpShareState.resolve
