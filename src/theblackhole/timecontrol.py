"""Simulation speed: pause, faster and slower."""

from .config import TIME_SCALE_MAX, TIME_SCALE_MIN


class TimeControl:
    """Pause and speed of the simulation clock."""

    def __init__(self) -> None:
        self.scale = 1.0
        self.paused = False

    def toggle_pause(self) -> None:
        """Pause or resume the simulation."""
        self.paused = not self.paused

    def faster(self) -> None:
        """Double the simulation speed (up to the maximum)."""
        self.scale = min(TIME_SCALE_MAX, self.scale * 2)

    def slower(self) -> None:
        """Halve the simulation speed (down to the minimum)."""
        self.scale = max(TIME_SCALE_MIN, self.scale / 2)

    def scaled(self, dt: float) -> float:
        """Simulation time that passes during a real frame of `dt` seconds."""
        return 0.0 if self.paused else dt * self.scale

    def label(self) -> str:
        """Speed as shown in the HUD, e.g. 'x2' or 'x1/4 (PAUSED)'."""
        speed = f"x{self.scale:g}" if self.scale >= 1 else f"x1/{1 / self.scale:g}"
        return f"{speed} (PAUSED)" if self.paused else speed
