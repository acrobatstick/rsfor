import re
import sys
from dataclasses import dataclass
from enum import Enum

# in minutes
min_service_time = 5
max_service_time = 60


class Tyre(Enum):
    Auto = -1
    TarmacDry = 0
    TarmacIntermediate = 1
    TarmacWet = 2
    GravelDry = 3
    GravelIntermediate = 4
    GravelWet = 5
    Snow = 6

    @classmethod
    def from_str(cls, value: str) -> "Tyre":
        try:
            return cls[value]
        except KeyError:
            options = [re.sub(r"(?<!^)(?=[A-Z])", " ", e.name) for e in cls]
            sys.exit(f"Invalid tyres type: '{value}'.\nValid options: {options}")


class Surface(Enum):
    New = 1
    Normal = 2
    Worn = 3

    @classmethod
    def from_str(cls, value: str) -> "Surface":
        try:
            return cls[value]
        except KeyError:
            sys.exit(f"Invalid surface wear: '{value}'. Valid options: {[e.name for e in cls]}")


class MechanicSkill(Enum):
    Inexperienced = 1
    Proficient = 2
    Competent = 3
    Skilled = 4
    Expert = 5

    @classmethod
    def from_str(cls, value: str) -> "MechanicSkill":
        try:
            return cls[value]
        except KeyError:
            sys.exit(f"Invalid mechanic skill: '{value}'. Valid options: {[e.name for e in cls]}")


@dataclass
class Stage:
    stage_id: int
    weather: str = "Morning Clear Crisp"
    allow_tyre_change: bool = True
    allow_setup_change: bool = True
    set_tyre: Tyre = Tyre.Auto
    mechanic_skill = MechanicSkill.Skilled
    surface_wear: Surface = Surface.Normal
    service_time: int = 5
    num_mechanics: int = 2

    def __post_init__(self) -> None:
        if not min_service_time <= self.service_time <= max_service_time:
            msg = (
                f"Stage({self.stage_id}): service_time must be between "
                f"{min_service_time} and {max_service_time}, "
                f"got {self.service_time}"
            )
            sys.exit(msg)

        if isinstance(self.set_tyre, str):
            self.set_tyre = Tyre.from_str("".join(self.set_tyre.split()))
        if isinstance(self.mechanic_skill, str):
            self.mechanic_skill = MechanicSkill.from_str(self.mechanic_skill)
        if isinstance(self.surface_wear, str):
            self.surface_wear = Surface.from_str(self.surface_wear)

    def __str__(self) -> str:
        return (
            f"Stage({self.stage_id})\n"
            f"  weather        : {self.weather}\n"
            f"  tyre change    : {self.allow_tyre_change}\n"
            f"  setup change   : {self.allow_setup_change}\n"
            f"  set tyre       : {self.set_tyre}\n"
            f"  service time   : {self.service_time} min"
        )
