"""Member-only world search across Jobs, People and Places.

Guests never reach this state: every query requires a signed-in subscriber, and
the returned rows carry only compact, display-safe details.
"""

import logging
from typing import Any, TypedDict

import reflex as rx
from sqlalchemy import text

from app.skill_categories import (
    category_labels,
    post_categories,
    split_categories,
)
from app.states.auth_state import AuthState

GROUP_LIMIT = 5
MIN_QUERY = 2


class SearchItem(TypedDict):
    kind: str
    id: str
    title: str
    subtitle: str


class SearchGroup(TypedDict):
    kind: str
    label: str
    icon: str
    total: int
    items: list[SearchItem]


class WorldSearchState(rx.State):
    query: str = ""
    expanded: bool = False
    is_searching: bool = False
    searched: bool = False
    groups: list[SearchGroup] = []

    @rx.var
    def has_results(self) -> bool:
        return len(self.groups) > 0

    @rx.var
    def result_summary(self) -> str:
        total = sum(group["total"] for group in self.groups)
        if total == 1:
            return "1 match"
        return f"{total} matches"

    @rx.var
    def show_panel(self) -> bool:
        return self.expanded and len(self.query.strip()) > 0

    @rx.var
    def show_empty(self) -> bool:
        return (
            self.searched
            and not self.is_searching
            and len(self.groups) == 0
            and len(self.query.strip()) >= MIN_QUERY
        )

    @rx.event
    def expand(self):
        self.expanded = True

    @rx.event
    def collapse(self):
        self.expanded = False

    @rx.event
    def set_query(self, value: str):
        self.query = value
        self.expanded = True
        if len(value.strip()) < MIN_QUERY:
            self.groups = []
            self.searched = False
            return
        return WorldSearchState.run_search

    @rx.event
    def submit(self, form_data: dict[str, Any]):
        typed = str(form_data.get("world_search", "") or "").strip()
        if typed:
            self.query = typed
        self.expanded = False
        if len(self.query.strip()) < MIN_QUERY:
            self.groups = []
            self.searched = False
            return
        return WorldSearchState.run_search

    @rx.event(background=True)
    async def run_search(self):
        async with self:
            raw = self.query.strip()
            sid = (await self.get_state(AuthState)).subscriber_id
            if len(raw) < MIN_QUERY or not sid.isdigit():
                self.groups = []
                self.searched = len(raw) >= MIN_QUERY
                self.is_searching = False
                return
            self.is_searching = True

        normalized = raw.lower()
        params: dict[str, str | int] = {
            "q": normalized,
            "like": f"%{normalized}%",
            "prefix": f"{normalized}%",
            "sid": int(sid),
            "limit": GROUP_LIMIT,
        }

        try:
            async with rx.asession() as asession:
                job_rows = (
                    await asession.execute(
                        text(
                            """
                            SELECT p.id, p.title,
                                   COALESCE(p.city, ''), COALESCE(p.country, ''),
                                   COALESCE(p.category, ''),
                                   COUNT(*) OVER () AS total,
                                   COALESCE(p.category_tags, '')
                            FROM skillkind_help_post p
                            WHERE p.status = 'open'
                              AND (SELECT COUNT(*) FROM skillkind_job_application ca
                                   WHERE ca.post_id = p.id AND ca.status = 'accepted')
                                  < GREATEST(COALESCE(p.helpers_needed, 1), 1)
                              AND (p.expires_at IS NULL
                                   OR p.expires_at > now())
                              AND NOT EXISTS (
                                  SELECT 1 FROM skillkind_member_block mb
                                  WHERE mb.blocker_id = :sid
                                    AND mb.blocked_id = p.author_id
                              )
                              AND (LOWER(p.title) LIKE :like
                                   OR LOWER(COALESCE(p.description, '')) LIKE :like
                                   OR LOWER(COALESCE(p.category, '')) LIKE :like
                                   OR LOWER(COALESCE(p.category_tags, '')) LIKE :like
                                   OR LOWER(COALESCE(p.knowledge_skills, '')) LIKE :like
                                   OR LOWER(COALESCE(p.city, '')) LIKE :like
                                   OR LOWER(COALESCE(p.country, '')) LIKE :like)
                            ORDER BY
                                CASE WHEN LOWER(p.title) = :q THEN 0
                                     WHEN LOWER(p.title) LIKE :prefix THEN 1
                                     ELSE 2 END,
                                p.created_at DESC
                            LIMIT :limit
                            """
                        ),
                        params,
                    )
                ).all()
                people_rows = (
                    await asession.execute(
                        text(
                            """
                            SELECT s.id, s.display_name,
                                   COALESCE(pr.username, ''),
                                   COALESCE(pr.headline, ''),
                                   COALESCE(pr.current_city, ''),
                                   COUNT(*) OVER () AS total,
                                   COALESCE(pr.skills, ''),
                                   COALESCE(pr.preferred_categories, '')
                            FROM skillkind_subscriber s
                            LEFT JOIN skillkind_profile pr
                                   ON pr.subscriber_id = s.id
                            WHERE s.is_active = TRUE
                              AND s.id <> :sid
                              AND COALESCE(pr.show_location, FALSE) = TRUE
                              AND pr.latitude IS NOT NULL
                              AND pr.longitude IS NOT NULL
                              AND (LOWER(COALESCE(s.display_name, '')) LIKE :like
                                   OR LOWER(COALESCE(pr.username, '')) LIKE :like
                                   OR LOWER(COALESCE(pr.current_city, '')) LIKE :like
                                   OR LOWER(COALESCE(pr.home_city, '')) LIKE :like
                                   OR LOWER(COALESCE(pr.home_country, '')) LIKE :like
                                   OR LOWER(COALESCE(pr.nationality, '')) LIKE :like
                                   OR LOWER(COALESCE(pr.headline, '')) LIKE :like
                                   OR LOWER(COALESCE(pr.skills, '')) LIKE :like
                                   OR LOWER(COALESCE(pr.preferred_categories, ''))
                                      LIKE :like)
                            ORDER BY
                                CASE WHEN LOWER(COALESCE(s.display_name, '')) = :q
                                          OR LOWER(COALESCE(pr.username, '')) = :q THEN 0
                                     WHEN LOWER(COALESCE(s.display_name, '')) LIKE :prefix
                                          OR LOWER(COALESCE(pr.username, '')) LIKE :prefix THEN 1
                                     ELSE 2 END,
                                COALESCE(pr.kindness_points, 0) DESC
                            LIMIT :limit
                            """
                        ),
                        params,
                    )
                ).all()
                place_rows = (
                    await asession.execute(
                        text(
                            """
                            WITH places AS (
                                SELECT city AS name FROM skillkind_help_post
                                WHERE status = 'open' AND COALESCE(TRIM(city), '') <> ''
                                UNION ALL
                                SELECT country FROM skillkind_help_post
                                WHERE status = 'open' AND COALESCE(TRIM(country), '') <> ''
                                UNION ALL
                                SELECT current_city FROM skillkind_profile
                                WHERE COALESCE(TRIM(current_city), '') <> ''
                                UNION ALL
                                SELECT home_city FROM skillkind_profile
                                WHERE COALESCE(TRIM(home_city), '') <> ''
                                UNION ALL
                                SELECT home_country FROM skillkind_profile
                                WHERE COALESCE(TRIM(home_country), '') <> ''
                            ), grouped AS (
                                SELECT LOWER(TRIM(name)) AS place_key,
                                       MIN(TRIM(name)) AS label,
                                       COUNT(*) AS mentions
                                FROM places
                                WHERE LOWER(TRIM(name)) LIKE :like
                                GROUP BY LOWER(TRIM(name))
                            )
                            SELECT label, place_key, mentions,
                                   COUNT(*) OVER () AS total
                            FROM grouped
                            ORDER BY
                                CASE WHEN place_key = :q THEN 0
                                     WHEN place_key LIKE :prefix THEN 1
                                     ELSE 2 END,
                                mentions DESC
                            LIMIT :limit
                            """
                        ),
                        params,
                    )
                ).all()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"World search failed: {e}")
            async with self:
                self.groups = []
                self.searched = True
                self.is_searching = False
            return

        job_items: list[SearchItem] = [
            {
                "kind": "job",
                "id": str(int(row[0])),
                "title": str(row[1] or "Help needed"),
                "subtitle": " · ".join(
                    [
                        part
                        for part in (
                            ", ".join(
                                category_labels(
                                    post_categories(
                                        str(row[6] or ""), str(row[4] or "")
                                    )
                                )
                            ),
                            ", ".join(
                                p for p in (str(row[2]), str(row[3])) if p
                            ),
                        )
                        if part
                    ]
                ),
            }
            for row in job_rows
        ]
        people_items: list[SearchItem] = [
            {
                "kind": "person",
                "id": str(int(row[0])),
                "title": str(row[1] or "A neighbour"),
                "subtitle": " · ".join(
                    [
                        part
                        for part in (
                            f"@{row[2]}" if str(row[2] or "") else "",
                            str(row[4] or ""),
                            str(row[3] or ""),
                            ", ".join(
                                category_labels(
                                    split_categories(str(row[7] or ""))
                                )
                            ),
                            str(row[6] or ""),
                        )
                        if part
                    ]
                )[:90],
            }
            for row in people_rows
        ]
        place_items: list[SearchItem] = [
            {
                "kind": "place",
                "id": str(row[0] or ""),
                "title": str(row[0] or ""),
                "subtitle": f"{int(row[2] or 0)} mentions on the map",
            }
            for row in place_rows
        ]

        job_total = int(job_rows[0][5]) if job_rows else 0
        people_total = int(people_rows[0][5]) if people_rows else 0
        place_total = int(place_rows[0][3]) if place_rows else 0
        exact_place = any(
            str(row[1] or "").lower() == normalized for row in place_rows
        )

        built: list[tuple[int, SearchGroup]] = []
        if job_items:
            built.append(
                (
                    job_total,
                    {
                        "kind": "job",
                        "label": "Jobs",
                        "icon": "hand-helping",
                        "total": job_total,
                        "items": job_items,
                    },
                )
            )
        if people_items:
            built.append(
                (
                    people_total,
                    {
                        "kind": "person",
                        "label": "People",
                        "icon": "users-round",
                        "total": people_total,
                        "items": people_items,
                    },
                )
            )
        if place_items:
            built.append(
                (
                    place_total,
                    {
                        "kind": "place",
                        "label": "Places",
                        "icon": "map-pin",
                        "total": place_total,
                        "items": place_items,
                    },
                )
            )
        built.sort(key=lambda pair: -pair[0])
        ordered = [group for _, group in built]
        if exact_place:
            ordered.sort(key=lambda group: 0 if group["kind"] == "place" else 1)

        async with self:
            self.groups = ordered
            self.searched = True
            self.is_searching = False

    @rx.event
    def choose(self, kind: str, identifier: str):
        """Collapse the search and move the discovery map to the choice."""
        from app.states.discovery_state import DiscoveryState

        self.expanded = False
        if kind == "job" and identifier.isdigit():
            return DiscoveryState.focus_post(int(identifier))
        if kind == "person" and identifier.isdigit():
            return DiscoveryState.focus_helper(int(identifier))
        if kind == "place" and identifier.strip():
            return DiscoveryState.focus_place(identifier.strip())
        return None
