from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_STOP_NUMBER, DOMAIN
from .coordinator import RozkladyCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: RozkladyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RefreshButton(coordinator, entry)])


class RefreshButton(ButtonEntity):
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: RozkladyCoordinator, entry: ConfigEntry) -> None:
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_refresh"
        self._attr_name = "Odśwież"

    @property
    def device_info(self) -> DeviceInfo:
        stop = self._entry.data.get(CONF_STOP_NUMBER)
        return DeviceInfo(
            identifiers={(DOMAIN, f"stop_{stop}")},
            name=f"Rozklady Lodz ({stop})",
            manufacturer="rozklady.lodz.pl",
            model="Realtime departures",
        )

    async def async_press(self) -> None:
        await self._coordinator.async_request_refresh()
