import reflex as rx

import math
from unittest.mock import patch
from app.location_privacy import _distance_km
import unittest
from types import SimpleNamespace

from app.states.guest_map_state import (
    GuestMapState,
    _public_job,
    _reference_code,
)


class GuestMapCoordinateTests(unittest.TestCase):
    def test_arbitrary_codes_are_deterministic_and_bounded(self):
        with patch("app.location_privacy.is_land", return_value=True):
            for identifier in range(100):
                row = (identifier, "Request", "x" * 200, 51.5, -0.12)
                job = _public_job(row)
                self.assertEqual(job, _public_job(row))
                self.assertEqual(len(job["description"]), 100)
                distance = _distance_km(51.5, -0.12, job["lat"], job["lng"])
                self.assertGreaterEqual(distance, 0.5)
                self.assertLessEqual(distance, 1.0)

    def test_marker_computation_preserves_title_only_payload_and_ids(self):
        self.assertTrue(issubclass(GuestMapState, rx.State))
        references = [_reference_code(i) for i in range(1000)]
        codes = [*references, "A1B2", "", "not-hex", "邻里互助 🤝"]
        jobs = [
            {
                "code": code,
                "title": "Test request",
                "description": "Preview",
                "lng": 2.3,
                "lat": 48.8,
            }
            for code in codes
        ]
        # Invoke the getter directly: constructor kwargs can leave jobs empty.
        state = SimpleNamespace(jobs=jobs, helpers=[], browse_mode="give")
        markers = GuestMapState.map_markers.fget(state)
        self.assertEqual(len(markers), len(jobs))
        self.assertEqual(markers, GuestMapState.map_markers.fget(state))
        self.assertEqual([marker["id"] for marker in markers], codes)
        self.assertEqual(len({marker["id"] for marker in markers[:1000]}), 1000)
        for job, marker in zip(jobs, markers, strict=True):
            with self.subTest(code=job["code"]):
                longitude, latitude = job["lng"], job["lat"]
                self.assertEqual(
                    marker,
                    {
                        "id": job["code"],
                        "lng": longitude,
                        "lat": latitude,
                        "label": job["title"],
                        "kind": "job",
                        "selected": False,
                        "icon": "hand-helping",
                        "color": "#fba922",
                        "image_url": "",
                    },
                )
                self.assertTrue(math.isfinite(marker["lng"]))
                self.assertTrue(math.isfinite(marker["lat"]))
                self.assertLessEqual(-2.0, marker["lng"])
                self.assertLessEqual(marker["lng"], 22.0)
                self.assertLessEqual(40.5, marker["lat"])
                self.assertLessEqual(marker["lat"], 52.5)

    def test_empty_jobs_still_produce_no_markers(self):
        self.assertEqual(
            GuestMapState.map_markers.fget(
                SimpleNamespace(jobs=[], helpers=[], browse_mode="give")
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
