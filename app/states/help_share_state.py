import reflex as rx

import logging
import re
from urllib.parse import urlencode
from sqlalchemy import text
from app.verification import public_base_url


def parse_shared_help(value: object) -> int:
    if not isinstance(value, str) or not re.fullmatch(
        r"[1-9][0-9]{0,18}", value
    ):
        return 0
    number = int(value)
    return number if number <= 9223372036854775807 else 0


def share_links(
    post_id: int, title: str, router_url: str
) -> tuple[str, list[dict[str, str]]]:
    url = (
        f"{public_base_url(router_url)}/?{urlencode({'shared_help': post_id})}"
    )
    message = f"Can you help? {' '.join(title.split())[:160]} — Go and Help"
    body = f"{message}\n{url}"
    return url, [
        {
            "label": "WhatsApp",
            "href": f"https://wa.me/?{urlencode({'text': body})}",
        },
        {
            "label": "Telegram",
            "href": f"https://t.me/share/url?{urlencode({'url': url, 'text': message})}",
        },
        {
            "label": "Facebook",
            "href": f"https://www.facebook.com/sharer/sharer.php?{urlencode({'u': url, 'quote': message})}",
        },
        {
            "label": "X",
            "href": f"https://twitter.com/intent/tweet?{urlencode({'url': url, 'text': message})}",
        },
        {
            "label": "Email",
            "href": f"mailto:?{urlencode({'subject': message, 'body': body})}",
        },
    ]


class HelpShareState(rx.State):
    active_key: str = ""
    url: str = ""
    links: list[dict[str, str]] = []
    pending: str = rx.LocalStorage("", name="gah_shared_help")
    _handled: str = ""

    @rx.event
    async def toggle(self, post_id: int, title: str, context: str):
        key = f"{context}-{post_id}"
        if self.active_key == key:
            self.active_key = ""
            return
        if parse_shared_help(str(post_id)) == 0:
            return
        try:
            self.url, self.links = share_links(
                post_id, title, str(self.router.url)
            )
            self.active_key = key
        except Exception as e:
            logging.exception(f"Error: {e}")
            return rx.toast(
                "Sharing is unavailable right now. Please try again."
            )

    @rx.event
    def close(self):
        self.active_key = ""

    @rx.event
    async def resolve(self):
        from app.states.auth_state import AuthState
        from app.states.guest_map_state import GuestMapState
        from app.states.discovery_state import DiscoveryState

        auth = await self.get_state(AuthState)
        if auth.checking_session:
            return
        raw = self.router.url.query_parameters.get("shared_help", self.pending)
        post_id = parse_shared_help(raw)
        if not post_id:
            return
        identity = auth.subscriber_id if auth.is_signed_in else "guest"
        handled = f"{identity}:{post_id}"
        if self._handled == handled:
            return
        try:
            async with rx.asession() as session:
                exists = (
                    await session.execute(
                        text("""
                    SELECT p.id FROM skillkind_help_post p
                    WHERE p.id = :pid AND p.status = 'open'
                      AND (p.expires_at IS NULL OR p.expires_at > now())
                      AND (SELECT COUNT(*) FROM skillkind_job_application a
                           WHERE a.post_id = p.id AND a.status = 'accepted')
                          < GREATEST(COALESCE(p.helpers_needed, 1), 1)
                    LIMIT 1
                """),
                        {"pid": post_id},
                    )
                ).first()
        except Exception as e:
            logging.exception(f"Error: {e}")
            return rx.toast(
                "We couldn't open that shared request. Please try again."
            )
        self._handled = handled
        if not exists:
            self.pending = ""
            return rx.toast(
                "That shared request is no longer available. You can still explore the map."
            )
        self.pending = str(post_id)
        if auth.is_signed_in:
            self.pending = ""
            return DiscoveryState.open_shared_post(post_id)
        guest = await self.get_state(GuestMapState)
        guest.wall_open = True
        guest.wall_reason = (
            "You've been invited to help on Go and Help! Sign in or register to view "
            "the request and offer a hand. You can also install/download Go and Help "
            "from your browser or device menu when supported: look for Install app "
            "or Add to Home Screen. You can always continue in your browser."
        )
