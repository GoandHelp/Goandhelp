import reflex as rx

import math
import unittest
from unittest.mock import patch

from app import location_privacy as privacy


def great_circle_distance(
    source: tuple[float, float], point: tuple[float, float]
) -> float:
    lat1, lon1 = map(math.radians, source)
    lat2, lon2 = map(math.radians, point)
    a = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 6371.0088 * 2 * math.atan2(math.sqrt(a), math.sqrt(max(0, 1 - a)))


class LocationPrivacyTests(unittest.TestCase):
    wrappers = (
        privacy.profile_approximate,
        privacy.post_member_approximate,
        privacy.post_guest_approximate,
    )

    def test_all_wrappers_distance_determinism_and_final_land_validation(self):
        with patch.object(privacy, "is_land", return_value=True) as land:
            for wrapper in self.wrappers:
                for source in (
                    (51.5, -0.12),
                    (0.0, 179.999),
                    (-33.9, 18.4),
                    (89.89, 20.0),
                ):
                    for record_id in range(1, 301):
                        with self.subTest(
                            wrapper=wrapper.__name__,
                            source=source,
                            record_id=record_id,
                        ):
                            point = wrapper(record_id, *source)
                            self.assertIsNotNone(point)
                            self.assertGreaterEqual(
                                great_circle_distance(source, point), 0.5
                            )
                            self.assertLessEqual(
                                great_circle_distance(source, point), 1.0
                            )
                            self.assertEqual(point, wrapper(record_id, *source))
                            self.assertEqual(land.call_args.args, point)

    def test_omission_when_no_land_or_no_valid_source(self):
        with patch.object(privacy, "is_land", return_value=False):
            for wrapper in self.wrappers:
                self.assertIsNone(wrapper(12, 51.5, -0.12))
        with patch.object(privacy, "is_land", return_value=True):
            for wrapper in self.wrappers:
                for source in (
                    (None, 0.0),
                    (0.0, None),
                    (float("nan"), 0.0),
                    (91.0, 0.0),
                ):
                    self.assertIsNone(wrapper(12, *source))

    def test_search_continues_past_water(self):
        for wrapper in self.wrappers:
            with patch.object(
                privacy, "is_land", side_effect=[False, False, True]
            ) as land:
                point = wrapper(12, 51.5, -0.12)
                self.assertIsNotNone(point)
                self.assertEqual(land.call_count, 3)
                self.assertEqual(land.call_args.args, point)
                self.assertTrue(
                    0.5 <= great_circle_distance((51.5, -0.12), point) <= 1.0
                )

    def test_audiences_retain_separate_salts(self):
        with patch.object(privacy, "is_land", return_value=True):
            points = {wrapper(42, 51.5, -0.12) for wrapper in self.wrappers}
            self.assertEqual(len(points), 3)

    def test_real_inland_mask(self):
        source = (48.8566, 2.3522)
        for wrapper in self.wrappers:
            point = wrapper(42, *source)
            self.assertIsNotNone(point)
            self.assertTrue(privacy.is_land(*point))
            self.assertTrue(0.5 <= great_circle_distance(source, point) <= 1.0)


if __name__ == "__main__":
    unittest.main()
