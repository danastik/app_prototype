from dataclasses import dataclass, field
from PySide6.QtGui import QPixmap
from typing import NamedTuple

# @dataclass(slots=True)
# class AnimationVariant:
#     frames: list[QPixmap]
#     weight: float

@dataclass(slots=True)
class AnimationData:
    """
    Contains all data needed to play animation: list of frames, fps, holds, loop, times_to_loop, bounds
    """
    frames: list[QPixmap]
    fps: float = 12
    holds: dict = field(default_factory=dict)
    loop: bool = False
    times_to_loop: int = 1
    bounds: tuple[int, int] = (0, 0)
    # variants: list[AnimationVariant] = field(default_factory=list)

class AllSurfacesData(NamedTuple):
    """
    Contains lists for all types of surfaces.
    """
    top: list
    right: list
    bottom: list
    left: list


class SegmentData(NamedTuple):
    """
    Contains the rect and lists for all types of segments for a window.
    """
    rect: tuple
    top: list[tuple]
    bottom: list[tuple]
    left: list[tuple]
    right: list[tuple]