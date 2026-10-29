"""Type aliases shared by the modules."""

from collections.abc import Callable

import numpy as np
from numpy.typing import ArrayLike, NDArray

__all__ = ["ArrayLike", "Color", "Lens", "Point2", "Vector"]

Vector = NDArray[np.float64]  # A 3D vector, or an (N, 3) / (N, k) array of them
Color = tuple[int, int, int]
Point2 = tuple[float, float]  # Screen coordinates in pixels
Lens = Callable[[float, float, float], list[Point2]]  # (x, y, distance) -> lensed images
