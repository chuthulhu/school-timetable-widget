from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
import re


TIME_PATTERN = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")


@dataclass
class Day:
    id: str
    label: str


@dataclass
class Period:
    id: str
    label: str
    start: str  # HH:MM
    end: str    # HH:MM


@dataclass
class UIPosition:
    x: int = 80
    y: int = 60
    width: int = 520
    height: int = 360
    lock: bool = False
    screen_info: Optional[dict] = None


@dataclass
class UIConfig:
    position: UIPosition = field(default_factory=UIPosition)


@dataclass
class ThemeConfig:
    preset: str = "light"  # light | dark | high-contrast(optional)
    tokens: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateConfig:
    auto_check: bool = True


@dataclass
class AppConfig:
    schema_version: int = 2
    locale: str = "ko-KR"
    days: List[Day] = field(default_factory=list)
    periods: List[Period] = field(default_factory=list)
    time_overrides: Dict[str, Dict[str, Dict[str, str]]] = field(default_factory=dict)
    timetable: Dict[str, Dict[str, str]] = field(default_factory=dict)
    ui: UIConfig = field(default_factory=UIConfig)
    theme: ThemeConfig = field(default_factory=ThemeConfig)
    update: UpdateConfig = field(default_factory=UpdateConfig)

    def to_dict(self) -> dict:
        data = asdict(self)
        return data


def _validate_time_string(value: str) -> bool:
    return bool(TIME_PATTERN.match(value))


def _unique_ids(items: List[Any], key: str) -> bool:
    seen = set()
    for item in items:
        v = getattr(item, key)
        if v in seen:
            return False
        seen.add(v)
    return True


def _coerce_days(days_raw: List[dict]) -> List[Day]:
    return [Day(id=str(d.get("id", "")).strip(), label=str(d.get("label", "")).strip()) for d in days_raw]


def _coerce_periods(periods_raw: List[dict]) -> List[Period]:
    periods: List[Period] = []
    for p in periods_raw:
        periods.append(
            Period(
                id=str(p.get("id", "")).strip(),
                label=str(p.get("label", "")).strip(),
                start=str(p.get("start", "")).strip(),
                end=str(p.get("end", "")).strip(),
            )
        )
    return periods


def parse_config(raw: dict) -> AppConfig:
    if not isinstance(raw, dict):
        raise ValueError("Config must be a JSON object")

    schema_version = int(raw.get("schema_version", 2))
    if schema_version != 2:
        raise ValueError(f"Unsupported schema_version: {schema_version}")

    days = _coerce_days(raw.get("days", []))
    periods = _coerce_periods(raw.get("periods", []))

    # Validate presence
    if not days:
        raise ValueError("Config.days must not be empty")
    if not periods:
        raise ValueError("Config.periods must not be empty")

    # Validate unique ids
    if not _unique_ids(days, "id"):
        raise ValueError("Duplicate day ids are not allowed")
    if not _unique_ids(periods, "id"):
        raise ValueError("Duplicate period ids are not allowed")

    # Validate periods time format
    for p in periods:
        if not (_validate_time_string(p.start) and _validate_time_string(p.end)):
            raise ValueError(f"Invalid time format in period {p.id}: {p.start}~{p.end}")

    # time_overrides
    time_overrides = raw.get("time_overrides", {}) or {}
    if not isinstance(time_overrides, dict):
        raise ValueError("time_overrides must be an object")

    day_ids = {d.id for d in days}
    period_ids = {p.id for p in periods}
    for d_id, overrides in time_overrides.items():
        if d_id not in day_ids:
            raise ValueError(f"time_overrides references unknown day id: {d_id}")
        if not isinstance(overrides, dict):
            raise ValueError("time_overrides[day] must be an object of period overrides")
        for p_id, ov in overrides.items():
            if p_id not in period_ids:
                raise ValueError(f"time_overrides[{d_id}] references unknown period id: {p_id}")
            if not isinstance(ov, dict):
                raise ValueError("override must be an object with start/end")
            s = ov.get("start", "")
            e = ov.get("end", "")
            if not (_validate_time_string(s) and _validate_time_string(e)):
                raise ValueError(f"Invalid override time for {d_id}/{p_id}: {s}~{e}")

    # timetable (free-form)
    timetable = raw.get("timetable", {}) or {}
    if not isinstance(timetable, dict):
        raise ValueError("timetable must be an object")

    # ui
    ui_raw = raw.get("ui", {}) or {}
    pos_raw = (ui_raw.get("position") or {}) if isinstance(ui_raw, dict) else {}
    position = UIPosition(
        x=int(pos_raw.get("x", 80)),
        y=int(pos_raw.get("y", 60)),
        width=int(pos_raw.get("width", 520)),
        height=int(pos_raw.get("height", 360)),
        lock=bool(pos_raw.get("lock", False)),
        screen_info=pos_raw.get("screen_info", None),
    )

    ui = UIConfig(position=position)

    # theme
    theme_raw = raw.get("theme", {}) or {}
    theme = ThemeConfig(
        preset=str(theme_raw.get("preset", "light")),
        tokens=dict(theme_raw.get("tokens", {})),
    )

    # update
    update_raw = raw.get("update", {}) or {}
    update = UpdateConfig(auto_check=bool(update_raw.get("auto_check", True)))

    config = AppConfig(
        schema_version=schema_version,
        locale=str(raw.get("locale", "ko-KR")),
        days=days,
        periods=periods,
        time_overrides=time_overrides,
        timetable=timetable,
        ui=ui,
        theme=theme,
        update=update,
    )
    return config


def create_default_config() -> AppConfig:
    return AppConfig(
        days=[
            Day(id="mon", label="월"),
            Day(id="tue", label="화"),
            Day(id="wed", label="수"),
            Day(id="thu", label="목"),
            Day(id="fri", label="금"),
        ],
        periods=[
            Period(id="1", label="1", start="09:00", end="09:45"),
            Period(id="2", label="2", start="09:55", end="10:40"),
            Period(id="3", label="3", start="10:50", end="11:35"),
            Period(id="4", label="4", start="11:45", end="12:30"),
            Period(id="5", label="5", start="13:30", end="14:15"),
            Period(id="6", label="6", start="14:25", end="15:10"),
            Period(id="7", label="7", start="15:20", end="16:05"),
        ],
    )


