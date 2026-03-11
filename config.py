import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from html import unescape
from typing import ClassVar
from urllib.parse import urlparse

import requests
import yaml
from bs4 import BeautifulSoup, Tag

import utils
from stage import Stage, Tyre

KEY_MAP = {
    "Description": "description",
    "Creator": "creator",
    "Damage Level": "damage",
    "Number of Legs": "leg_count",
    "SuperRally": "super_rally",
    "Pacenotes options": "pacenote_opt",
    "Car Groups": "car_groups",
}


class Damage(Enum):
    Reduced = 2
    Realistic = 3

    @staticmethod
    def from_str(value: str) -> "Damage":
        match value:
            case "reduced" | "2":
                return Damage.Reduced
            case "realistic" | "3":
                return Damage.Realistic
            case _:
                raise utils.UnknownValueError(prop="Damage", value=value)


class PacenoteStyle(Enum):
    Normal = 0
    No_3D_Pacenotes = 1
    No_Countdown = 2
    No_3D_And_Countdown = 3
    Audio_Only = 4
    No_Symbols_And_Audio = 12

    @staticmethod
    def from_str(value: str) -> "PacenoteStyle":
        match value.lower():
            case "normal pacenotes" | "0":
                result = PacenoteStyle.Normal
            case "don't show 3d pacenotes" | "1":
                result = PacenoteStyle.No_3D_Pacenotes
            case "don't show the countdown of pacenote distance" | "2":
                result = PacenoteStyle.No_Countdown
            case "don't show the 3d pacenote and countdown of pace note distance" | "3":
                result = PacenoteStyle.No_3D_And_Countdown
            case "only pacenote audio" | "4":
                result = PacenoteStyle.Audio_Only
            case "no pacenote symbols and audio" | "12":
                result = PacenoteStyle.No_Symbols_And_Audio
            case _:
                raise utils.UnknownValueError(prop="Pacenote Style", value=value)
        return result


@dataclass
class Config:
    MIN_STAGE_COUNT: ClassVar[int] = 2
    MAX_STAGE_COUNT: ClassVar[int] = 69
    MIN_LEG_COUNT: ClassVar[int] = 1
    MAX_LEG_COUNT: ClassVar[int] = 6

    name: str = "Rally Test"
    description: str = "Description Test"
    damage: Damage = Damage.Realistic
    stage_count: int = 2
    leg_count: int = 2
    pacenote_opt: PacenoteStyle = PacenoteStyle.Audio_Only
    roadside_service: int = 2
    password: str = ""
    physics_ver: int = 6
    car_groups: list = field(default_factory=list)
    stages: list = field(default_factory=list)
    is_url: bool = False

    def __str__(self) -> str:
        stages_str = "\n".join(f"  {str(stage).replace(chr(10), chr(10) + '  ')}" for stage in self.stages)
        car_groups_str = ", ".join(self.car_groups)
        return (
            f"Config\n"
            f"  name            : {self.name}\n"
            f"  description     : {self.description}\n"
            f"  damage          : {self.damage}\n"
            f"  stage_count     : {self.stage_count}\n"
            f"  leg_count       : {self.leg_count}\n"
            f"  pacenote_opt    : {self.pacenote_opt}\n"
            f"  roadside_service: {self.roadside_service}\n"
            f"  physics_ver     : {self.physics_ver}\n"
            f"  car_groups      : {car_groups_str}\n"
            f"  stages          :\n{stages_str}"
        )

    def __post_init__(self) -> None:
        if not self.name:
            sys.exit("Config: Rally must have a name")

        if not self.MIN_STAGE_COUNT <= self.stage_count <= self.MAX_STAGE_COUNT:
            sys.exit(f"Config: stage_count must be between 2 and 69, got {self.stage_count}")

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
        self.damage = Damage.from_str(data.get("damage", self.damage))
        self.stage_count = int(data.get("stage_count", self.stage_count))
        self.leg_count = int(data.get("leg_count", self.leg_count))
        self.pacenote_opt = PacenoteStyle.from_str(data.get("pacenote_opt", self.pacenote_opt))
        self.roadside_service = int(data.get("roadside_service", self.roadside_service))
        self.physics_ver = int(data.get("physics_ver", self.physics_ver))
        self.car_groups = [str(car_id) for car_id in data.get("car_groups", self.car_groups)]
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
        response = requests.get(path, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html5lib")
        header = soup.find("div", class_="fejlec4", string="Rally info")

        # find the "header" inside the online rally page as the anchor
        # to find the rally info such as the stages and legs details
        if header is None:
            sys.exit(f"Could not find 'Rally info' section in page: {path}")

        tables = header.find_all_next("table", limit=2)
        table1 = tables[0] if len(tables) > 0 else None
        table2 = tables[1] if len(tables) > 1 else None

        if isinstance(table1, Tag):
            self.scrape_table1(table1)

        if isinstance(table2, Tag):
            self.scrape_table2(table2)

        self.__post_init__()  # re-run validation after loading

    def scrape_table1(self, table: Tag) -> None:
        data = []
        rows = table.find_all("tr")
        for row in rows:
            if isinstance(row, Tag):
                cells = row.get_text(separator=" ", strip=True).split(":", 1)
                data.append(cells)

        car_groups_at = -1

        self.name = data.pop(0)[0]

        for idx, cells in enumerate(data):
            if len(cells) == 2:
                key, value = cells
                value = value.strip()
                mapped = KEY_MAP.get(key.strip())
                if mapped and hasattr(self, mapped):
                    match mapped:
                        case "leg_count":
                            setattr(self, mapped, int(value))
                        case "car_groups":
                            setattr(self, mapped, [c.strip() for c in value.split(",")])
                            car_groups_at = idx
                        case "damage":
                            setattr(self, mapped, Damage.from_str(value))
                        case "pacenote_opt":
                            setattr(self, mapped, PacenoteStyle.from_str(value))
                        case _:
                            setattr(self, mapped, value)

        if car_groups_at != -1:
            # TODO: set the schedule of each leg
            data = data[car_groups_at + 1 :]
        else:
            sys.exit("could not find car group element")

    def scrape_table2(self, table: Tag) -> None:
        rows = table.find_all("tr")
        stages = []

        for row in rows:
            if not isinstance(row, Tag):
                continue
            classes = row.get("class") or []
            if "paratlan" not in classes and "paros" not in classes:
                continue

            cells = row.find_all("td", recursive=False)
            if len(cells) != 7:
                sys.exit("not a valid stage row details")

            div = row.find("div", onmouseover=True)
            if not isinstance(div, Tag):
                sys.exit("could not get the stage tip element")

            onmouseover = str(div.get("onmouseover", ""))
            match = re.search(r"ID:\s*(\d+)", unescape(onmouseover))
            if not match:
                sys.exit("could not get the stage id from the tip element")

            stage_id = int(match.group(1))

            stage = Stage(stage_id=stage_id)

            stage.weather = cells[4].get_text()
            allow_tyre_change, allow_setup_change = cells[5].get_text().split(" / ")
            stage.allow_tyre_change = utils.string_to_boolean_map(allow_tyre_change) or False
            stage.allow_setup_change = utils.string_to_boolean_map(allow_setup_change) or False

            set_tyre = cells[6].get_text(strip=True)
            if not allow_tyre_change or set_tyre == "Keep previous":
                stage.set_tyre = Tyre.Auto
            else:
                stage.set_tyre = Tyre.from_str(set_tyre)

            next_row = row.find_next_sibling("tr")
            has_service_park = False

            while isinstance(next_row, Tag):
                next_classes = next_row.get("class") or []
                if "servicepark" in next_classes:
                    has_service_park = True
                elif "paratlan" in next_classes or "paros" in classes:
                    # if the next row is a stage. that mean there is no service park
                    # for the current stage we are reading
                    break
                if has_service_park:
                    break
                next_row = next_row.find_next_sibling("tr")

            if has_service_park and isinstance(next_row, Tag):
                parts = next_row.get_text(strip=True).split("-", 1).pop(1).split("-")
                time_match = re.search(r"\d+", parts[0])
                mech_match = re.search(r"\d+", parts[1])
                stage.service_time = int(time_match.group()) if time_match else 0
                stage.num_mechanics = int(mech_match.group()) if mech_match else 0

            stages.append(stage)

        self.stages = stages
        self.stage_count = len(stages)
