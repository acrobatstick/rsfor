import logging
import re
import sys
from dataclasses import asdict, dataclass, field, fields
from enum import Enum
from html import unescape
from pathlib import Path
from typing import ClassVar, TypeAlias
from urllib.parse import urlparse

import requests
import yaml
from bs4 import BeautifulSoup, ResultSet, Tag

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

SerializedType: TypeAlias = None | str | int | float | bool | dict[str, "SerializedType"] | list["SerializedType"]


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
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger(__name__))
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
    is_url: bool = False
    legs: dict[int, list[Stage]] = field(default_factory=dict)
    super_rally: bool = True

    def __str__(self) -> str:
        stages_str = "\n".join(f"  {str(stage).replace(chr(10), chr(10) + '  ')}" for stage in self.stages())
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
            self.logger.error("Rally must have a name")
            sys.exit(1)

        if not self.MIN_STAGE_COUNT <= self.stage_count <= self.MAX_STAGE_COUNT:
            self.logger.error(
                "stage_count must be between %d and %d, got %d",
                self.MIN_STAGE_COUNT,
                self.MAX_STAGE_COUNT,
                self.stage_count,
            )
            sys.exit(1)

        if self.roadside_service not in {0, 2, 3, 5}:
            self.logger.error("roadside_service must be 0, 2, 3, or 5. got %d", self.roadside_service)
            sys.exit(1)

        if not self.MIN_LEG_COUNT <= self.leg_count <= self.MAX_LEG_COUNT:
            self.logger.error(
                "leg_count must be between %d and %d, got %d",
                self.MIN_LEG_COUNT,
                self.MAX_LEG_COUNT,
                self.stage_count,
            )
            sys.exit(1)

        if self.leg_count > self.stage_count:
            self.logger.error("Cannot have more legs than stages")
            sys.exit(1)

    @classmethod
    def from_path(cls, logger: logging.Logger, path: str, name: str = "", password: str = "") -> "Config":
        instance = cls()  # creates with all defaults
        instance.logger = logger

        parsed = urlparse(path)
        instance.is_url = parsed.scheme in ("http", "https")
        if not instance.is_url:
            instance._read_from_file(path)
        else:
            instance._read_from_url(path)

        # if no name arg provided, append (Copy) to avoid confusion on
        # online rally list
        if name:
            instance.name = name
        elif instance.is_url:
            instance.name += " (Copy)"

        if password:
            instance.password = password

        return instance

    def _read_from_file(self, path: str) -> None:
        with Path(path).open("r") as f:
            data = yaml.safe_load(f)

        self.name = str(data.get("name", self.name))
        self.description = str(data.get("description", self.description))
        self.password = str(data.get("password", self.password))
        self.damage = Damage.from_str(data.get("damage", self.damage))
        self.stage_count = int(data.get("stage_count", self.stage_count))
        self.leg_count = int(data.get("leg_count", self.leg_count))
        self.pacenote_opt = PacenoteStyle.from_str(str(data.get("pacenote_opt", self.pacenote_opt)))
        self.roadside_service = int(data.get("roadside_service", self.roadside_service))
        self.physics_ver = int(data.get("physics_ver", self.physics_ver))
        self.car_groups = [str(car_id) for car_id in data.get("car_groups", self.car_groups)]
        self.super_rally = data.get("super_rally", self.super_rally)

        stages = [
            Stage(
                id=stage["id"],
                max_leg=self.leg_count,
                **{k: v for k, v in stage.items() if k != "id"},
            )
            for stage in data.get("stages", [])
        ]

        self.legs = {i: [] for i in range(1, self.leg_count + 1)}

        # update stage count using the length of the stage array instead just
        # to make sure
        if len(stages) != self.stage_count:
            self.stage_count = len(stages)

        self._insert_stages_to_leg(stages)

        for i in range(1, self.leg_count + 1):
            stages = self.legs.get(i)
            if stages is None:
                # should not raise this error
                raise LookupError
            if not stages:
                self.logger.error("Leg(%d) must have at least 1 stage", i)
                sys.exit(1)

        self.__post_init__()  # re-run validation after loading

    def _read_from_url(self, path: str) -> None:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        response = requests.get(path, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html5lib")
        header = soup.find("div", class_="fejlec4", string="Rally info")

        is_championship = False
        # find the "header" inside the online rally page as the anchor
        # to find the rally info such as the stages and legs details
        if not isinstance(header, Tag):
            # if header is not found. it can be a championship page.
            # select the last <td> element since it's the main container for the rally
            header = soup.find_all("td", class_="szdb")[-1]
            if not isinstance(header, Tag):
                self.logger.error("Could not find 'Rally info' section in page: %s", path)
                sys.exit(1)

            # to determine rally championship, check if header have 4 tables inside it
            if len(header.find_all("table")) >= 4:
                is_championship = True
            else:
                self.logger.error("Could not find 'Rally info' section in page: %s", path)
                sys.exit(1)

        if is_championship:
            # not implementing due to most of championship rally are using stage aliases
            self.logger.error("Automating championship rally is not implemented")
            sys.exit(1)

        # select the last 2 tables
        #   - table1 = rally overview details
        #   - table2 = leg details
        tables = header.find_all_next("table", limit=2)
        table1 = tables[0] if len(tables) > 0 else None
        table2 = tables[1] if len(tables) > 1 else None

        if isinstance(table1, Tag):
            self._scrape_table1(table1)

        if isinstance(table2, Tag):
            self._scrape_table2(table2)

        self.__post_init__()  # re-run validation after loading

    def _set_from_map(self, data: list) -> None:
        for cells in data:
            if len(cells) != 2:
                continue
            key, value = cells
            value = value.strip()
            mapped = KEY_MAP.get(key.strip())
            if not mapped or not hasattr(self, mapped):
                continue
            match mapped:
                case "leg_count":
                    setattr(self, mapped, int(value))
                case "super_rally":
                    setattr(self, mapped, utils.string_to_boolean_map(value) or True)
                case "car_groups":
                    setattr(self, mapped, [c.strip() for c in value.split(",")])
                case "damage":
                    setattr(self, mapped, Damage.from_str(value))
                case "pacenote_opt":
                    setattr(self, mapped, PacenoteStyle.from_str(value))
                case _:
                    setattr(self, mapped, value)

    def _scrape_table1(self, table: Tag) -> None:
        data = []
        rows = table.find_all("tr")
        for row in rows:
            if isinstance(row, Tag):
                cells = row.get_text(separator=" ", strip=True).split(":", 1)
                data.append(cells)

        self.name = data.pop(0)[0]
        self._set_from_map(data)

    def _parse_stageid_from_tip(self, div: object) -> int:
        if not isinstance(div, Tag):
            self.logger.error("Could not get stage information from stage list, maybe using alias?")
            sys.exit(1)
        onmouseover = str(div.get("onmouseover", ""))
        match = re.search(r"ID:\s*(\d+)", unescape(onmouseover))
        if not match:
            self.logger.fatal("Could not get stage id from stage tip element")
            sys.exit(1)
        return int(match.group(1))

    def _parse_stage_row(self, stage: Stage, cells: ResultSet) -> None:
        stage.weather = cells[4].get_text()
        allow_tyre_change, allow_setup_change = cells[5].get_text().split(" / ")
        stage.allow_tyre_change = utils.string_to_boolean_map(allow_tyre_change) or False
        stage.allow_setup_change = utils.string_to_boolean_map(allow_setup_change) or False
        set_tyre = cells[6].get_text(strip=True)

        if not allow_tyre_change or set_tyre == "Keep previous":
            stage.set_tyre = Tyre.Auto
        else:
            stage.set_tyre = Tyre.from_str(set_tyre)

    def _scan_next_rows(self, rows: ResultSet, i: int) -> tuple[bool, int, int]:
        """Scan ahead to check for service park and leg boundaries."""
        has_service_park = False
        leg_increment = 0
        while i < len(rows):
            next_row = rows[i]
            if not isinstance(next_row, Tag):
                self.logger.fatal("next_row is not an html element")
                sys.exit(1)
            next_classes = next_row.get("class") or []
            if "servicepark" in next_classes:
                has_service_park = True
            elif "paratlan" in next_classes or "paros" in next_classes:
                break
            elif not next_classes:
                # no class means it's a leg boundary with form of <tr>
                leg_increment += 1
            if has_service_park:
                break
            i += 1
        return has_service_park, leg_increment, i

    def _parse_service_park(self, stage: Stage, row: object) -> None:
        if not isinstance(row, Tag):
            self.logger.fatal("service park row is not a Tag element")
            sys.exit(1)
        parts = row.get_text(strip=True).split("-", 1).pop(1).split("-")
        time_match = re.search(r"\d+", parts[0])
        stage.service_time = int(time_match.group()) if time_match else 0
        # service park with crew
        if len(parts) > 1:
            mech_match = re.search(r"\d+", parts[1])
            stage.num_mechanics = int(mech_match.group()) if mech_match else 0

    def _scrape_table2(self, table: Tag) -> None:
        rows = table.find_all("tr")
        stages = []
        leg = 1
        i = 0
        while i < len(rows):
            row = rows[i]
            i += 1
            if not isinstance(row, Tag):
                continue

            classes = row.get("class") or []
            if "paratlan" in classes or "paros" in classes:
                cells = row.find_all("td", recursive=False)
                if len(cells) != 7:
                    sys.exit("not a valid stage row details")
                stage_id = self._parse_stageid_from_tip(div=row.find("div", onmouseover=True))
                stage = Stage(id=stage_id, start_at_leg=leg)
                self._parse_stage_row(stage, cells)

                has_service_park, leg_increment, i = self._scan_next_rows(rows, i)
                # update current leg position if we reach leg boundaries while scanning rows
                leg += leg_increment

                if has_service_park and i < len(rows):
                    # take the row by the new index from reading inside self._scan_next_rows
                    next_row = rows[i]
                    i += 1
                    if not isinstance(next_row, Tag):
                        self._parse_service_park(stage, next_row)

                stages.append(stage)
            else:
                i += 1

        self._insert_stages_to_leg(stages)
        self.stage_count = len(stages)

    def _insert_stages_to_leg(self, stages: list[Stage]) -> None:
        self.legs.clear()
        for stage in stages:
            at_leg = stage.start_at_leg
            leg = self.legs.get(at_leg)
            if leg is None:
                self.legs = {i: [] for i in range(1, self.leg_count + 1)}
                leg = self.legs[at_leg]
            leg.append(stage)

    def stages(self) -> list[Stage]:
        ret: list[Stage] = []
        for i in range(1, self.leg_count + 1):
            stages = self.legs.get(i)
            if stages is None:
                # should not raise this error
                raise LookupError
            ret.extend(stages)
        # TODO: should this be sorted like this?
        return sorted(ret, key=lambda s: s.start_at_leg)

    def generate_legs_start_at(self) -> list[int]:
        ret: list[int] = []
        if not self.stages:
            return ret
        stages = self.stages()
        i = 0
        while i < len(stages) - 1:
            current = stages[i]
            j = i + 1
            while j < len(stages) and stages[j].start_at_leg == current.start_at_leg:
                j += 1
            if j < len(stages):
                ret.append(j + 1)
            i = j
        return ret

    def dump(self) -> None:
        def serialize(obj: object) -> SerializedType:  # pyright: ignore[reportAny]
            if isinstance(obj, logging.Logger):
                return None
            if isinstance(obj, Enum):
                return obj.name  # or obj.value
            if isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [serialize(i) for i in obj]
            if hasattr(obj, "__dataclass_fields__"):
                return {k: serialize(v) for k, v in asdict(obj).items()}  # type: ignore[arg-type]
            return obj  # type: ignore[arg-type]

        stage_field_order = [
            "id",
            "weather",
            "allow_tyre_change",
            "allow_setup_change",
            "set_tyre",
            "service_time",
            "surface_wear",
            "start_at_leg",
        ]
        # flatten stages on legs property into 1 big list instead
        stages = []
        for leg_num, stage_list in self.legs.items():
            for stage in stage_list:
                s = {f.name: serialize(getattr(stage, f.name)) for f in fields(stage)}
                s["start_at_leg"] = leg_num
                ordered = {k: s[k] for k in stage_field_order if k in s}
                ordered.update({k: v for k, v in s.items() if k not in stage_field_order})
                stages.append(ordered)

        all_data = {
            f.name: serialize(getattr(self, f.name))
            for f in fields(self)
            if not isinstance(getattr(self, f.name), logging.Logger) and f.name != "legs"  # exclude legs
        }
        all_data["stages"] = stages

        top_lvl_order = [
            "name",
            "description",
            "damage",
            "stage_count",
            "leg_count",
            "pacenote_opt",
            "roadside_service",
            "password",
            "physics_ver",
            "car_groups",
            "is_url",
            "super_rally",
            "stages",
        ]

        data = {k: all_data[k] for k in top_lvl_order if k in all_data}
        data.update({k: v for k, v in all_data.items() if k not in top_lvl_order})

        path = Path(f"./dumps/{self.name}.yaml")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            self.logger.info("Rally configuration dumped at %s", path)
