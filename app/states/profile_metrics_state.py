"""Premium request-success metrics shown inside the member Profile screen.

Everything here is read-only analytics over real rows: `skillkind_help_post`
(including the authoritative `view_count` column), `skillkind_job_application`,
`skillkind_category_search_event`, `skillkind_subscriber.date_of_birth` and
`skillkind_profile.nationality`.

Every query is gated server-side by the signed-in subscriber id AND by the
authoritative `db_is_premium` check, so a free member can never receive premium
analytics even if the client state is tampered with. Exact coordinates are used
only inside SQL distance maths and are never returned to the frontend.
"""

import logging
import re
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.filter_categories import (
    FILTER_CATEGORIES,
    FilterCategory,
    category_label,
    expand_category_tokens,
)
from app.membership import ACTIVE_POST_CLAUSE, db_is_premium
from app.models import TASK_CATEGORIES
from app.states.auth_state import AuthState

MAX_RADIUS_KM = 2000
MIN_RADIUS_KM = 0
DEFAULT_RADIUS_KM = 200
EARTH_RADIUS_KM = 6371.0

WORLDWIDE_NOTE = (
    "Ranked worldwide — add a profile location to rank what is happening "
    "around you."
)


class RequestViewRow(TypedDict):
    id: int
    title: str
    status: str
    status_label: str
    views: int
    competitors: int


class RankRow(TypedDict):
    label: str
    count: int
    width: str


STATUS_LABELS: dict[str, str] = {
    "open": "Open",
    "matched": "Matched",
    "completed": "Completed",
    "cancelled": "Cancelled",
}

# Function words, pronouns, conjunctions, prepositions, auxiliaries and other
# non-content tokens. Only likely nouns, verbs and adjectives survive.
STOP_WORDS: frozenset[str] = frozenset(
    """
    the and for you your yours our ours their theirs his her hers its
    with without within into onto from that this these those there here
    what which who whom whose when where why how all any both each few more
    most other some such only own same than too very can will just should now
    are was were been being have has had having does did doing done
    but not nor yet also because since while about above after again against
    below between during before beyond down under over off out then they them
    she him himself herself myself itself ourselves themselves yourself
    would could shall might must may need needs needed want wants wanted
    get gets got getting let lets please thanks thank hello hey
    someone somebody anyone anybody everyone everybody nothing something
    anything everything one two three four five six seven eight nine ten
    day days week weeks month months year years hour hours time times
    lot lots bit bits thing things way ways etc okay yes nope
    ist der die das und fur por para con una uno les des pour dans
    """.split()
)

# Very short or generic tokens that add no ranking value.
EXTRA_STOP_WORDS: frozenset[str] = frozenset(
    {"help", "helper", "helpers", "helping", "looking", "look", "hand"}
)

WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z'\-]{2,}")


def _clamp_radius(value: str | int | float) -> int:
    try:
        parsed = int(round(float(value)))
    except (TypeError, ValueError):
        parsed = DEFAULT_RADIUS_KM
    return max(MIN_RADIUS_KM, min(MAX_RADIUS_KM, parsed))


def _distance_clause(alias: str, prefix: str) -> str:
    """Haversine distance filter (km) against stored lat/long columns."""
    lat = f"{alias}.latitude::double precision"
    lon = f"{alias}.longitude::double precision"
    return (
        f" AND {alias}.latitude IS NOT NULL AND {alias}.longitude IS NOT NULL"
        f" AND (2 * {EARTH_RADIUS_KM} * asin(least(1, sqrt("
        f"power(sin(radians(:{prefix}_lat - {lat}) / 2), 2)"
        f" + cos(radians(:{prefix}_lat)) * cos(radians({lat}))"
        f" * power(sin(radians(:{prefix}_lon - {lon}) / 2), 2)"
        f")))) <= :{prefix}_radius"
    )


def _rank_rows(pairs: list[tuple[str, int]]) -> list[RankRow]:
    if not pairs:
        return []
    top = max(count for _, count in pairs) or 1
    rows: list[RankRow] = []
    for label, count in pairs:
        share = max(8, int(round(count * 100 / top)))
        rows.append({"label": label, "count": int(count), "width": f"{share}%"})
    return rows


def _meaningful_words(blobs: list[str]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for blob in blobs:
        for raw in WORD_PATTERN.findall(blob or ""):
            word = raw.lower().strip("'-")
            if len(word) < 3 or word.endswith("ly") or word.isdigit():
                continue
            if word in STOP_WORDS or word in EXTRA_STOP_WORDS:
                continue
            counts[word] = counts.get(word, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    repeated = [pair for pair in ranked if pair[1] > 1]
    return (repeated or ranked)[:10]


class ProfileMetricsState(rx.State):
    """Server-gated Premium metrics view model."""

    # Authoritative, set only from the database.
    is_premium: bool = False
    loaded: bool = False
    is_loading: bool = False
    error: str = ""

    has_location: bool = False

    competitor_radius_km: int = DEFAULT_RADIUS_KM
    search_radius_km: int = DEFAULT_RADIUS_KM
    request_radius_km: int = DEFAULT_RADIUS_KM

    selected_category: str = TASK_CATEGORIES[0]
    category_options: list[FilterCategory] = FILTER_CATEGORIES

    request_rows: list[RequestViewRow] = []
    searched_categories: list[RankRow] = []
    request_categories: list[RankRow] = []
    keywords: list[RankRow] = []

    helper_age_label: str = ""
    helper_age_sample: int = 0
    helper_nationality: str = ""
    helper_nationality_count: int = 0
    helper_nationality_sample: int = 0
    helpee_age_label: str = ""
    helpee_age_sample: int = 0
    helpee_nationality: str = ""
    helpee_nationality_count: int = 0
    helpee_nationality_sample: int = 0

    # ------------------------------------------------------------------
    # Presentation helpers
    # ------------------------------------------------------------------

    @rx.var
    def selected_category_label(self) -> str:
        return category_label(self.selected_category)

    @rx.var
    def location_note(self) -> str:
        if self.has_location:
            return (
                "Distances are measured from your saved profile location. "
                "Your exact point is never shown here or to anyone else."
            )
        return WORLDWIDE_NOTE

    @rx.var
    def competitor_scope_label(self) -> str:
        return self._scope_label(self.competitor_radius_km)

    @rx.var
    def search_scope_label(self) -> str:
        return self._scope_label(self.search_radius_km)

    @rx.var
    def request_scope_label(self) -> str:
        return self._scope_label(self.request_radius_km)

    @rx.var
    def helper_age_note(self) -> str:
        if not self.helper_age_label:
            return "No helper birthdays shared for this category yet."
        return f"Average age of {self.helper_age_sample} helpers"

    @rx.var
    def helpee_age_note(self) -> str:
        if not self.helpee_age_label:
            return "No helpee birthdays shared for this category yet."
        return f"Average age of {self.helpee_age_sample} helpees"

    @rx.var
    def helper_nationality_note(self) -> str:
        if not self.helper_nationality:
            return "No helper nationality recorded for this category yet."
        return (
            f"Most common of {self.helper_nationality_sample} helpers who "
            f"shared one — {self.helper_nationality_count} members."
        )

    @rx.var
    def helpee_nationality_note(self) -> str:
        if not self.helpee_nationality:
            return "No helpee nationality recorded for this category yet."
        return (
            f"Most common of {self.helpee_nationality_sample} helpees who "
            f"shared one — {self.helpee_nationality_count} members."
        )

    def _scope_label(self, radius: int) -> str:
        if not self.has_location or radius <= 0:
            return "Worldwide"
        return f"Within {radius} km"

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def _reset(self):
        self.is_premium = False
        self.loaded = False
        self.is_loading = False
        self.error = ""
        self.has_location = False
        self.request_rows = []
        self.searched_categories = []
        self.request_categories = []
        self.keywords = []
        self.helper_age_label = ""
        self.helper_age_sample = 0
        self.helper_nationality = ""
        self.helper_nationality_count = 0
        self.helper_nationality_sample = 0
        self.helpee_age_label = ""
        self.helpee_age_sample = 0
        self.helpee_nationality = ""
        self.helpee_nationality_count = 0
        self.helpee_nationality_sample = 0

    @rx.event
    def clear_metrics(self):
        """Drop every sensitive figure (sign out / profile clear)."""
        self._reset()
        self.competitor_radius_km = DEFAULT_RADIUS_KM
        self.search_radius_km = DEFAULT_RADIUS_KM
        self.request_radius_km = DEFAULT_RADIUS_KM
        self.selected_category = TASK_CATEGORIES[0]

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------

    @rx.event
    def set_competitor_radius(self, value: float):
        self.competitor_radius_km = _clamp_radius(value)
        return ProfileMetricsState.load_request_metrics

    @rx.event
    def set_search_radius(self, value: float):
        self.search_radius_km = _clamp_radius(value)
        return ProfileMetricsState.load_searched_categories

    @rx.event
    def set_request_radius(self, value: float):
        self.request_radius_km = _clamp_radius(value)
        return ProfileMetricsState.load_request_categories

    @rx.event
    def set_selected_category(self, value: str):
        if value in TASK_CATEGORIES:
            self.selected_category = value
        return ProfileMetricsState.load_category_metrics

    # ------------------------------------------------------------------
    # Server-side gate
    # ------------------------------------------------------------------

    async def _gate(self) -> tuple[int, bool]:
        """(subscriber_id, premium) read straight from the database."""
        async with self:
            raw = (await self.get_state(AuthState)).subscriber_id
        if not raw.isdigit():
            async with self:
                self._reset()
            return 0, False
        sid = int(raw)
        async with rx.asession() as asession:
            premium = await db_is_premium(asession, sid)
            point = (
                await asession.execute(
                    text(
                        """
                        SELECT latitude, longitude
                        FROM skillkind_profile
                        WHERE subscriber_id = :sid
                        """
                    ),
                    {"sid": sid},
                )
            ).first()
        has_point = bool(
            point is not None and point[0] is not None and point[1] is not None
        )
        async with self:
            if not premium:
                self._reset()
            else:
                self.is_premium = True
                self.has_location = has_point
        return sid, premium

    async def _own_point(self, sid: int) -> tuple[float, float] | None:
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT latitude, longitude
                        FROM skillkind_profile
                        WHERE subscriber_id = :sid
                          AND latitude IS NOT NULL
                          AND longitude IS NOT NULL
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).first()
        if row is None:
            return None
        return float(row[0]), float(row[1])

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    @rx.event(background=True)
    async def load_metrics(self):
        """Lazy full load, used when the Profile screen opens."""
        sid, premium = await self._gate()
        if not sid or not premium:
            return
        async with self:
            self.is_loading = True
            self.error = ""
        yield ProfileMetricsState.load_request_metrics
        yield ProfileMetricsState.load_searched_categories
        yield ProfileMetricsState.load_request_categories
        yield ProfileMetricsState.load_category_metrics
        async with self:
            self.is_loading = False
            self.loaded = True

    @rx.event(background=True)
    async def load_request_metrics(self):
        """A. Views on my requests. B. Competing active requests nearby."""
        sid, premium = await self._gate()
        if not sid or not premium:
            return
        async with self:
            radius = self.competitor_radius_km
        point = await self._own_point(sid)
        params: dict[str, str | int | float] = {"sid": sid}
        clause = ""
        if point is not None and radius > 0:
            clause = _distance_clause("p", "comp")
            params["comp_lat"] = point[0]
            params["comp_lon"] = point[1]
            params["comp_radius"] = radius
        query = text(
            f"""
            WITH mine AS (
                SELECT p.id, p.title, p.status,
                       COALESCE(p.view_count, 0) AS views,
                       p.created_at,
                       CASE WHEN btrim(COALESCE(p.category_tags, '')) <> ''
                            THEN string_to_array(
                                lower(replace(p.category_tags, ' ', '')), ',')
                            ELSE ARRAY[lower(COALESCE(p.category, 'other'))]
                       END AS tokens
                FROM skillkind_help_post p
                WHERE p.author_id = :sid
                ORDER BY p.created_at DESC
                LIMIT 10
            ),
            others AS (
                SELECT p.id,
                       CASE WHEN btrim(COALESCE(p.category_tags, '')) <> ''
                            THEN string_to_array(
                                lower(replace(p.category_tags, ' ', '')), ',')
                            ELSE ARRAY[lower(COALESCE(p.category, 'other'))]
                       END AS tokens
                FROM skillkind_help_post p
                WHERE p.author_id <> :sid AND p.status = 'open'
                  AND {ACTIVE_POST_CLAUSE}{clause}
            )
            SELECT m.id, m.title, m.status, m.views,
                   COUNT(DISTINCT o.id) AS rivals
            FROM mine m
            LEFT JOIN others o ON o.tokens && m.tokens
            GROUP BY m.id, m.title, m.status, m.views, m.created_at
            ORDER BY m.created_at DESC
            """
        )
        try:
            async with rx.asession() as asession:
                rows = (await asession.execute(query, params)).all()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Could not load request metrics: {e}")
            async with self:
                self.error = "We couldn't load your request metrics just now."
            return
        async with self:
            self.request_rows = [
                {
                    "id": int(r[0]),
                    "title": str(r[1] or "Untitled request"),
                    "status": str(r[2] or "open"),
                    "status_label": STATUS_LABELS.get(
                        str(r[2] or "open"), str(r[2] or "open").title()
                    ),
                    "views": int(r[3] or 0),
                    "competitors": int(r[4] or 0),
                }
                for r in rows
            ]
            self.error = ""

    @rx.event(background=True)
    async def load_searched_categories(self):
        """C. Top searched categories from real category-search events."""
        sid, premium = await self._gate()
        if not sid or not premium:
            return
        async with self:
            radius = self.search_radius_km
        point = await self._own_point(sid)
        params: dict[str, str | int | float] = {}
        clause = ""
        if point is not None and radius > 0:
            clause = _distance_clause("e", "srch")
            params["srch_lat"] = point[0]
            params["srch_lon"] = point[1]
            params["srch_radius"] = radius
        query = text(
            f"""
            SELECT lower(btrim(e.category)) AS token, COUNT(*) AS hits
            FROM skillkind_category_search_event e
            WHERE btrim(COALESCE(e.category, '')) <> ''{clause}
            GROUP BY lower(btrim(e.category))
            ORDER BY hits DESC, token
            LIMIT 10
            """
        )
        try:
            async with rx.asession() as asession:
                rows = (await asession.execute(query, params)).all()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Could not load searched categories: {e}")
            async with self:
                self.error = "We couldn't load the search rankings just now."
            return
        async with self:
            self.searched_categories = _rank_rows(
                [(category_label(str(r[0])), int(r[1] or 0)) for r in rows]
            )

    @rx.event(background=True)
    async def load_request_categories(self):
        """D. Top help-request categories from real posts."""
        sid, premium = await self._gate()
        if not sid or not premium:
            return
        async with self:
            radius = self.request_radius_km
        point = await self._own_point(sid)
        params: dict[str, str | int | float] = {}
        clause = ""
        if point is not None and radius > 0:
            clause = _distance_clause("p", "req")
            params["req_lat"] = point[0]
            params["req_lon"] = point[1]
            params["req_radius"] = radius
        query = text(
            f"""
            WITH expanded AS (
                SELECT lower(btrim(tag)) AS token
                FROM skillkind_help_post p
                CROSS JOIN LATERAL unnest(
                    CASE WHEN btrim(COALESCE(p.category_tags, '')) <> ''
                         THEN string_to_array(p.category_tags, ',')
                         ELSE ARRAY[COALESCE(p.category, 'other')]
                    END
                ) AS tag
                WHERE 1 = 1{clause}
            )
            SELECT token, COUNT(*) AS hits
            FROM expanded
            WHERE token <> ''
            GROUP BY token
            ORDER BY hits DESC, token
            LIMIT 10
            """
        )
        try:
            async with rx.asession() as asession:
                rows = (await asession.execute(query, params)).all()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Could not load request categories: {e}")
            async with self:
                self.error = "We couldn't load the category rankings just now."
            return
        async with self:
            self.request_categories = _rank_rows(
                [(category_label(str(r[0])), int(r[1] or 0)) for r in rows]
            )

    @rx.event(background=True)
    async def load_category_metrics(self):
        """E-I. Successful keywords plus helper/helpee age and nationality."""
        sid, premium = await self._gate()
        if not sid or not premium:
            return
        async with self:
            category = self.selected_category
        tokens = expand_category_tokens([category]) or [category]
        params: dict[str, list[str]] = {"tokens": tokens}
        match_clause = (
            "(lower(COALESCE(p.category, '')) = ANY(CAST(:tokens AS text[]))"
            " OR string_to_array("
            "lower(replace(COALESCE(p.category_tags, ''), ' ', '')), ',')"
            " && CAST(:tokens AS text[]))"
        )
        keyword_query = text(
            f"""
            SELECT p.title, COALESCE(p.description, '')
            FROM skillkind_help_post p
            WHERE {match_clause}
              AND (
                p.status IN ('matched', 'completed')
                OR EXISTS (
                    SELECT 1 FROM skillkind_job_application a
                    WHERE a.post_id = p.id AND a.status = 'accepted'
                )
              )
            ORDER BY p.created_at DESC
            LIMIT 300
            """
        )
        demographics_query = text(
            f"""
            WITH cat_posts AS (
                SELECT p.id, p.author_id
                FROM skillkind_help_post p
                WHERE {match_clause}
            ),
            roles AS (
                SELECT 'helper' AS role, a.helper_id AS sid
                FROM skillkind_job_application a
                JOIN cat_posts c ON c.id = a.post_id
                GROUP BY a.helper_id
                UNION ALL
                SELECT 'helpee' AS role, c.author_id AS sid
                FROM cat_posts c
                GROUP BY c.author_id
            ),
            ages AS (
                SELECT r.role,
                       AVG(EXTRACT(YEAR FROM age(s.date_of_birth))) AS avg_age,
                       COUNT(*) AS sample
                FROM roles r
                JOIN skillkind_subscriber s ON s.id = r.sid
                WHERE s.date_of_birth IS NOT NULL
                GROUP BY r.role
            ),
            nats AS (
                SELECT r.role, btrim(pr.nationality) AS nat, COUNT(*) AS c
                FROM roles r
                JOIN skillkind_profile pr ON pr.subscriber_id = r.sid
                WHERE btrim(COALESCE(pr.nationality, '')) <> ''
                GROUP BY r.role, btrim(pr.nationality)
            ),
            ranked AS (
                SELECT role, nat, c,
                       ROW_NUMBER() OVER (
                           PARTITION BY role ORDER BY c DESC, nat
                       ) AS rn,
                       SUM(c) OVER (PARTITION BY role) AS total
                FROM nats
            )
            SELECT COALESCE(a.role, r.role) AS role,
                   a.avg_age, a.sample, r.nat, r.c, r.total
            FROM ages a
            FULL OUTER JOIN ranked r ON r.role = a.role AND r.rn = 1
            WHERE r.rn IS NULL OR r.rn = 1
            """
        )
        try:
            async with rx.asession() as asession:
                blob_rows = (
                    await asession.execute(keyword_query, params)
                ).all()
                demo_rows = (
                    await asession.execute(demographics_query, params)
                ).all()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Could not load category metrics: {e}")
            async with self:
                self.error = "We couldn't load the category insights just now."
            return
        blobs = [f"{r[0] or ''} {r[1] or ''}" for r in blob_rows]
        words = _meaningful_words(blobs)
        helper_age = ""
        helper_sample = 0
        helper_nat = ""
        helper_nat_count = 0
        helper_nat_sample = 0
        helpee_age = ""
        helpee_sample = 0
        helpee_nat = ""
        helpee_nat_count = 0
        helpee_nat_sample = 0
        for row in demo_rows:
            role = str(row[0] or "")
            age_label = "" if row[1] is None else f"{float(row[1]):.1f}"
            sample = int(row[2] or 0)
            nat = str(row[3] or "")
            nat_count = int(row[4] or 0)
            nat_total = int(row[5] or 0)
            if role == "helper":
                helper_age = age_label
                helper_sample = sample
                helper_nat = nat
                helper_nat_count = nat_count
                helper_nat_sample = nat_total
            elif role == "helpee":
                helpee_age = age_label
                helpee_sample = sample
                helpee_nat = nat
                helpee_nat_count = nat_count
                helpee_nat_sample = nat_total
        async with self:
            self.keywords = _rank_rows(words)
            self.helper_age_label = helper_age
            self.helper_age_sample = helper_sample
            self.helper_nationality = helper_nat
            self.helper_nationality_count = helper_nat_count
            self.helper_nationality_sample = helper_nat_sample
            self.helpee_age_label = helpee_age
            self.helpee_age_sample = helpee_sample
            self.helpee_nationality = helpee_nat
            self.helpee_nationality_count = helpee_nat_count
            self.helpee_nationality_sample = helpee_nat_sample
