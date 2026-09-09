from dataclasses import dataclass, field
from PySide6.QtGui import QPixmap

@dataclass(slots=True)
class AnimationVariant:
    frames: list[QPixmap]
    weight: float

@dataclass(slots=True)
class AnimationData:
    frames: list[QPixmap]
    fps: int = 12
    holds: dict = field(default_factory=dict)
    times_to_loop: int = 1
    bounds: tuple[int, int] = (0, 0)
    loop: bool = False
    variants: list[AnimationVariant] = field(default_factory=list)