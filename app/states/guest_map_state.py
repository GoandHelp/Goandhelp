"""Privacy-safe guest previews with approximate request locations."""

import asyncio
import hashlib
import logging
from typing import Any, TypedDict

import reflex as rx
from sqlalchemy import text
from sqlalchemy.exc import InterfaceError, OperationalError

from app.components.openfreemap import MapMarker
from app.location_privacy import post_guest_approximate

PAGE_SIZE = 100
MAX_DB_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 0.25


class GuestJob(TypedDict):
    code: str
    title: str
    description: str
    lng: float
    lat: float


GuestRow = tuple[int, str, str, float | None, float | None]


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


class GuestMapState(rx.State):
    """Guest-only view model. Holds no member, poster or helper data."""

    jobs: list[GuestJob] = []
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
    # "map" or "list" — guests may switch freely between both safe views.
    view_mode: str = "map"
    # Guests can only browse jobs ("give"); "get" is members-only.
    browse_mode: str = "give"
    map_center: list[float] = [10.0, 46.5]
    map_zoom: float = 3.6

    @rx.var
    def has_jobs(self) -> bool:
        return len(self.jobs) > 0

    @rx.var
    def is_list_view(self) -> bool:
        return self.view_mode == "list"

    @rx.var
    def map_markers(self) -> list[MapMarker]:
        """Only server-obfuscated public points reach the map."""
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

    @rx.event
    def set_view_mode(self, mode: str):
        self.view_mode = "list" if mode == "list" else "map"

    @rx.event
    def expand_search(self):
        self.search_expanded = True

    @rx.event
    def collapse_search(self):
        self.search_expanded = False

    @rx.event
    def set_search_query(self, value: str):
        self.search_query = value
        self.search_expanded = True

    @rx.event
    def go_to_map(self):
        self.open_join_prompt()

    @rx.event
    def select_give(self):
        self.browse_mode = "give"

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
    def open_wall(self, reason: str):
        self.wall_open = True
        self.wall_reason = reason

    @rx.event
    def open_wall_for_marker(self, marker_id: str):
        self.open_join_prompt()
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
        """Load anonymous counts and rough marker positions for guests only."""
        from app.states.auth_state import AuthState

        async with self:
            auth = await self.get_state(AuthState)
            signed_in = auth.subscriber_id.isdigit() and auth.email != ""
            if signed_in:
                # Members use the full discovery board; keep guest state empty.
                self.jobs = []
                self.open_total = 0
                self.is_loading = False
                self.loaded = True
                self.load_message = ""
                return
            self.is_loading = True
            self.load_message = ""

        rows: list[GuestRow] = []
        for attempt in range(1, MAX_DB_ATTEMPTS + 1):
            try:
                # A fresh session per attempt so a dead pooled connection is dropped.
                async with rx.asession() as asession:
                    rows = []
                    before_id = 9223372036854775807
                    while True:
                        page = (
                            await asession.execute(
                                text("""
                                SELECT p.id, p.title, LEFT(COALESCE(p.description, ''), 100), p.latitude, p.longitude
                                FROM skillkind_help_post p
                                WHERE p.status = 'open' AND p.id < :before_id
                                  AND (SELECT COUNT(*) FROM skillkind_job_application ca
                                       WHERE ca.post_id = p.id AND ca.status = 'accepted')
                                      < GREATEST(COALESCE(p.helpers_needed, 1), 1)
                                  AND (p.expires_at IS NULL OR p.expires_at > now())
                                ORDER BY p.id DESC
                                LIMIT :page_size
                            """),
                                {
                                    "before_id": before_id,
                                    "page_size": PAGE_SIZE,
                                },
                            )
                        ).all()
                        rows.extend(
                            (
                                int(r[0]),
                                str(r[1] or ""),
                                str(r[2] or ""),
                                r[3],
                                r[4],
                            )
                            for r in page
                        )
                        break
                break
            except (OperationalError, InterfaceError) as e:
                if attempt < MAX_DB_ATTEMPTS:
                    logging.warning(
                        f"Transient database error loading guest map preview "
                        f"(attempt {attempt}/{MAX_DB_ATTEMPTS}): {e}"
                    )
                    await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)
                    continue
                logging.exception(
                    f"Guest map preview failed after {MAX_DB_ATTEMPTS} attempts: {e}"
                )
                async with self:
                    self.jobs = []
                    self.open_total = 0
                    self.is_loading = False
                    self.loaded = True
                    self.load_message = (
                        "Map preview is temporarily unavailable."
                    )
                return
            except Exception as e:  # noqa: BLE001
                logging.exception(f"Error loading guest map preview: {e}")
                unavailable = any(
                    phrase in str(e).lower()
                    for phrase in (
                        "database is not initialized",
                        "database not initialized",
                        "database is unavailable",
                        "database unavailable",
                        "temporarily unavailable",
                    )
                )
                if unavailable and attempt < MAX_DB_ATTEMPTS:
                    logging.warning(
                        f"Transient startup database error loading guest map preview "
                        f"(attempt {attempt}/{MAX_DB_ATTEMPTS})"
                    )
                    await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)
                    continue
                async with self:
                    self.jobs = []
                    self.open_total = 0
                    self.is_loading = False
                    self.loaded = True
                    self.load_message = (
                        "Map preview is temporarily unavailable."
                        if unavailable
                        else "Map preview could not be loaded."
                    )
                return

        jobs: list[GuestJob] = []
        for row in rows:
            job = await asyncio.to_thread(_public_job, row)
            if job is not None:
                jobs.append(job)

        async with self:
            self.jobs = jobs
            self.open_total = len(jobs)
            self.is_loading = False
            self.loaded = True
            self.load_message = ""
        from app.states.help_share_state import HelpShareState

        yield HelpShareState.resolve
