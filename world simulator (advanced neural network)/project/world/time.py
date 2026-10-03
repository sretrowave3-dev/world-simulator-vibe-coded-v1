"""
project/world/time.py

Celestial Timekeeper, Diurnal Cycle & Orbital Seasons Engine for the ALife Platform.

Features:
- Fixed-timestep temporal progression (Ticks -> Seconds -> Days -> Seasons -> Years -> Epochs).
- Solar declination, orbital insolation factor, and day/night cycle illumination factor.
- Calendar tracking and event timestamp generation.
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


class Season(enum.IntEnum):
    SPRING = 0
    SUMMER = 1
    AUTUMN = 2
    WINTER = 3


@dataclass(frozen=True, slots=True)
class TimeSnapshot:
    tick: int
    seconds: float
    day: int
    day_fraction: float  # 0.0 (midnight) to 0.5 (noon) to 1.0 (midnight)
    season: Season
    year: int
    daylight_factor: float     # 0.0 (night) to 1.0 (peak daylight)
    insolation_factor: float   # 0.5 (winter) to 1.5 (summer)
    solar_angle_rad: float     # Angle of sun above horizon


class WorldTimeManager:
    """
    Master celestial clock driving temporal progression and orbital illumination.
    """

    def __init__(
        self,
        seconds_per_day: float = 120.0,
        days_per_year: int = 360,
        ticks_per_second: int = 60,
    ) -> None:
        self.seconds_per_day = seconds_per_day
        self.days_per_year = days_per_year
        self.ticks_per_second = ticks_per_second

        self.current_tick: int = 0
        self.total_seconds: float = 0.0

    def tick(self, dt: float) -> None:
        self.current_tick += 1
        self.total_seconds += dt

    @property
    def total_days(self) -> float:
        return self.total_seconds / self.seconds_per_day

    @property
    def current_day(self) -> int:
        return int(math.floor(self.total_days))

    @property
    def day_fraction(self) -> float:
        return (self.total_seconds % self.seconds_per_day) / self.seconds_per_day

    @property
    def current_year(self) -> int:
        return int(math.floor(self.total_days / self.days_per_year))

    @property
    def day_of_year(self) -> int:
        return self.current_day % self.days_per_year

    @property
    def current_season(self) -> Season:
        season_len = self.days_per_year / 4.0
        season_idx = int(self.day_of_year / season_len) % 4
        return Season(season_idx)

    @property
    def solar_angle_rad(self) -> float:
        """Solar elevation angle: peaks at noon (pi/2) and goes below 0 at night."""
        # Fraction 0.0 -> Midnight (-pi/2), 0.25 -> Sunrise (0), 0.5 -> Noon (pi/2), 0.75 -> Sunset (0)
        return math.sin(self.day_fraction * 2.0 * math.pi - math.pi * 0.5)

    @property
    def daylight_factor(self) -> float:
        """Normalized ambient daylight factor [0.0 (pitch black) to 1.0 (full daylight)]."""
        sin_val = math.sin((self.day_fraction - 0.25) * 2.0 * math.pi)
        # Smooth ramp around sunrise/sunset
        return max(0.0, min(1.0, (sin_val + 0.2) * 1.5))

    @property
    def insolation_factor(self) -> float:
        """Orbital seasonal solar flux factor [0.7 to 1.3]."""
        orbital_phase = (self.day_of_year / self.days_per_year) * 2.0 * math.pi
        return 1.0 + 0.3 * math.sin(orbital_phase - math.pi * 0.5)

    @property
    def is_daylight(self) -> bool:
        return self.daylight_factor > 0.15

    def get_sun_properties(self) -> Dict[str, Any]:
        """Calculates dynamic solar illumination, sun disc color, and ambient lighting tint."""
        df = self.daylight_factor
        frac = self.day_fraction  # 0.0 (midnight) -> 0.25 (sunrise) -> 0.5 (noon) -> 0.75 (sunset)

        # Solar Lux: 0 (night) to 100,000 (clear noon sunlight)
        solar_lux = df * 100000.0 * self.insolation_factor

        # Determine sun disc color and ambient atmospheric tint based on diurnal progression
        if 0.20 <= frac < 0.32:
            # Golden Sunrise / Dawn
            prog = (frac - 0.20) / 0.12
            sun_color = (255, int(150 + prog * 90), int(40 + prog * 160))
            ambient_tint = (int(160 + prog * 80), int(120 + prog * 120), int(90 + prog * 140))
            phase_name = "DAWN"
        elif 0.32 <= frac < 0.68:
            # Midday Brilliant Sun
            sun_color = (255, 250, 220)
            ambient_tint = (245, 248, 255)
            phase_name = "MIDDAY"
        elif 0.68 <= frac < 0.80:
            # Crimson/Amber Sunset
            prog = (frac - 0.68) / 0.12
            sun_color = (255, int(220 - prog * 120), int(180 - prog * 140))
            ambient_tint = (int(230 - prog * 130), int(160 - prog * 100), int(140 - prog * 70))
            phase_name = "DUSK"
        else:
            # Night with Moonlight
            sun_color = (180, 205, 255)  # Silver moonlight
            ambient_tint = (25, 30, 55)
            phase_name = "NIGHT"

        # Sun sky position (X: East to West [0.0 to 1.0], Y: Horizon parabola)
        sun_sky_x = (frac - 0.20) / 0.60  # 0.0 at dawn, 0.5 at noon, 1.0 at sunset
        sun_sky_y = math.sin(max(0.0, min(1.0, sun_sky_x)) * math.pi) if (0.20 <= frac <= 0.80) else 0.0

        return {
            "day_fraction": frac,
            "daylight_factor": df,
            "phase": phase_name,
            "solar_lux": solar_lux,
            "is_daylight": self.is_daylight,
            "sun_color_rgb": sun_color,
            "ambient_tint_rgb": ambient_tint,
            "sun_sky_x": sun_sky_x,
            "sun_sky_y": sun_sky_y,
            "insolation": self.insolation_factor,
        }

    def get_snapshot(self) -> TimeSnapshot:
        return TimeSnapshot(
            tick=self.current_tick,
            seconds=self.total_seconds,
            day=self.current_day,
            day_fraction=self.day_fraction,
            season=self.current_season,
            year=self.current_year,
            daylight_factor=self.daylight_factor,
            insolation_factor=self.insolation_factor,
            solar_angle_rad=self.solar_angle_rad,
        )

    def reset(self) -> None:
        self.current_tick = 0
        self.total_seconds = 0.0
