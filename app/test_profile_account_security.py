import reflex as rx

import ast
import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.components import profile_tabs as ui, onboarding
from app.states.profile_state import ProfileState
from app.states.onboarding_state import OnboardingState, COUNTRY_OPTIONS
from app.states.auth_state import hash_password


class StateHarness(SimpleNamespace):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get_state(self, cls):
        return self.auth


def walk(component):
    yield component
    for child in component.children:
        yield from walk(child)


class ProfileAccountComponents(unittest.TestCase):
    def test_native_required_terms_custom_box(self):
        from app.components.auth_panel import register_form

        form = register_form()
        self.assertTrue(form.render())
        fields = [
            c
            for c in walk(form)
            if c.tag == "input" and str(c.type).strip('"') == "checkbox"
        ]
        self.assertEqual(len(fields), 1)
        checkbox = fields[0]
        self.assertEqual(str(checkbox.name).strip('"'), "terms_consent")
        self.assertEqual(str(checkbox.required), "true")
        self.assertNotIn("on_change", checkbox.event_triggers)
        checkbox_classes = str(checkbox.class_name)
        for token in (
            "peer absolute inset-0",
            "h-full w-full",
            "opacity-0",
            "cursor-pointer",
        ):
            self.assertIn(token, checkbox_classes)
        self.assertNotIn("sr-only", checkbox_classes)
        source = inspect.getsource(register_form)
        for token in (
            "border-black! bg-white",
            "peer-checked:bg-[#fba922]",
            "text-black",
            "[&>svg]:invisible",
            "peer-checked:[&>svg]:visible",
            "peer-focus-visible:outline-2",
            'default_value="accepted"',
            "on_submit=AuthState.register",
            "I agree to the Terms and User Agreement (required)",
        ):
            self.assertIn(token, source)

    def test_separate_forms_and_inputs(self):
        wrapper = ui.details_tab()
        self.assertTrue(wrapper.render())
        self.assertEqual(wrapper.tag, "div")
        self.assertEqual(len(wrapper.children), 2)
        details, password = wrapper.children
        self.assertIn("Languages", str(details))
        self.assertNotIn("current_password", str(details))
        self.assertIn("Change password", str(password))
        self.assertFalse(
            any(c.tag == "form" for c in walk(details) if c is not details)
        )
        self.assertFalse(
            any(c.tag == "form" for c in walk(password) if c is not password)
        )
        inputs = [c for c in walk(password) if c.tag == "input"]
        self.assertEqual(len(inputs), 3)
        for field, autocomplete, minimum in zip(
            inputs,
            ["current-password", "new-password", "new-password"],
            [1, 6, 6],
        ):
            self.assertEqual(str(field.type).strip('"'), "password")
            self.assertEqual(str(field.auto_complete).strip('"'), autocomplete)
            self.assertEqual(str(field.min_length), str(minimum))
            self.assertNotIn("on_change", field.event_triggers)
        self.assertIn(
            "reset_on_submit=True", inspect.getsource(ui.change_password_form)
        )
        self.assertIn("Password", str(ui.my_information_section()))

    def test_hero_and_verification(self):
        hero = inspect.getsource(ui.identity_passport)
        self.assertNotIn("credential_chips", hero)
        self.assertIn("nationality_flag", hero)
        self.assertIn("handle_label", hero)
        guidance = ui.verification_guidance()
        self.assertTrue(guidance.render())
        self.assertEqual(len(guidance.children[1].children), 1)
        self.assertNotIn("What we will never do", str(guidance))
        self.assertNotIn("We will not capture", str(guidance))
        self.assertIn("What the verification tick means", str(guidance))
        self.assertIn("Get verified - ", str(guidance))
        self.assertIn("Get more opportunities", str(guidance))

    def test_nationality_contract(self):
        country = onboarding.country_screen()
        selects = [c for c in walk(country) if c.tag == "select"]
        self.assertEqual(len(selects), 1)
        self.assertNotIn(
            "multiple=True", inspect.getsource(onboarding.country_screen)
        )
        state = OnboardingState(_reflex_internal_init=True)
        state.is_complete = False
        state.saving = False
        state.first_request_post_id = 0
        OnboardingState.choose_country.fn(state, COUNTRY_OPTIONS[0])
        for invalid in ("Atlantis", "", "France,Germany"):
            OnboardingState.choose_country.fn(state, invalid)
            self.assertEqual(state.home_country, COUNTRY_OPTIONS[0])
        state.is_complete = True
        OnboardingState.choose_country.fn(state, COUNTRY_OPTIONS[-1])
        self.assertEqual(state.home_country, COUNTRY_OPTIONS[0])
        finish = inspect.getsource(OnboardingState._finish)
        self.assertIn("home_country = :country, nationality = :country", finish)
        self.assertIn(
            "home_city, home_country, nationality, current_city", finish
        )
        self.assertIn(":country, :country, ''", finish)
        self.assertEqual(finish.count('"country": country'), 2)
        summary_state = OnboardingState(_reflex_internal_init=True)
        summary_state.home_country = COUNTRY_OPTIONS[0]
        self.assertTrue(
            any(
                row["label"] == "Nationality"
                and row["value"] == summary_state.home_country
                for row in summary_state.summary_rows
            )
        )
        load = inspect.getsource(ProfileState._load_profile_data)
        self.assertIn(
            'str(profile_row[20] or "").strip() or self.home_country', load
        )
        for handler in (
            ProfileState.save_details,
            ProfileState.save_area,
            ProfileState.save_skills,
        ):
            self.assertNotIn("nationality", inspect.getsource(handler.fn))
        self.assertNotIn('name="nationality"', inspect.getsource(ui))
        self.assertIn('name="home_country"', inspect.getsource(ui.details_tab))

    def test_only_feedback_password_state_and_clear(self):
        tree = ast.parse(inspect.getsource(ProfileState))
        fields = {
            node.target.id
            for node in tree.body[0].body
            if isinstance(node, ast.AnnAssign)
        }
        self.assertEqual(
            {f for f in fields if "password" in f},
            {"password_error", "password_success", "password_busy"},
        )
        state = ProfileState(_reflex_internal_init=True)
        state.password_busy = True
        state.password_error = "error"
        state.password_success = "success"
        ProfileState.clear_profile.fn(state)
        self.assertEqual(state.password_error, "")
        self.assertEqual(state.password_success, "")
        self.assertFalse(state.password_busy)


class PasswordTransactions(unittest.IsolatedAsyncioTestCase):
    async def run_change(
        self, data=None, sid="42", signed_in=True, matched=True, fail=False
    ):
        state = StateHarness(
            auth=SimpleNamespace(
                subscriber_id=sid,
                is_signed_in=signed_in,
                preferred_language="en",
            ),
            password_busy=False,
            password_error="",
            password_success="old",
        )
        session = MagicMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        result = MagicMock()
        result.first.return_value = (42,) if matched else None
        session.execute = AsyncMock(return_value=result)
        if fail:
            session.execute.side_effect = RuntimeError("database unavailable")
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        data = (
            data
            if data is not None
            else {
                "current_password": "old-secret",
                "new_password": "new-secret",
                "confirm_password": "new-secret",
                "sid": "999",
            }
        )
        with (
            patch("app.states.profile_state.rx.asession", return_value=session),
            patch("app.states.profile_state.logging.exception"),
        ):
            events = []
            async for event in ProfileState.change_password.fn(state, data):
                events.append(event)
        return state, session, events

    async def test_success_conditional_update_and_invalidation(self):
        state, session, events = await self.run_change()
        self.assertFalse(state.password_busy)
        self.assertEqual(state.password_error, "")
        self.assertTrue(state.password_success)
        self.assertEqual(len(events), 1)
        calls = session.execute.call_args_list
        self.assertEqual(len(calls), 2)
        sql, params = calls[0].args
        sql = " ".join(str(sql).split())
        self.assertIn(
            "WHERE id = :sid AND password_hash = :current_hash AND is_active = TRUE RETURNING id",
            sql,
        )
        self.assertEqual(
            params,
            {
                "sid": 42,
                "current_hash": hash_password("old-secret"),
                "new_hash": hash_password("new-secret"),
            },
        )
        self.assertNotIn("old-secret", sql)
        token_sql, token_params = calls[1].args
        self.assertIn("skillkind_password_reset_token", str(token_sql))
        self.assertIn("used_at IS NULL", str(token_sql))
        self.assertIn("invalidated_at = now()", str(token_sql))
        self.assertEqual(token_params, {"sid": 42})
        session.commit.assert_awaited_once()
        session.rollback.assert_not_awaited()

    async def test_wrong_current_and_failure_rollback(self):
        state, session, events = await self.run_change(matched=False)
        self.assertEqual(state.password_error, "Current password is incorrect.")
        self.assertEqual(session.execute.await_count, 1)
        session.commit.assert_not_awaited()
        session.rollback.assert_awaited_once()
        self.assertFalse(events)
        state, session, events = await self.run_change(fail=True)
        self.assertIn("couldn't save", state.password_error)
        self.assertFalse(state.password_busy)
        self.assertFalse(state.password_success)
        session.rollback.assert_awaited_once()
        session.commit.assert_not_awaited()

    async def test_validation_without_database(self):
        for current, password, confirm in [
            ("", "abcdef", "abcdef"),
            ("secret", "short", "short"),
            ("secret", "abcdef", "different"),
            ("secret", "secret", "secret"),
        ]:
            state, session, events = await self.run_change(
                {
                    "current_password": current,
                    "new_password": password,
                    "confirm_password": confirm,
                }
            )
            self.assertTrue(state.password_error)
            self.assertFalse(state.password_success)
            self.assertFalse(state.password_busy)
            session.execute.assert_not_awaited()
        for sid, signed_in in [
            ("", False),
            ("not-numeric", True),
            ("42", False),
            ("²", True),
        ]:
            state, session, events = await self.run_change(
                sid=sid, signed_in=signed_in
            )
            self.assertIn("sign in", state.password_error)
            session.execute.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
