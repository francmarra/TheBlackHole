"""Save and load the state of a scenario as JSON."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from .aliases import Color, Vector

FORMAT_VERSION = 1
SCENES = ("solar", "blackhole", "galaxy")


class ScenarioError(ValueError):
    """A save file that is missing, malformed or has invalid values."""


def save(path: Path, scene: str, data: dict[str, Any], time_scale: float) -> None:
    """Write `data` (from a scene's `to_dict`) to `path`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    document = {"version": FORMAT_VERSION, "scene": scene, "time_scale": time_scale, "data": data}
    path.write_text(json.dumps(document, indent=1), encoding="utf-8")


def load(path: Path) -> dict[str, Any]:
    """Read a saved scenario; raises ScenarioError if the file is not one."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ScenarioError(f"{path.name} is not valid JSON: {error}") from error
    if not isinstance(document, dict) or document.get("version") != FORMAT_VERSION:
        raise ScenarioError(f"{path.name} is not a TheBlackHole save (version {FORMAT_VERSION})")
    if document.get("scene") not in SCENES or not isinstance(document.get("data"), dict):
        raise ScenarioError(f"{path.name} has an unknown scene")
    document["time_scale"] = number(document.get("time_scale", 1.0), "time_scale", positive=True)
    return document


# Validation helpers for values read from a file


def number(value: object, name: str, positive: bool = False) -> float:
    """A finite float (and > 0 if `positive`)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ScenarioError(f"{name} must be a finite number")
    if positive and value <= 0:
        raise ScenarioError(f"{name} must be positive")
    return float(value)


def vector(value: object, name: str) -> Vector:
    """A 3D vector of finite floats."""
    if not isinstance(value, list) or len(value) != 3:
        raise ScenarioError(f"{name} must be a list of 3 numbers")
    return np.array([number(v, name) for v in value])


def color(value: object, name: str) -> Color:
    """An (r, g, b) colour with components 0-255."""
    if not isinstance(value, list) or len(value) != 3:
        raise ScenarioError(f"{name} must be a list of 3 numbers")
    r, g, b = (int(min(255, max(0, number(v, name)))) for v in value)
    return r, g, b


def array(value: object, name: str, rows: int | None = None) -> Vector:
    """An (N, 3) array of finite floats."""
    try:
        result = np.array(value, dtype=float)
    except (TypeError, ValueError) as error:
        raise ScenarioError(f"{name} must be a list of [x, y, z]") from error
    if result.ndim != 2 or result.shape[1] != 3 or (rows is not None and len(result) != rows):
        raise ScenarioError(f"{name} must be a list of [x, y, z]" + (f" with {rows} rows" if rows else ""))
    if not np.isfinite(result).all():
        raise ScenarioError(f"{name} must only contain finite numbers")
    return result
