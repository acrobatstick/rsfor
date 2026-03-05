from dataclasses import dataclass, field
import sys


@dataclass
class Stage:
    stage_id: int
    weather: str = "Morning Clear Crisp"
    allow_tyre_change: bool = True
    allow_setup_change: bool = True
    set_tyre: str = "auto"
    service_time: int = 5
    wear: int = 2

    tyres = {
        "auto": -1,
        "Tarmac Dry": 0,
        "Tarmac Intermediate": 1,
        "Tarmac Wet": 2,
        "Gravel Dry": 3,
        "Gravel Intermediate": 4,
        "Gravel Wet": 5,
        "Snow": 6,
    }

    def __post_init__(self):
        if not 5 <= self.service_time <= 60:
            sys.exit(
                f"Stage({self.stage_id}): service_time must be between 5 and 60, got {self.service_time}"
            )

        if not isinstance(self.allow_tyre_change, bool):
            sys.exit(f"Stage({self.stage_id}): allow_tyre_change must be a true/false")

        if not isinstance(self.allow_setup_change, bool):
            sys.exit(f"Stage({self.stage_id}): allow_setup_change must be a true/false")

        if not self.set_tyre in self.tyres:
            sys.exit(
                f"Stage({self.stage_id}): set_tyres of '{self.set_tyre}' is not available to use"
            )

    def __str__(self) -> str:
        return (
            f"Stage({self.stage_id})\n"
            f"  weather        : {self.weather}\n"
            f"  tyre change    : {self.allow_tyre_change}\n"
            f"  setup change   : {self.allow_setup_change}\n"
            f"  set tyre       : {self.set_tyre}\n"
            f"  service time   : {self.service_time} min"
        )
