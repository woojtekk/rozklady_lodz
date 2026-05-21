from __future__ import annotations

from typing import Any
from datetime import datetime, timedelta, timezone

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import CoordinatorEntity


from .const import (
    CONF_LINES,
    CONF_NAME,
    CONF_STOP_NUMBER,
    DEFAULT_NAME,
    DOMAIN,
)
from .coordinator import RozkladyCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: RozkladyCoordinator = hass.data[DOMAIN][entry.entry_id]
    lines_config = entry.options.get(CONF_LINES, entry.data[CONF_LINES])
    lines = [line.strip().upper() for line in str(lines_config).split(",") if line.strip()]
    name_prefix = entry.data.get(CONF_NAME) or DEFAULT_NAME

    entities: list[SensorEntity] = [
        DepartureSensor(coordinator, entry, line, name_prefix) for line in lines
    ]
    entities.append(LastUpdateSensor(coordinator, entry, name_prefix))
    async_add_entities(entities)


class DepartureSensor(CoordinatorEntity[RozkladyCoordinator], SensorEntity):
    _attr_icon = "mdi:tram"
    _attr_native_unit_of_measurement = "min"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self, coordinator: RozkladyCoordinator, entry: ConfigEntry, line: str, name_prefix: str
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._line = line
        self._attr_unique_id = f"{entry.entry_id}_line_{line}"
        self._attr_name = f"{name_prefix} {line}"

    @property
    def device_info(self) -> DeviceInfo:
        stop = self._entry.data.get(CONF_STOP_NUMBER)
        return DeviceInfo(
            identifiers={(DOMAIN, f"stop_{stop}")},
            name=f"Rozklady Lodz ({stop})",
            manufacturer="rozklady.lodz.pl",
            model="Realtime departures",
        )

    @property
    def native_value(self) -> int | None:
        data = self.coordinator.data or {}
        is_stale = bool(data.get("stale"))
        elapsed_minutes = 0
        if is_stale and self.coordinator.last_success_utc is not None:
            elapsed_s = (datetime.now(timezone.utc) - self.coordinator.last_success_utc).total_seconds()
            elapsed_minutes = int(elapsed_s // 60)
        departures = (data.get("departures") or {}).get(self._line)
        if not departures:
            return None
        for item in departures["items"]:
            minutes = item.get("minutes")
            if minutes is not None:
                remaining = int(minutes) - elapsed_minutes
                if remaining < 0:
                    return None
                return max(0, remaining)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        is_stale = bool(data.get("stale"))
        elapsed_minutes = 0
        if is_stale and self.coordinator.last_success_utc is not None:
            elapsed_s = (datetime.now(timezone.utc) - self.coordinator.last_success_utc).total_seconds()
            elapsed_minutes = int(elapsed_s // 60)
        departures = (data.get("departures") or {}).get(self._line) or {}

        items = departures.get("items") or []
        minutes_list: list[int] = []
        for item in items:
            minutes = item.get("minutes")
            if minutes is None:
                continue
            remaining = int(minutes) - elapsed_minutes
            if remaining < 0:
                continue
            minutes_list.append(max(0, remaining))
        pretty_list = [item["pretty"] for item in items]

        return {
            "stop_name": data.get("stop_name"),
            "direction": departures.get("dir"),
            "minutes_list": minutes_list,
            "pretty_list": pretty_list,
            "line": self._line,
            "stale": is_stale,
            "stale_age_s": data.get("stale_age_s"),
        }


class LastUpdateSensor(SensorEntity):
    _attr_icon = "mdi:clock-outline"
    _attr_native_unit_of_measurement = "s"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self, coordinator: RozkladyCoordinator, entry: ConfigEntry, name_prefix: str
    ) -> None:
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_last_update_age"
        self._attr_name = f"{name_prefix} ostatnia aktualizacja"
        self._unsub = None

    @property
    def device_info(self) -> DeviceInfo:
        stop = self._entry.data.get(CONF_STOP_NUMBER)
        return DeviceInfo(
            identifiers={(DOMAIN, f"stop_{stop}")},
            name=f"Rozklady Lodz ({stop})",
            manufacturer="rozklady.lodz.pl",
            model="Realtime departures",
        )

    @property
    def native_value(self) -> int | None:
        if self._coordinator.last_success_utc is None:
            return None
        elapsed = (datetime.now(timezone.utc) - self._coordinator.last_success_utc).total_seconds()
        return int(elapsed)

    async def async_added_to_hass(self) -> None:
        self._unsub = async_track_time_interval(
            self.hass, self._tick, timedelta(seconds=1)
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    def _tick(self, _now: datetime) -> None:
        self.async_write_ha_state()
