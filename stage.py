import sys
from dataclasses import dataclass
from enum import Enum

from utils import UnknownValueError

# in minutes
min_service_time = 5
max_service_time = 60


class Tyre(Enum):
    Auto = -1
    Tarmac_Dry = 0
    Tarmac_Intermediate = 1
    Tarmac_Wet = 2
    Gravel_Dry = 3
    Gravel_Intermediate = 4
    Gravel_Wet = 5
    Snow = 6

    @staticmethod
    def from_str(value: str) -> "Tyre":
        value = value.lower()
        match value:
            case "auto" | "-1":
                result = Tyre.Auto
            case "tarmac dry" | "0":
                result = Tyre.Tarmac_Dry
            case "tarmac intermediate" | "1":
                result = Tyre.Tarmac_Intermediate
            case "tarmac wet" | "2":
                result = Tyre.Tarmac_Wet
            case "gravel dry" | "3":
                result = Tyre.Gravel_Dry
            case "gravel intermediate" | "4":
                result = Tyre.Gravel_Intermediate
            case "gravel wet" | "5":
                result = Tyre.Gravel_Wet
            case "snow" | "6":
                result = Tyre.Snow
            case _:
                raise UnknownValueError(prop="Tyre", value=value)
        return result


class Surface(Enum):
    New = 1
    Normal = 2
    Worn = 3

    @classmethod
    def from_str(cls, value: str) -> "Surface":
        try:
            return cls[value.capitalize()]
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
    id: int
    weather: str = "Morning Clear Crisp"
    allow_tyre_change: bool = True
    allow_setup_change: bool = True
    set_tyre: Tyre = Tyre.Auto
    mechanic_skill = MechanicSkill.Skilled
    surface_wear: Surface = Surface.Normal
    service_time: int = 5
    num_mechanics: int = 2
    start_at_leg: int = -1
    max_leg: int = 6

    def __post_init__(self) -> None:
        if not min_service_time <= self.service_time <= max_service_time:
            msg = (
                f"Stage({self.id}): service_time must be between "
                f"{min_service_time} and {max_service_time}, "
                f"got {self.service_time}"
            )
            sys.exit(msg)

        if isinstance(self.set_tyre, str):
            self.set_tyre = Tyre.from_str(self.set_tyre)
        if isinstance(self.mechanic_skill, str):
            self.mechanic_skill = MechanicSkill.from_str(self.mechanic_skill)
        if isinstance(self.surface_wear, str):
            self.surface_wear = Surface.from_str(self.surface_wear)
        if self.start_at_leg not in range(1, self.max_leg + 1):
            sys.exit(
                f"Stage({self.id}): start_at_leg must be in range of 1 <= n <= {self.max_leg}, got={self.start_at_leg}"
            )

    def __str__(self) -> str:
        return (
            f"Stage({self.id})\n"
            f"  weather        : {self.weather}\n"
            f"  tyre change    : {self.allow_tyre_change}\n"
            f"  setup change   : {self.allow_setup_change}\n"
            f"  set tyre       : {self.set_tyre}\n"
            f"  service time   : {self.service_time} min\n"
            f"  start_at_leg   : {self.start_at_leg}"
        )
