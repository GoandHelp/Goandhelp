"""Help-request bookmarks: one row per (member, request), toggled in place."""

import logging
from typing import Any, TypedDict

import reflex as rx
from sqlalchemy import text

from app.filter_categories import category_label
from app.states.auth_state import AuthState


class SavedRequest(TypedDict):
    id: int
    title: str
    category_label: str
    reward_label: str
    location: str
    scheduled: str
    status: str
    saved: str
    note: str


REWARD_LABELS: dict[str, str] = {
    "lunch": "Lunch",
    "dinner": "Dinner",
    "accommodation": "Accommodation",
    "guided_tours": "Guided tours",
    "workshops": "Workshops",
    "lessons": "Lessons",
    "other": "Other",
}


class BookmarkState(rx.State):
    bookmarked_ids: list[int] = []
    saved_requests: list[SavedRequest] = []
    is_loading: bool = False
    has_loaded: bool = False
    busy_id: int = 0
    note_busy_id: int = 0
    error: str = ""
    success: str = ""

    @rx.var
    def saved_count(self) -> int:
        return len(self.saved_requests)

    @rx.event(background=True)
    async def load_bookmarks(self):
        """Load every bookmark of the signed-in member, newest first."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            self.error = ""
        if not sid.isdigit():
            async with self:
                self.bookmarked_ids = []
                self.saved_requests = []
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
                            SELECT b.help_post_id, p.title,
                                   COALESCE(p.category, ''),
                                   COALESCE(p.category_tags, ''),
                                   COALESCE(p.reward_type, ''),
                                   COALESCE(p.city, ''),
                                   COALESCE(p.country, ''),
                                   p.scheduled_for,
                                   COALESCE(p.status, 'open'),
                                   b.created_at,
                                   COALESCE(b.note, '')
                            FROM skillkind_help_post_bookmark b
                            JOIN skillkind_help_post p
                                 ON p.id = b.help_post_id
                            WHERE b.subscriber_id = :sid
                            ORDER BY b.created_at DESC
                            LIMIT 60
                            """
                        ),
                        {"sid": int(sid)},
                    )
                ).all()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Could not load saved help requests: {e}")
            async with self:
                self.is_loading = False
                self.has_loaded = True
                self.error = (
                    "We could not load your saved help requests just now. "
                    "Please try again in a moment."
                )
            return
        saved: list[SavedRequest] = []
        ids: list[int] = []
        for row in rows:
            post_id = int(row[0])
            ids.append(post_id)
            tags = [
                part.strip()
                for part in str(row[3] or "").split(",")
                if part.strip()
            ]
            primary = tags[0] if tags else str(row[2] or "")
            reward = str(row[4] or "")
            place = ", ".join(
                [
                    part
                    for part in (str(row[5] or ""), str(row[6] or ""))
                    if part
                ]
            )
            saved.append(
                {
                    "id": post_id,
                    "title": str(row[1] or "Help needed"),
                    "category_label": category_label(primary)
                    if primary
                    else "Any help",
                    "reward_label": REWARD_LABELS.get(
                        reward, reward.replace("_", " ").title()
                    )
                    or "Reward to agree",
                    "location": place or "Approximate area",
                    "scheduled": row[7].strftime("%b %d · %H:%M")
                    if row[7] is not None
                    else "Time to agree",
                    "status": str(row[8] or "open"),
                    "saved": row[9].strftime("%b %d, %Y")
                    if row[9] is not None
                    else "",
                    "note": str(row[10] or ""),
                }
            )
        async with self:
            self.bookmarked_ids = ids
            self.saved_requests = saved
            self.is_loading = False
            self.has_loaded = True

    @rx.event(background=True)
    async def toggle_bookmark(self, post_id: int):
        """Save or unsave one request. Never opens or selects the request."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            was_saved = int(post_id) in self.bookmarked_ids
            self.error = ""
            self.success = ""
            self.busy_id = int(post_id)
        if not sid.isdigit():
            async with self:
                self.busy_id = 0
                self.error = "Sign in to save a help request."
            return
        try:
            async with rx.asession() as asession:
                if was_saved:
                    await asession.execute(
                        text(
                            """
                            DELETE FROM skillkind_help_post_bookmark
                            WHERE subscriber_id = :sid
                              AND help_post_id = :pid
                            """
                        ),
                        {"sid": int(sid), "pid": int(post_id)},
                    )
                else:
                    await asession.execute(
                        text(
                            """
                            INSERT INTO skillkind_help_post_bookmark
                                (subscriber_id, help_post_id, note, created_at)
                            SELECT :sid, :pid, '', now()
                            FROM skillkind_help_post p
                            WHERE p.id = :pid AND p.author_id <> :sid
                            ON CONFLICT (subscriber_id, help_post_id)
                            DO NOTHING
                            """
                        ),
                        {"sid": int(sid), "pid": int(post_id)},
                    )
                await asession.commit()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Could not change a bookmark: {e}")
            async with self:
                self.busy_id = 0
                self.error = (
                    "We could not change that bookmark. Please try again."
                )
            return
        async with self:
            self.busy_id = 0
            self.success = (
                "Removed from your saved help requests."
                if was_saved
                else "Saved to your help requests."
            )
        yield BookmarkState.load_bookmarks

    @rx.event(background=True)
    async def save_note(self, post_id: int, form_data: dict[str, Any]):
        """Store a private note on the signed-in member's own bookmark."""
        note = str(form_data.get("note", "") or "").strip()[:255]
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            self.error = ""
            self.success = ""
            self.note_busy_id = int(post_id)
        if not sid.isdigit():
            async with self:
                self.note_busy_id = 0
                self.error = "Sign in to add a private note."
            return
        try:
            async with rx.asession() as asession:
                result = await asession.execute(
                    text(
                        """
                        UPDATE skillkind_help_post_bookmark
                        SET note = :note
                        WHERE subscriber_id = :sid
                          AND help_post_id = :pid
                        """
                    ),
                    {"note": note, "sid": int(sid), "pid": int(post_id)},
                )
                await asession.commit()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Could not save a bookmark note: {e}")
            async with self:
                self.note_busy_id = 0
                self.error = (
                    "We could not save your private note. Please try again."
                )
            return
        if not result.rowcount:
            async with self:
                self.note_busy_id = 0
                self.error = (
                    "That help request is no longer in your saved list, so "
                    "the note was not saved."
                )
            return
        async with self:
            self.note_busy_id = 0
            self.success = (
                "Private note cleared."
                if not note
                else "Private note saved. Only you can see it."
            )
        yield BookmarkState.load_bookmarks

    @rx.event
    async def open_on_map(self, post_id: int):
        """Open a saved request on the member map, unfiltered."""
        from app.states.discovery_state import DiscoveryState
        from app.states.profile_state import ProfileState

        profile = await self.get_state(ProfileState)
        profile.active_tab = "discover"
        self.error = ""
        self.success = ""
        return DiscoveryState.focus_post(int(post_id))
