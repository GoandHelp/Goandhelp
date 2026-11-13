"""Which in-app handbook / policy screen is open, if any."""

import reflex as rx

from app.policies import (
    POLICY_DOCUMENTS,
    PolicySection,
)


class PolicyState(rx.State):
    """A single full-screen policy reader shared by every entry point."""

    open_key: str = ""
    title: str = ""
    subtitle: str = ""
    icon: str = "book-open"
    updated: str = ""
    notice: str = ""
    sections: list[PolicySection] = []

    @rx.var
    def is_open(self) -> bool:
        return self.open_key != ""

    @rx.event
    def open_policy(self, key: str):
        document = POLICY_DOCUMENTS.get(key)
        if document is None:
            return
        self.open_key = document["key"]
        self.title = document["title"]
        self.subtitle = document["subtitle"]
        self.icon = document["icon"]
        self.updated = document["updated"]
        self.notice = document["notice"]
        self.sections = list(document["sections"])

    @rx.event
    def close_policy(self):
        self.open_key = ""
        self.title = ""
        self.subtitle = ""
        self.icon = "book-open"
        self.updated = ""
        self.notice = ""
        self.sections = []
