"""Unit tests for helper functions in src/main.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from main import aspect_fit


class TestAspectFit:
    def test_4_3_sensor_wide_container(self) -> None:
        w, h = aspect_fit(4056, 3040, 800, 600)
        # Should be constrained by height: w = 600 * (4056/3040) ≈ 800
        assert w <= 800
        assert h <= 600
        # Check ratio is preserved within 1px rounding
        assert abs(w / h - 4056 / 3040) < 0.01

    def test_4_3_sensor_tall_container(self) -> None:
        w, h = aspect_fit(4056, 3040, 400, 600)
        assert w <= 400
        assert h <= 600
        assert abs(w / h - 4056 / 3040) < 0.01

    def test_exact_fit(self) -> None:
        w, h = aspect_fit(4, 3, 400, 300)
        assert w == 400
        assert h == 300

    def test_square_sensor(self) -> None:
        w, h = aspect_fit(1000, 1000, 300, 200)
        assert w == h == 200

    def test_imx477_in_poc_container(self) -> None:
        # Container: 573×366 from the original PoC (before fix)
        w, h = aspect_fit(4056, 3040, 573, 366)
        assert w <= 573
        assert h <= 366
        # The corrected preview should be 4:3 ≈ 488×366
        assert abs(w / h - 4056 / 3040) < 0.01
