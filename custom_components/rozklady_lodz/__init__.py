from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .const import (
    DOMAIN, PLATFORMS, CONF_STOP_NUMBER, CONF_SCAN_INTERVAL, CONF_ONLY_TRAMS,
    DEFAULT_SCAN_INTERVAL, DEFAULT_ONLY_TRAMS,
)
from .coordinator import RozkladyCoordinator

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    stop_number = int(entry.data[CONF_STOP_NUMBER])
    scan = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    only_trams = entry.options.get(CONF_ONLY_TRAMS, DEFAULT_ONLY_TRAMS)
    coordinator = RozkladyCoordinator(hass, stop_number, scan, only_trams)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
