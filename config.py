import sys
from dataclasses import dataclass, field
from typing import ClassVar
from urllib.parse import urlparse

import requests
import yaml
from bs4 import BeautifulSoup

from stage import Stage


@dataclass
class Config:
    MIN_STAGE_COUNT: ClassVar[int] = 2
    MAX_STAGE_COUNT: ClassVar[int] = 69
    MIN_LEG_COUNT: ClassVar[int] = 1
    MAX_LEG_COUNT: ClassVar[int] = 6

    name: str = "Rally Test"
    description: str = "Description Test"
    damage: int = 2
    stage_count: int = 2
    leg_count: int = 2
    pacenote_opt: int = 4
    roadside_service: int = 2
    password: str = ""
    physics_ver: int = 6
    car_ids: list = field(default_factory=list)
    stages: list = field(default_factory=list)
    is_url: bool = False

    def __str__(self) -> str:
        stages_str = "\n".join(f"  {str(stage).replace(chr(10), chr(10) + '  ')}" for stage in self.stages)
        car_ids_str = ", ".join(self.car_ids)
        return (
            f"Config\n"
            f"  name           : {self.name}\n"
            f"  description    : {self.description}\n"
            f"  damage         : {self.damage}\n"
            f"  stage_count    : {self.stage_count}\n"
            f"  leg_count      : {self.leg_count}\n"
            f"  pacenote_opt   : {self.pacenote_opt}\n"
            f"  roadside_service: {self.roadside_service}\n"
            f"  physics_ver    : {self.physics_ver}\n"
            f"  car_ids        : {car_ids_str}\n"
            f"  stages         :\n{stages_str}"
        )

    def __post_init__(self) -> None:
        if not self.name:
            sys.exit("Config: Rally must have a name")

        if self.damage not in {2, 3}:
            sys.exit(f"Config: damage must be between 2 and 3, got {self.damage}")

        if not self.MIN_STAGE_COUNT <= self.stage_count <= self.MAX_STAGE_COUNT:
            sys.exit(f"Config: stage_count must be between 2 and 69, got {self.stage_count}")

        if self.pacenote_opt not in {0, 1, 2, 3, 4, 12}:
            sys.exit(f"Error: pacenote_opt must be 0-4 or 12, got '{self.pacenote_opt}'")

        if self.roadside_service not in {0, 2, 3, 5}:
            sys.exit(f"Error: roadside_service must be 0, 2, 3, or 5. got '{self.pacenote_opt}'")

        if not self.MIN_LEG_COUNT <= self.leg_count <= self.MAX_LEG_COUNT:
            sys.exit(f"Config: leg_count must be between 1 and 6, got {self.leg_count}")

    @classmethod
    def from_path(cls, path: str) -> "Config":
        instance = cls()  # creates with all defaults
        parsed = urlparse(path)
        instance.is_url = parsed.scheme in ("http", "https")
        if not instance.is_url:
            instance.read_from_file(path)
        else:
            instance.read_from_url(path)
        return instance

    def read_from_file(self, path: str) -> None:
        with open(path) as f:
            data = yaml.safe_load(f)

        self.name = str(data.get("name", self.name))
        self.description = str(data.get("description", self.description))
        self.password = str(data.get("password", self.password))
        self.damage = int(data.get("damage", self.damage))
        self.stage_count = int(data.get("stage_count", self.stage_count))
        self.leg_count = int(data.get("leg_count", self.leg_count))
        self.pacenote_opt = int(data.get("pacenote_opt", self.pacenote_opt))
        self.roadside_service = int(data.get("roadside_service", self.roadside_service))
        self.physics_ver = int(data.get("physics_ver", self.physics_ver))
        self.car_ids = [str(car_id) for car_id in data.get("car_ids", self.car_ids)]
        self.stages = [
            Stage(stage_id=stage_id, **stage_data) for stage_id, stage_data in data.get("stages", {}).items()
        ]

        # update stage count using the length of the stage array instead just
        # to make sure
        if len(self.stages) != self.stage_count:
            self.stage_count = len(self.stages)

        self.__post_init__()  # re-run validation after loading

    def read_from_url(self, path: str) -> None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        response = requests.get(path, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        header = soup.find("div", class_="fejlec4", string="Rally info")

        if header is None:
            raise ValueError(f"Could not find 'Rally info' section in page: {path}")

        tables = header.find_all_next("table", limit=2)

        for table in tables:
            print(table)
