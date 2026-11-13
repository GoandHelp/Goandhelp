import reflex as rx

import concurrent.futures
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from app import location_privacy as privacy


class LandMaskLoadingTests(unittest.TestCase):
    def test_streamed_mask_matches_original_cells_and_grid_indices(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "globe_combined_mask_compressed.npz"
            lat = np.linspace(90, -90, 5)
            lon = np.linspace(-180, 180, 300003)
            water = (
                np.random.default_rng(7)
                .integers(0, 2, size=(len(lat), len(lon)), dtype=np.uint8)
                .astype(bool)
            )
            np.savez_compressed(archive, lat=lat, lon=lon, mask=water)
            distribution = SimpleNamespace(
                files=[Path(archive.name)],
                locate_file=lambda path: archive,
            )
            with patch.object(
                privacy.importlib.metadata,
                "distribution",
                return_value=distribution,
            ):
                mask = privacy._PackedLandMask()
            self.assertEqual(len(mask._bits), (water.size + 7) // 8)
            for index in (0, 7, 8, 1048575, 1048576, water.size - 1):
                row, column = divmod(index, len(lon))
                stored = bool(mask._bits[index // 8] & (1 << (7 - index % 8)))
                self.assertEqual(stored, bool(water[row, column]))
            for latitude, longitude in (
                (48.8, 2.3),
                (0, 0),
                (-90, 180),
                (90, -180),
            ):
                row = int((latitude - lat[0]) / (lat[1] - lat[0]))
                column = int((longitude - lon[0]) / (lon[1] - lon[0]))
                self.assertEqual(
                    mask.is_land(latitude, longitude), not water[row, column]
                )

    def test_concurrent_first_checks_build_only_one_mask(self):
        privacy._packed_globe.cache_clear()
        try:
            with patch.object(privacy, "_PackedLandMask") as constructor:
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=8
                ) as pool:
                    results = list(
                        pool.map(lambda _: privacy._globe(), range(32))
                    )
                constructor.assert_called_once()
                self.assertTrue(all(result is results[0] for result in results))
        finally:
            privacy._packed_globe.cache_clear()

    def test_dataset_failure_keeps_location_private(self):
        with patch.object(
            privacy, "_globe", side_effect=ValueError("Invalid dataset")
        ):
            with self.assertLogs(level="ERROR"):
                self.assertFalse(privacy.is_land(48.8, 2.3))

    def test_real_first_map_lookup_has_bounded_peak_memory(self):
        script = """
import json
import resource
import sys
import numpy
from app import location_privacy as privacy
before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
for wrapper in (privacy.profile_approximate, privacy.post_member_approximate, privacy.post_guest_approximate):
    point = wrapper(42, 48.8566, 2.3522)
    assert point is not None and privacy.is_land(*point)
    assert 0.5 <= privacy._distance_km(48.8566, 2.3522, *point) <= 1.0
    assert point == wrapper(42, 48.8566, 2.3522)
assert not any(name == 'global_land_mask' or name.startswith('global_land_mask.') for name in sys.modules)
after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(json.dumps({'peak_growth_kib': after - before}))
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=120,
            check=True,
        )
        measurements = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertLess(measurements["peak_growth_kib"], 220 * 1024)


if __name__ == "__main__":
    unittest.main()
