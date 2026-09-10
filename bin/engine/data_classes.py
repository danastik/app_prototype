from dataclasses import dataclass, field
from PySide6.QtGui import QPixmap

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

@dataclass(slots=True)
class AllSurfacesData:
    """
    Contains lists for all types of surfaces.
    """
    top: list
    right: list
    bottom: list
    left: list

@dataclass(slots=True)
class SegmentData:
    rect: tuple
    top: list
    bottom: list
    left: list
    right: list