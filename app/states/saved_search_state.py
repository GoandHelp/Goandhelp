"""Saved Discover search alerts, persisted per signed-in member.

Every filter the Discover screen exposes is stored so the exact search can be
recreated later. The normalized columns of `skillkind_saved_search_alert` cover
categories, reward, place and languages; the premium advanced filters (last
online, combined rating window and nationality) are packed into the `keyword`
column as a compact `key=value;` string, which has no other use in this app.

`fingerprint` is the SHA-256 digest of the normalized filter set and is unique
per subscriber, so saving the same search twice is refused rather than
duplicated.
"""

import hashlib
import logging
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.filter_categories import category_label
from app.models import SAVED_SEARCH_LABEL_MAX_LENGTH
from app.states.auth_state import AuthState
from app.states.discovery_state import (
    REWARD_LABELS,
    DiscoveryState,
    clamp_distance_km,
)

LAST_ONLINE_LABELS: dict[str, str] = {
    "today": "Online today",
    "week": "Online this week",
    "month": "Online this month",
}


class SavedAlert(TypedDict):
    id: int
    label: str
    summary: str
    chips: list[str]
    is_enabled: bool
    created: str
    categories: list[str]
    reward: str
    city: str
    languages: list[str]
    keyword: str
    # 0 means the saved search covered any distance.
    radius_km: int


def _split(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _encode_advanced(
    last_online: str, rating_min: int, rating_max: int, nationality: str
) -> str:
    """Pack the premium filters into one short, re-readable string."""
    pieces: list[str] = []
    if last_online in LAST_ONLINE_LABELS:
        pieces.append(f"online={last_online}")
    if rating_min > 0 or rating_max < 100:
        pieces.append(f"rating={rating_min}-{rating_max}")
    if nationality:
        pieces.append(f"nat={nationality.lower()}")
    return ";".join(pieces)[:160]


def _decode_advanced(keyword: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for piece in keyword.split(";"):
        if "=" in piece:
            key, _, value = piece.partition("=")
            parsed[key.strip()] = value.strip()
    return parsed


def _chips(
    categories: list[str],
    reward: str,
    city: str,
    languages: list[str],
    keyword: str,
    radius_km: int = 0,
) -> list[str]:
    """Human-readable description of every filter stored on an alert."""
    chips: list[str] = [f"Category: {category_label(c)}" for c in categories]
    if radius_km > 0:
        chips.append(f"Distance: {radius_km} km")
    if reward:
        chips.append(f"Reward: {REWARD_LABELS.get(reward, reward.title())}")
    if city:
        chips.append(f"Place: {city}")
    for language in languages:
        chips.append(f"Speaks {language.title()}")
    advanced = _decode_advanced(keyword)
    online = advanced.get("online", "")
    if online in LAST_ONLINE_LABELS:
        chips.append(LAST_ONLINE_LABELS[online])
    rating = advanced.get("rating", "")
    if rating:
        chips.append(f"Rating {rating.replace('-', '–')}%")
    nationality = advanced.get("nat", "")
    if nationality:
        chips.append(f"Nationality: {nationality.title()}")
    return chips


class SavedSearchState(rx.State):
    alerts: list[SavedAlert] = []
    is_loading: bool = False
    has_loaded: bool = False
    is_saving: bool = False
    busy_id: int = 0
    error: str = ""
    success: str = ""

    @rx.var
    def alert_count(self) -> int:
        return len(self.alerts)

    @rx.var
    def enabled_count(self) -> int:
        return len([a for a in self.alerts if a["is_enabled"]])

    def _row_to_alert(self, row) -> SavedAlert:
        categories = _split(str(row[4] or ""))
        reward = str(row[5] or "")
        city = str(row[6] or "")
        languages = _split(str(row[7] or ""))
        keyword = str(row[3] or "")
        radius_km = clamp_distance_km(int(row[9] or 0)) if len(row) > 9 else 0
        chips = _chips(categories, reward, city, languages, keyword, radius_km)
        return {
            "id": int(row[0]),
            "label": str(row[1] or "Saved search"),
            "summary": " · ".join(chips) or "Every open help request",
            "chips": chips,
            "is_enabled": bool(row[2]),
            "created": row[8].strftime("%b %d, %Y")
            if row[8] is not None
            else "",
            "categories": categories,
            "reward": reward,
            "city": city,
            "languages": languages,
            "keyword": keyword,
            "radius_km": radius_km,
        }

    @rx.event(background=True)
    async def load_alerts(self):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            self.error = ""
        if not sid.isdigit():
            async with self:
                self.alerts = []
                self.is_loading = False
                self.has_loaded = True
            return
        async with self:
            self.is_loading = True
        try:
            async with rx.asession() as asession:
                rows = (
                    await asession.execute(
                        text(
                            """
                            SELECT id, label, is_enabled, keyword,
                                   category_tags, reward_types, city, languages,
                                   created_at, COALESCE(radius_km, 0)
                            FROM skillkind_saved_search_alert
                            WHERE subscriber_id = :sid
                            ORDER BY created_at DESC
                            LIMIT 40
                            """
                        ),
                        {"sid": int(sid)},
                    )
                ).all()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Could not load saved searches: {e}")
            async with self:
                self.is_loading = False
                self.has_loaded = True
                self.error = (
                    "We could not load your saved searches just now. "
                    "Please try again in a moment."
                )
            return
        loaded = [self._row_to_alert(row) for row in rows]
        async with self:
            self.alerts = loaded
            self.is_loading = False
            self.has_loaded = True

    @rx.event(background=True)
    async def save_current_search(self):
        """Store the live Discover filters as one alert, never twice."""
        async with self:
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id
            discovery = await self.get_state(DiscoveryState)
            categories = sorted(
                {c.strip().lower() for c in discovery.category_filters if c}
            )
            reward = (
                discovery.reward_filter
                if discovery.reward_filter in REWARD_LABELS
                else ""
            )
            city = discovery.city_filter.strip()[:120]
            languages = sorted(
                {
                    lang.strip().lower()
                    for lang in discovery.language_filters
                    if lang.strip()
                }
            )
            keyword = _encode_advanced(
                discovery.last_online_filter,
                int(discovery.rating_min),
                int(discovery.rating_max),
                discovery.nationality_filter.strip(),
            )
            radius_km = clamp_distance_km(int(discovery.distance_km))
            self.error = ""
            self.success = ""
        if not sid.isdigit():
            async with self:
                self.error = "Sign in to save a search and get alerts."
            return
        chips = _chips(categories, reward, city, languages, keyword, radius_km)
        label = (" · ".join(chips) or "Every open help request")[
            :SAVED_SEARCH_LABEL_MAX_LENGTH
        ]
        fingerprint = hashlib.sha256(
            "|".join(
                [
                    ",".join(categories),
                    reward,
                    city.lower(),
                    ",".join(languages),
                    keyword,
                    str(radius_km),
                ]
            ).encode()
        ).hexdigest()
        async with self:
            self.is_saving = True
        try:
            async with rx.asession() as asession:
                existing = (
                    await asession.execute(
                        text(
                            """
                            SELECT id FROM skillkind_saved_search_alert
                            WHERE subscriber_id = :sid
                              AND fingerprint = :fingerprint
                            """
                        ),
                        {"sid": int(sid), "fingerprint": fingerprint},
                    )
                ).first()
                if existing is not None:
                    async with self:
                        self.is_saving = False
                        self.success = ""
                        self.error = (
                            "You have already saved this exact search — find "
                            "it in Saved search alerts."
                        )
                    return
                await asession.execute(
                    text(
                        """
                        INSERT INTO skillkind_saved_search_alert
                            (subscriber_id, fingerprint, label, keyword,
                             category_tags, reward_types, urgency, city,
                             country, radius_km, min_duration_minutes,
                             max_duration_minutes, languages, verified_only,
                             with_photos_only, is_enabled, notify_by_email,
                             match_count, created_at)
                        VALUES
                            (:sid, :fingerprint, :label, :keyword,
                             :categories, :reward, '', :city,
                             '', :radius_km, 0,
                             0, :languages, FALSE,
                             FALSE, TRUE, TRUE,
                             0, now())
                        ON CONFLICT (subscriber_id, fingerprint) DO NOTHING
                        """
                    ),
                    {
                        "sid": int(sid),
                        "fingerprint": fingerprint,
                        "label": label,
                        "keyword": keyword,
                        "categories": ",".join(categories)[:500],
                        "reward": reward,
                        "city": city,
                        "radius_km": int(radius_km),
                        "languages": ",".join(languages)[:255],
                    },
                )
                await asession.commit()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Could not save a search alert: {e}")
            async with self:
                self.is_saving = False
                self.error = (
                    "We could not save that search. Please try again shortly."
                )
            return
        async with self:
            self.is_saving = False
            self.success = "Search saved. We'll alert you about new matches."
        yield rx.toast("Search saved to My requests.", duration=4000)
        yield SavedSearchState.load_alerts

    @rx.event(background=True)
    async def toggle_alert(self, alert_id: int):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            self.error = ""
            self.success = ""
            self.busy_id = int(alert_id)
        if not sid.isdigit():
            async with self:
                self.busy_id = 0
                self.error = "Sign in to manage your saved searches."
            return
        try:
            async with rx.asession() as asession:
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_saved_search_alert
                        SET is_enabled = NOT is_enabled, updated_at = now()
                        WHERE id = :aid AND subscriber_id = :sid
                        """
                    ),
                    {"aid": int(alert_id), "sid": int(sid)},
                )
                await asession.commit()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Could not update a saved search: {e}")
            async with self:
                self.busy_id = 0
                self.error = (
                    "We could not change that alert. Please try again shortly."
                )
            return
        async with self:
            self.busy_id = 0
        yield SavedSearchState.load_alerts

    @rx.event(background=True)
    async def delete_alert(self, alert_id: int):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            self.error = ""
            self.success = ""
            self.busy_id = int(alert_id)
        if not sid.isdigit():
            async with self:
                self.busy_id = 0
                self.error = "Sign in to manage your saved searches."
            return
        try:
            async with rx.asession() as asession:
                await asession.execute(
                    text(
                        """
                        DELETE FROM skillkind_saved_search_alert
                        WHERE id = :aid AND subscriber_id = :sid
                        """
                    ),
                    {"aid": int(alert_id), "sid": int(sid)},
                )
                await asession.commit()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Could not delete a saved search: {e}")
            async with self:
                self.busy_id = 0
                self.error = (
                    "We could not delete that alert. Please try again shortly."
                )
            return
        async with self:
            self.busy_id = 0
            self.success = "Saved search deleted."
        yield SavedSearchState.load_alerts

    @rx.event
    async def apply_alert(self, alert_id: int):
        """Recreate a saved search on the map, exactly as it was stored."""
        from app.states.profile_state import ProfileState

        chosen = [a for a in self.alerts if a["id"] == int(alert_id)]
        if not chosen:
            self.error = "That saved search is no longer available."
            return
        alert = chosen[0]
        advanced = _decode_advanced(alert["keyword"])
        rating = advanced.get("rating", "")
        rating_min, rating_max = 0, 100
        if "-" in rating:
            low, _, high = rating.partition("-")
            if low.isdigit() and high.isdigit():
                rating_min, rating_max = int(low), int(high)
        discovery = await self.get_state(DiscoveryState)
        discovery.map_mode = "give"
        discovery.view_mode = "map"
        discovery.category_filters = list(alert["categories"])
        discovery.reward_filter = alert["reward"] or "all"
        discovery.city_filter = alert["city"]
        discovery.language_filters = list(alert["languages"])
        discovery.last_online_filter = advanced.get("online", "any") or "any"
        discovery.rating_min = rating_min
        discovery.rating_max = rating_max
        discovery.nationality_filter = advanced.get("nat", "")
        discovery.distance_km = clamp_distance_km(int(alert["radius_km"]))
        discovery.distance_initialized = True
        discovery.distance_reset_token += 1
        discovery.filter_panel_open = False
        profile = await self.get_state(ProfileState)
        profile.active_tab = "discover"
        self.error = ""
        self.success = ""
        return DiscoveryState.load_jobs
