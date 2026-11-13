"""View state for the Find People noticeboard (search + contact requests)."""

from typing import Any

import reflex as rx


class FindPeopleState(rx.State):
    """Which traveller card is expanded, and the request form draft."""

    expanded_id: int = 0

    @rx.event
    def toggle_expanded(self, person_id: int):
        self.expanded_id = 0 if self.expanded_id == person_id else person_id

    @rx.event
    def collapse(self):
        self.expanded_id = 0

    @rx.event
    def submit_request(self, form_data: dict[str, Any]):
        """Send a contact request for the currently expanded traveller."""
        from app.states.contacts_state import ContactsState

        person_id = self.expanded_id
        note = str(form_data.get("note", "") or "").strip()
        if person_id <= 0:
            return
        self.expanded_id = 0
        yield ContactsState.send_request(person_id, note)

    @rx.event
    def quick_request(self, person_id: int):
        from app.states.contacts_state import ContactsState

        if person_id <= 0:
            return
        self.expanded_id = 0
        yield ContactsState.send_request(person_id, "")
