from dataclasses import dataclass

@dataclass(slots=True)
class AnimationCommand:
    name: str
    cfg: dict = {}

@dataclass(slots=True)
class ParticleCommand:
    name: str
    constant: bool = False

@dataclass(slots=True)
class VariableCommand:
    name: str
    op: str
    value: float = 0

@dataclass(slots=True)
class FlagCommand:
    name: str
    op: str

@dataclass(slots=True)
class AudioCommand:
    name: str
    volume: float
    speed: float