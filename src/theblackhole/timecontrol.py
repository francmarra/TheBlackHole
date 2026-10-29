"""Simulation speed: pause, faster and slower."""

from .config import TIME_SCALE_MAX, TIME_SCALE_MIN


class TimeControl:
    def __init__(self):
        self.scale = 1.0
        self.paused = False

    def toggle_pause(self):
        self.paused = not self.paused

    def faster(self):
        self.scale = min(TIME_SCALE_MAX, self.scale * 2)

    def slower(self):
        self.scale = max(TIME_SCALE_MIN, self.scale / 2)

    def scaled(self, dt):
        """Simulation time that passes during a real frame of `dt` seconds."""
        return 0.0 if self.paused else dt * self.scale

    def label(self):
        speed = f"x{self.scale:g}" if self.scale >= 1 else f"x1/{1 / self.scale:g}"
        return f"{speed} (PAUSED)" if self.paused else speed
