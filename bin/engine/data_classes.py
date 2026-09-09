from dataclasses import dataclass, field

@dataclass(slots=True)
class AnimationVariant:
    frames: list
    weight: float

@dataclass(slots=True)
class AnimationData:
    frames: list
    fps: int = 12
    holds: dict = field(default_factory=dict)
    times_to_loop: int = 1
    bounds: tuple[int, int] = (0, 0)
    loop: bool = False
    variants: list[AnimationVariant] = field(default_factory=list)