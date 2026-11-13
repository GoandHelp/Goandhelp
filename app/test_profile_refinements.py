import reflex as rx

import unittest

from test_utils import run_event
from app.states.community_state import CommunityState
from app.states.profile_state import ProfileState


class ProfileRefinementTests(unittest.IsolatedAsyncioTestCase):
    async def test_rating_shortcut_through_event_system(self):
        profile = ProfileState(
            active_tab="profile",
            current_city="Porto",
            location_mode="approximate",
            latitude="41.157944",
            longitude="-8.629105",
        )
        community = await profile.get_state(CommunityState)
        for section in ("community", "events", "reviews"):
            profile.active_tab = "profile"
            profile.location_open = True
            profile.blocked_open = True
            profile.error = "Previous feedback"
            profile.success = "Profile details saved."
            community.section = section
            community.error = "Previous community feedback"
            await run_event(profile.open_reviews)
            self.assertEqual(profile.active_tab, "community")
            self.assertEqual(community.section, "reviews")
            self.assertEqual(profile.error, "")
            self.assertEqual(profile.success, "")
            self.assertEqual(community.error, "")
            self.assertFalse(profile.location_open)
            self.assertTrue(profile.blocked_open)

    async def test_location_summary_keeps_coordinate_data(self):
        profile = ProfileState(
            active_tab="profile", current_city="", location_mode="hidden"
        )
        self.assertEqual(
            profile.location_card_summary,
            "No city set yet – Address and map",
        )
        profile.current_city = "Porto"
        profile.location_mode = "approximate"
        profile.latitude = "41.157944"
        profile.longitude = "-8.629105"
        self.assertEqual(
            profile.location_card_summary,
            "Porto – Address and map",
        )
        self.assertEqual(profile.coordinates_value, "41.157944, -8.629105")
        profile.location_mode = "hidden"
        profile.current_city = "  Porto  "
        self.assertEqual(
            profile.location_card_summary, "Porto – Address and map"
        )
        profile.current_city = "   "
        self.assertEqual(
            profile.location_card_summary, "No city set yet – Address and map"
        )


if __name__ == "__main__":
    unittest.main()
