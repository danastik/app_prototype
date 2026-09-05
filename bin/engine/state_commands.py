from dataclasses import dataclass

@dataclass(slots=True)
class VariableCommand:
    name: str
    op: str
    value: float = 0

@dataclass(slots=True)
class BoolCommand:
    name: str
    value: bool

@dataclass(slots=True)
class ParticleCommand:
    name: str
    constant: bool = False

@dataclass(slots=True)
class AudioCommand:
    action: str
    name: str
    volume: float | None = None
    speed: float | None = None