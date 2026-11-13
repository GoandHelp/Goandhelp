"""In-app member notifications: unread counters and the recent list."""

import json
import logging
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.states.auth_state import AuthState
from app.notification_content import (
    REVIEW_REMINDER_SQL,
    concise_text,
    review_task_id,
)

NOTIFICATION_PREFERENCE_KEYS = (
    "notify_help_offers",
    "notify_requests_in_my_field",
    "notify_messages",
    "notify_schedule_changes",
    "notify_community_activity",
    "notify_reminders",
)


def notification_preferences(raw: object) -> dict[str, bool]:
    try:
        values = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError) as e:
        logging.exception(f"Error: {e}")
        values = {}
    if not isinstance(values, dict):
        values = {}
    return {
        key: values.get(key) if type(values.get(key)) is bool else True
        for key in NOTIFICATION_PREFERENCE_KEYS
    }


NOTIFICATION_FILTER = """
    CASE
        WHEN kind = 'requests_in_my_field' THEN :notify_requests_in_my_field
        WHEN LOWER(TRIM(COALESCE(target_route, ''))) = 'community'
             OR LOWER(TRIM(COALESCE(target_route, ''))) LIKE 'community:%'
             OR kind LIKE 'community_%' THEN :notify_community_activity
        WHEN kind IN ('help_offer', 'help_confirmed', 'direct_help_request',
                      'direct_request', 'request_accepted', 'request_declined')
             THEN :notify_help_offers
        WHEN kind = 'inbox_message' THEN :notify_messages
        WHEN kind IN ('schedule_proposed', 'schedule_confirmed', 'schedule_declined')
             THEN :notify_schedule_changes
        ELSE :notify_reminders
    END
"""

COMMUNITY_KINDS: tuple[str, ...] = ("community_like", "community_reply")
HELP_KINDS: tuple[str, ...] = (
    "help_offer",
    "help_confirmed",
    "direct_help_request",
    "direct_request",
    "request_accepted",
    "request_declined",
    "job_expired",
    "job_renewed",
    "job_started",
    "job_completed",
    "job_reminder",
    "task_reminder",
    "check_in_reminder",
    "cancellation_proposed",
    "cancellation_accepted",
    "cancellation_declined",
    "no_show_reported",
    "schedule_proposed",
    "schedule_confirmed",
    "schedule_declined",
)
INBOX_KINDS: tuple[str, ...] = ("inbox_message",)

KIND_ICONS: dict[str, str] = {
    "community_like": "heart",
    "community_reply": "message-square",
    "inbox_message": "mail",
    "help_offer": "hand-helping",
    "help_confirmed": "circle-check-big",
    "schedule_proposed": "calendar-clock",
    "schedule_confirmed": "calendar-check",
    "schedule_declined": "calendar-x",
}

KIND_LABELS: dict[str, str] = {
    "community_like": "Community",
    "community_reply": "Community",
    "inbox_message": "Inbox",
    "help_offer": "Help",
    "help_confirmed": "Help",
    "schedule_proposed": "Help",
    "schedule_confirmed": "Help",
    "schedule_declined": "Help",
}

# Events reuse the Help kinds but are routed to Community, and review notices
# reuse the allowed `community_like` kind with a review-shaped title. Both are
# recognised from the existing columns — no schema change is needed.
COMMUNITY_ROUTE = "community"
REVIEW_TITLE_MARKER = "review"


def _classify(kind: str, route: str, title: str) -> tuple[str, str]:
    """Return (area, subsection) for one notification row.

    area is `community`, `inbox` or `help`; subsection is `forum`, `events`,
    `reviews` or an empty string when the area has no subsection.
    """
    normalised_route = (route or "").strip().lower()
    lowered_title = (title or "").lower()
    if normalised_route.startswith("community:"):
        subsection = normalised_route.split(":")[1]
        return (
            "community",
            subsection if subsection in ("reviews", "events") else "forum",
        )
    if kind == "requests_in_my_field":
        return ("help", "")
    if kind in HELP_KINDS:
        # An event notice is routed to Community, so it counts as Community.
        if normalised_route == COMMUNITY_ROUTE:
            return ("community", "events")
        return ("help", "")
    if kind in COMMUNITY_KINDS:
        if kind == "community_like" and REVIEW_TITLE_MARKER in lowered_title:
            return ("community", "reviews")
        return ("community", "forum")
    return ("inbox", "")


class NotificationItem(TypedDict):
    id: int
    kind: str
    icon: str
    area: str
    title: str
    body: str
    created: str
    is_read: bool
    actor_id: int
    actor_name: str
    actor_avatar: str
    actor_seed: str
    community_topic_id: int
    community_comment_id: int
    help_post_id: int
    contact_link_id: int
    noncontact_conversation_id: int
    target_route: str
    review_task_id: int


class NotificationState(rx.State):
    """Real unread counters and recent notices for the signed-in member."""

    community_unread: int = 0
    inbox_unread: int = 0
    help_unread: int = 0
    # Community subsections, so a quiet dot can sit on the right tab.
    forum_unread: int = 0
    events_unread: int = 0
    reviews_unread: int = 0
    # Contextual read model: which containers have unread activity.
    unread_topic_ids: list[int] = []
    unread_help_post_ids: list[int] = []
    unread_contact_link_ids: list[int] = []
    unread_noncontact_ids: list[int] = []
    recent: list[NotificationItem] = []
    is_loading: bool = False
    error: str = ""
    panel_open: bool = False
    read_busy: bool = False
    action_id: int = 0
    field_unread: int = 0
    field_created: str = ""

    @rx.event(background=True)
    async def delete_field_group(self):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            if not sid.isdigit() or self.action_id:
                return
            self.action_id = -1
        try:
            async with rx.asession() as session:
                await session.execute(
                    text("""
                    DELETE FROM skillkind_member_notification
                    WHERE recipient_id=:sid AND kind='requests_in_my_field' AND is_read=FALSE
                """),
                    {"sid": int(sid)},
                )
                await session.commit()
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    "Could not delete these notifications. Please try again."
                )
        finally:
            async with self:
                self.action_id = 0
        yield NotificationState.load_notifications

    @rx.event(background=True)
    async def open_field_group(self):
        from app.field_requests import owned_field_matches
        from app.states.discovery_state import (
            DiscoveryState,
            MODE_GIVE,
            VIEW_MAP,
            VIEW_LIST,
        )
        from app.states.profile_state import ProfileState

        async with self:
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id
            if not auth.is_signed_in or not sid.isdigit() or self.action_id:
                return
            self.action_id = -1
            self.error = ""
        try:
            async with rx.asession() as session:
                matches = await owned_field_matches(session, int(sid))
                if matches:
                    await session.execute(
                        text("""
                        UPDATE skillkind_member_notification SET is_read=TRUE, read_at=now()
                        WHERE recipient_id=:sid AND kind='requests_in_my_field'
                          AND is_read=FALSE AND id=ANY(:notices)
                    """),
                        {
                            "sid": int(sid),
                            "notices": [row[0] for row in matches],
                        },
                    )
                await session.commit()
            async with self:
                if (await self.get_state(AuthState)).subscriber_id != sid:
                    return
                if not matches:
                    self.error = "These requests are no longer available or no longer match your preferences."
                    return
                discovery = await self.get_state(DiscoveryState)
                profile = await self.get_state(ProfileState)
                posts = sorted({row[1] for row in matches})
                visible = discovery.viewport_ready and all(
                    pid in discovery.visible_post_ids for pid in posts
                )
                await profile._dismiss_navigation_surfaces()
                profile.active_tab = "discover"
                discovery.map_mode = MODE_GIVE
                discovery.view_mode = VIEW_MAP if visible else VIEW_LIST
                discovery._field_priority_post_ids = posts
                discovery._field_priority_owner = sid
                discovery.map_pulse_post_ids = posts
                discovery.map_pulse_token += 1
                discovery.category_filters = []
                discovery.reward_filter = "all"
                discovery.city_filter = ""
                discovery.distance_km = 0
                discovery.distance_reset_token += 1
                discovery.last_online_filter = "any"
                discovery.rating_min = 0
                discovery.rating_max = 100
                discovery.nationality_filter = ""
                discovery.language_filters = []
                self.panel_open = False
            yield DiscoveryState.load_jobs
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    "Could not open matching requests. Please try again."
                )
        finally:
            async with self:
                self.action_id = 0
        yield NotificationState.load_notifications

    @rx.event(background=True)
    async def delete_notification(self, notification_id: int):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            if not sid.isdigit() or self.action_id:
                return
            self.action_id = notification_id
        try:
            async with rx.asession() as session:
                await session.execute(
                    text(
                        "DELETE FROM skillkind_member_notification WHERE id=:nid AND recipient_id=:sid"
                    ),
                    {"nid": notification_id, "sid": int(sid)},
                )
                await session.commit()
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    "Could not delete this notification. Please try again."
                )
        finally:
            async with self:
                self.action_id = 0
        yield NotificationState.load_notifications

    @rx.event(background=True)
    async def open_notification(self, item: NotificationItem):
        from app.states.profile_state import ProfileState
        from app.states.community_state import CommunityState
        from app.states.messaging_state import MessagingState
        from app.states.contacts_state import ContactsState
        from app.states.noncontact_state import NonContactMessagingState
        from app.states.unified_inbox_state import UnifiedInboxState
        from app.states.event_state import EventState
        from app.states.help_hub_state import HelpHubState

        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            if not sid.isdigit() or self.action_id:
                return
            self.action_id = item["id"]
            self.error = ""
            self.panel_open = False
        try:
            async with rx.asession() as session:
                row = (
                    await session.execute(
                        text("""
                    SELECT kind, target_route, title, COALESCE(actor_id, 0),
                           COALESCE(community_topic_id, 0), COALESCE(help_post_id, 0),
                           COALESCE(contact_link_id, 0), COALESCE(noncontact_conversation_id, 0)
                    FROM skillkind_member_notification n
                    WHERE id = :nid AND recipient_id = :sid
                      AND NOT EXISTS (SELECT 1 FROM skillkind_member_block b
                          WHERE (b.blocker_id=:sid AND b.blocked_id=n.actor_id)
                             OR (b.blocked_id=:sid AND b.blocker_id=n.actor_id))
                    LIMIT 1
                """),
                        {"nid": item["id"], "sid": int(sid)},
                    )
                ).first()
                if not row:
                    raise ValueError("Notification unavailable")
                kind, route, title = str(row[0]), str(row[1] or ""), str(row[2])
                actor, topic, post, contact, direct = (int(v) for v in row[3:])
                area, section = _classify(kind, route, title)
                task = review_task_id(route)
                thread = 0
                if post and area != "community":
                    thread_row = (
                        await session.execute(
                            text("""
                        SELECT t.id FROM skillkind_message_thread t
                        WHERE t.post_id=:pid AND :sid IN (t.poster_id,t.helper_id)
                          AND (:actor=0 OR :actor IN (t.poster_id,t.helper_id))
                          AND NOT EXISTS (SELECT 1 FROM skillkind_member_block b
                            WHERE (b.blocker_id=t.poster_id AND b.blocked_id=t.helper_id)
                               OR (b.blocker_id=t.helper_id AND b.blocked_id=t.poster_id))
                        ORDER BY t.id DESC LIMIT 1
                    """),
                            {"pid": post, "sid": int(sid), "actor": actor},
                        )
                    ).first()
                    thread = int(thread_row[0]) if thread_row else 0
                await session.execute(
                    text(
                        "UPDATE skillkind_member_notification SET is_read=true, read_at=NOW() WHERE id=:nid AND recipient_id=:sid"
                    ),
                    {"nid": item["id"], "sid": int(sid)},
                )
                await session.commit()
            async with self:
                profile = await self.get_state(ProfileState)
                community = await self.get_state(CommunityState)
                messaging = await self.get_state(MessagingState)
                contacts = await self.get_state(ContactsState)
                noncontact = await self.get_state(NonContactMessagingState)
                unified = await self.get_state(UnifiedInboxState)
            # These loaders perform I/O unlocked and apply results inside their
            # own `async with self` contexts; never wrap their I/O in our lock.
            if contact:
                await contacts._load_contacts_data(sid, 0)
                async with self:
                    if (await self.get_state(AuthState)).subscriber_id != sid:
                        return
                    available = next(
                        (
                            c
                            for c in [
                                *contacts.contacts,
                                *contacts.incoming_requests,
                            ]
                            if c["link_id"] == contact
                        ),
                        None,
                    )
                    if not available:
                        raise ValueError("Contact unavailable")
                    if available["status"] == "pending":
                        profile.active_tab = "community"
                        community.section = "contacts"
                    else:
                        unified.preserve_next_mount = (
                            profile.active_tab != "inbox"
                        )
                        profile.active_tab = "inbox"
                if available["status"] != "pending":
                    yield UnifiedInboxState.open_item("contact", contact)
            elif direct:
                await noncontact._load_conversations_data(sid)
                async with self:
                    if (await self.get_state(AuthState)).subscriber_id != sid:
                        return
                    if not any(
                        c["conv_id"] == direct for c in noncontact.conversations
                    ):
                        raise ValueError("Conversation unavailable")
                    unified.preserve_next_mount = profile.active_tab != "inbox"
                    profile.active_tab = "inbox"
                yield UnifiedInboxState.open_item("noncontact", direct)
            elif task:
                async with rx.asession() as session:
                    eligible = await messaging._eligible_review_task(
                        session, task, int(sid)
                    )
                if not eligible:
                    raise ValueError("Review no longer available")
                async with self:
                    messaging.dismissed_review_task_ids = [
                        value
                        for value in messaging.dismissed_review_task_ids
                        if value != task
                    ]
                await messaging._load_threads_data(sid, 0)
                async with self:
                    if (await self.get_state(AuthState)).subscriber_id != sid:
                        return
                    target = next(
                        (
                            t
                            for t in messaging.review_targets
                            if t["task_id"] == task
                        ),
                        None,
                    )
                    if not target:
                        raise ValueError("Review no longer available")
                    messaging.review_navigation_pending = True
                    profile.active_tab = "community"
                    community.section = "reviews"
                yield MessagingState.select_review_target(task)
                yield MessagingState.open_review_target
            elif thread:
                async with self:
                    messaging.thread_filter = "all"
                await messaging._load_threads_data(sid, thread)
                async with self:
                    if (await self.get_state(AuthState)).subscriber_id != sid:
                        return
                    if not any(t["id"] == thread for t in messaging.threads):
                        raise ValueError("Conversation unavailable")
                    unified.preserve_next_mount = profile.active_tab != "inbox"
                    profile.active_tab = "inbox"
                yield UnifiedInboxState.open_item("job", thread)
            elif area == "community":
                async with self:
                    profile.active_tab = "community"
                    community.section = (
                        "community" if section == "forum" else section
                    )
                if section == "forum":
                    if not topic:
                        raise ValueError("Discussion unavailable")
                    yield CommunityState.open_notification_topic(topic)
                elif section == "events":
                    yield EventState.load_events
                else:
                    yield MessagingState.load_review_targets
            elif area == "help" and post:
                async with self:
                    profile.active_tab = "help"
                yield HelpHubState.load_help_hub
            else:
                raise ValueError("Destination unavailable")
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    "This notification destination is no longer available."
                )
            yield rx.toast(
                "This notification destination is no longer available."
            )
        finally:
            async with self:
                self.action_id = 0
        yield NotificationState.load_notifications

    @rx.event
    async def open_panel(self):
        from app.states.profile_state import ProfileState
        from app.states.discovery_state import DiscoveryState
        from app.states.world_search_state import WorldSearchState

        (await self.get_state(ProfileState)).settings_open = False
        (await self.get_state(DiscoveryState)).filter_panel_open = False
        (await self.get_state(WorldSearchState)).expanded = False
        self.panel_open = True
        return NotificationState.load_notifications

    @rx.event
    def close_panel(self):
        self.panel_open = False

    @rx.event
    def toggle_panel(self):
        if self.panel_open:
            self.panel_open = False
        else:
            return NotificationState.open_panel

    @rx.event
    async def toggle_map_settings(self):
        from app.states.profile_state import ProfileState
        from app.states.discovery_state import DiscoveryState
        from app.states.world_search_state import WorldSearchState

        profile = await self.get_state(ProfileState)
        profile.settings_open = not profile.settings_open
        self.panel_open = False
        (await self.get_state(DiscoveryState)).filter_panel_open = False
        (await self.get_state(WorldSearchState)).expanded = False
        if profile.settings_open:
            return ProfileState.load_notification_preferences

    @rx.event
    async def toggle_map_filters(self):
        from app.states.profile_state import ProfileState
        from app.states.discovery_state import DiscoveryState
        from app.states.world_search_state import WorldSearchState

        self.panel_open = False
        (await self.get_state(ProfileState)).settings_open = False
        (await self.get_state(WorldSearchState)).expanded = False
        discovery = await self.get_state(DiscoveryState)
        discovery.filter_panel_open = not discovery.filter_panel_open

    @rx.event
    async def open_map_search(self):
        from app.states.profile_state import ProfileState
        from app.states.discovery_state import DiscoveryState
        from app.states.world_search_state import WorldSearchState

        self.panel_open = False
        (await self.get_state(ProfileState)).settings_open = False
        (await self.get_state(DiscoveryState)).filter_panel_open = False
        (await self.get_state(WorldSearchState)).expanded = True

    @rx.var
    def total_unread(self) -> int:
        return self.community_unread + self.inbox_unread + self.help_unread

    @rx.var
    def has_notifications(self) -> bool:
        return len(self.recent) > 0 or self.field_unread > 0

    @rx.event(background=True)
    async def load_notifications(self):
        """Load unread counters per area plus the newest notices."""
        async with self:
            if self.is_loading:
                return
            sid = (await self.get_state(AuthState)).subscriber_id
            self.is_loading = True
            self.error = ""
        if not sid.isdigit():
            async with self:
                self.community_unread = 0
                self.inbox_unread = 0
                self.help_unread = 0
                self.forum_unread = 0
                self.events_unread = 0
                self.reviews_unread = 0
                self.unread_topic_ids = []
                self.unread_help_post_ids = []
                self.unread_contact_link_ids = []
                self.unread_noncontact_ids = []
                self.recent = []
                self.field_unread = 0
                self.field_created = ""
                self.is_loading = False
            return
        try:
            await self._load_notifications_data(sid)
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.is_loading = False
                self.error = "We couldn't load notifications. Please try again."

    async def _load_notifications_data(self, sid: str) -> None:
        try:
            async with rx.asession() as asession:
                # Serialize reminder creation per recipient; the existing dedupe index is not unique.
                await asession.execute(
                    text(
                        "SELECT id FROM skillkind_subscriber WHERE id=:sid FOR UPDATE"
                    ),
                    {"sid": int(sid)},
                )
                await asession.execute(
                    text(REVIEW_REMINDER_SQL), {"sid": int(sid)}
                )
                await asession.commit()
                raw_preferences = (
                    await asession.execute(
                        text(
                            "SELECT permissions_json FROM skillkind_onboarding_progress WHERE subscriber_id = :sid"
                        ),
                        {"sid": int(sid)},
                    )
                ).scalar_one_or_none()
                preferences = notification_preferences(raw_preferences)
                from app.field_requests import (
                    HELPER_MATCH_SQL,
                    DISTANCE_SQL,
                    field_preferences,
                )

                field_enabled, field_radius = field_preferences(raw_preferences)
                field_summary = (
                    await asession.execute(
                        text(f"""
                    SELECT COUNT(*), MAX(n.created_at)
                    FROM skillkind_member_notification n
                    WHERE n.recipient_id=:sid AND n.kind='requests_in_my_field' AND n.is_read=FALSE
                      AND :enabled AND EXISTS (
                          SELECT 1 {HELPER_MATCH_SQL}
                          AND helper.id=:sid AND p.id=n.help_post_id AND ({DISTANCE_SQL})<=:radius
                      )
                """),
                        {
                            "sid": int(sid),
                            "enabled": field_enabled,
                            "radius": field_radius,
                        },
                    )
                ).first()
                unread_rows = (
                    await asession.execute(
                        text(f"""
                        SELECT kind, COALESCE(target_route, ''), title,
                               community_topic_id, help_post_id,
                               contact_link_id, noncontact_conversation_id
                        FROM skillkind_member_notification
WHERE recipient_id = :sid AND is_read = false
                          AND kind <> 'requests_in_my_field'
                          AND {NOTIFICATION_FILTER}
                        ORDER BY id DESC LIMIT 500
                        """),
                        {"sid": int(sid), **preferences},
                    )
                ).all()
                recent_rows = (
                    await asession.execute(
                        text(f"""
                        SELECT n.id, kind, title, '', is_read,
                               n.created_at, COALESCE(target_route, ''),
                               COALESCE(n.actor_id, 0), COALESCE(s.display_name, 'A member'),
                               COALESCE(pr.avatar_path, ''), COALESCE(community_topic_id, 0),
                               COALESCE(community_comment_id, 0), COALESCE(help_post_id, 0),
                               COALESCE(contact_link_id, 0), COALESCE(noncontact_conversation_id, 0)
                        FROM skillkind_member_notification n
                        LEFT JOIN skillkind_subscriber s ON s.id = n.actor_id
                        LEFT JOIN skillkind_profile pr ON pr.subscriber_id = s.id
                        WHERE recipient_id = :sid AND kind <> 'requests_in_my_field' AND {NOTIFICATION_FILTER}
                        ORDER BY n.created_at DESC, n.id DESC LIMIT 12
                        """),
                        {"sid": int(sid), **preferences},
                    )
                ).all()
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.is_loading = False
                if (await self.get_state(AuthState)).subscriber_id == sid:
                    self.error = (
                        "We couldn't load notifications. Please try again."
                    )
            return
        areas = {"community": 0, "inbox": 0, "help": 0}
        subsections = {"forum": 0, "events": 0, "reviews": 0}
        topic_ids: list[int] = []
        post_ids: list[int] = []
        link_ids: list[int] = []
        conversation_ids: list[int] = []
        for row in unread_rows:
            area, subsection = _classify(
                str(row[0]), str(row[1] or ""), str(row[2] or "")
            )
            areas[area] = areas[area] + 1
            if subsection:
                subsections[subsection] = subsections[subsection] + 1
            if row[3] is not None and int(row[3]) not in topic_ids:
                topic_ids.append(int(row[3]))
            if (
                row[4] is not None
                and area == "help"
                and int(row[4]) not in post_ids
            ):
                post_ids.append(int(row[4]))
            if (
                area == "inbox"
                and row[5] is not None
                and int(row[5]) not in link_ids
            ):
                link_ids.append(int(row[5]))
            if (
                area == "inbox"
                and row[6] is not None
                and int(row[6]) not in conversation_ids
            ):
                conversation_ids.append(int(row[6]))
        async with self:
            if (await self.get_state(AuthState)).subscriber_id != sid:
                self.is_loading = False
                return
            self.community_unread = areas["community"]
            self.inbox_unread = areas["inbox"]
            self.field_unread = (
                int(field_summary[0] or 0) if field_summary else 0
            )
            self.field_created = (
                field_summary[1].strftime("%d %B – %H:%M")
                if field_summary and field_summary[1]
                else ""
            )
            self.help_unread = areas["help"] + self.field_unread
            self.forum_unread = subsections["forum"]
            self.events_unread = subsections["events"]
            self.reviews_unread = subsections["reviews"]
            self.unread_topic_ids = topic_ids
            self.unread_help_post_ids = post_ids
            self.unread_contact_link_ids = link_ids
            self.unread_noncontact_ids = conversation_ids
            self.recent = [
                {
                    "id": int(row[0]),
                    "kind": str(row[1]),
                    "icon": KIND_ICONS.get(str(row[1]), "bell"),
                    "area": (
                        "Reminders"
                        if "reminder" in str(row[1])
                        else _classify(str(row[1]), str(row[6]), str(row[2]))[
                            0
                        ].title()
                    ),
                    "title": concise_text(
                        str(row[1]),
                        str(row[8]),
                        str(row[6]),
                        str(row[2]),
                        int(row[11]),
                    ),
                    "body": "",
                    "actor_id": int(row[7]),
                    "actor_name": str(row[8]),
                    "actor_avatar": str(row[9]),
                    "actor_seed": f"member-{row[7]}",
                    "community_topic_id": int(row[10]),
                    "community_comment_id": int(row[11]),
                    "help_post_id": int(row[12]),
                    "contact_link_id": int(row[13]),
                    "noncontact_conversation_id": int(row[14]),
                    "target_route": str(row[6]),
                    "review_task_id": review_task_id(str(row[6])),
                    "created": (
                        row[5].strftime("%d %B – %H:%M") if row[5] else ""
                    ),
                    "is_read": bool(row[4]),
                }
                for row in recent_rows
            ]
            self.is_loading = False

    @rx.event(background=True)
    async def mark_read(self, notification_id: int):
        """Mark one of my own notifications read — ownership enforced in SQL."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
        if not sid.isdigit():
            return
        async with self:
            if self.read_busy:
                return
            self.read_busy = True
            self.error = ""
        try:
            await self._mark_scoped_read(
                "id = :nid", {"nid": int(notification_id), "sid": int(sid)}
            )
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    "Couldn't mark this notification read. Please try again."
                )
            return
        finally:
            async with self:
                self.read_busy = False
        yield NotificationState.load_notifications

    @rx.event(background=True)
    async def mark_help_read(self):
        """Mark only my unread Help notifications read — nothing else."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            self.help_unread = 0
        if not sid.isdigit():
            return
        kind_params = {
            f"kind_{index}": kind for index, kind in enumerate(HELP_KINDS)
        }
        placeholders = ", ".join(f":{name}" for name in kind_params)
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    f"""
                    UPDATE skillkind_member_notification
                    SET is_read = true, read_at = NOW()
                    WHERE recipient_id = :sid
                      AND is_read = false
                      AND kind IN ({placeholders})
                      AND LOWER(TRIM(COALESCE(target_route, ''))) <> 'community'
                                            AND LOWER(TRIM(COALESCE(target_route, ''))) NOT LIKE 'community:%'
                    """
                ),
                {"sid": int(sid), **kind_params},
            )
            await asession.commit()
        yield NotificationState.load_notifications

    async def _mark_scoped_read(
        self, clause: str, params: dict[str, int]
    ) -> None:
        """Mark only my own unread notifications matching one narrow clause.

        Ownership is always enforced in SQL: `recipient_id = :sid` can never be
        overridden by the caller, and only fixed SQL fragments are spliced in.
        """
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    f"""
                    UPDATE skillkind_member_notification
                    SET is_read = true, read_at = NOW()
                    WHERE recipient_id = :sid
                      AND is_read = false
                      AND {clause}
                    """
                ),
                params,
            )
            await asession.commit()

    @rx.event(background=True)
    async def mark_topic_read(self, topic_id: int):
        """Opening one forum topic clears only that topic's notices."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
        if not sid.isdigit() or int(topic_id) <= 0:
            return
        await self._mark_scoped_read(
            "community_topic_id = :tid",
            {"sid": int(sid), "tid": int(topic_id)},
        )
        yield NotificationState.load_notifications

    @rx.event(background=True)
    async def mark_help_post_read(self, post_id: int):
        """Opening one job conversation clears only that request's notices."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
        if not sid.isdigit() or int(post_id) <= 0:
            return
        await self._mark_scoped_read(
            "help_post_id = :pid",
            {"sid": int(sid), "pid": int(post_id)},
        )
        yield NotificationState.load_notifications

    @rx.event(background=True)
    async def mark_contact_read(self, link_id: int):
        """Opening one contact conversation clears only its notices."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
        if not sid.isdigit() or int(link_id) <= 0:
            return
        await self._mark_scoped_read(
            "contact_link_id = :lid",
            {"sid": int(sid), "lid": int(link_id)},
        )
        yield NotificationState.load_notifications

    @rx.event(background=True)
    async def mark_noncontact_read(self, conversation_id: int):
        """Opening one non-contact conversation clears only its notices."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
        if not sid.isdigit() or int(conversation_id) <= 0:
            return
        await self._mark_scoped_read(
            "noncontact_conversation_id = :cid",
            {"sid": int(sid), "cid": int(conversation_id)},
        )
        yield NotificationState.load_notifications

    @rx.event(background=True)
    async def mark_events_read(self):
        """Entering Community › Events clears only event notices."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            self.events_unread = 0
        if not sid.isdigit():
            return
        await self._mark_scoped_read(
            "kind IN ('help_offer', 'help_confirmed') "
            "AND LOWER(COALESCE(target_route, '')) = 'community'",
            {"sid": int(sid)},
        )
        yield NotificationState.load_notifications

    @rx.event(background=True)
    async def mark_reviews_read(self):
        """Entering Community › Reviews clears only review notices."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            self.reviews_unread = 0
        if not sid.isdigit():
            return
        await self._mark_scoped_read(
            "kind = 'community_like' AND LOWER(title) LIKE '%review%'",
            {"sid": int(sid)},
        )
        yield NotificationState.load_notifications

    @rx.event(background=True)
    async def mark_all_read(self):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
        if not sid.isdigit():
            return
        async with self:
            if self.read_busy:
                return
            self.read_busy = True
            self.error = ""
        try:
            await self._mark_scoped_read("1 = 1", {"sid": int(sid)})
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    "Couldn't mark notifications read. Please try again."
                )
            return
        finally:
            async with self:
                self.read_busy = False
        yield NotificationState.load_notifications
