from __future__ import annotations
import logging
from math import atan2, cos, radians, sin, sqrt
from datetime import timedelta
from typing import Any
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import API_URL, DEFAULT_SCAN_INTERVAL, STOPS_API_URL
from .api import RozkladyAPI

_LOGGER = logging.getLogger(__name__)


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_m = 6371000.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return radius_m * c


class RozkladyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        stop_number: int,
        scan_interval: int,
        only_trams: bool,
        tracked_entities: list[str] | None = None,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="rozklady_lodz",
            update_interval=timedelta(seconds=scan_interval or DEFAULT_SCAN_INTERVAL),
        )
        self._stop = stop_number
        self._only_trams = only_trams
        self._tracked_entities = tracked_entities or []
        self._api = RozkladyAPI(async_get_clientsession(hass), API_URL)
        self._stops_cache: list[dict[str, Any]] | None = None

    async def _ensure_stops_cache(self) -> list[dict[str, Any]]:
        if self._stops_cache is not None:
            return self._stops_cache
        self._stops_cache = await self._api.fetch_stops(STOPS_API_URL)
        return self._stops_cache

    def _entity_position(self, entity_id: str) -> tuple[float, float] | None:
        state = self.hass.states.get(entity_id)
        if state is None:
            return None
        latitude = state.attributes.get(ATTR_LATITUDE)
        longitude = state.attributes.get(ATTR_LONGITUDE)
        if latitude is None or longitude is None:
            return None
        try:
            return float(latitude), float(longitude)
        except (TypeError, ValueError):
            return None

    async def _resolve_stop_from_tracked_entities(self) -> tuple[int, str | None, float | None]:
        if not self._tracked_entities:
            return self._stop, None, None

        stops = await self._ensure_stops_cache()
        if not stops:
            return self._stop, None, None

        best_stop: dict[str, Any] | None = None
        best_source: str | None = None
        best_distance: float | None = None

        for entity_id in self._tracked_entities:
            coords = self._entity_position(entity_id)
            if coords is None:
                continue
            lat, lon = coords
            for stop in stops:
                distance_m = _haversine_m(lat, lon, stop["latitude"], stop["longitude"])
                if best_distance is None or distance_m < best_distance:
                    best_distance = distance_m
                    best_stop = stop
                    best_source = entity_id

        if best_stop is None:
            return self._stop, None, None

        return int(best_stop["stop_number"]), best_source, best_distance

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            active_stop, source, distance_m = await self._resolve_stop_from_tracked_entities()
            xml = await self._api.fetch_xml(active_stop)
            data = self._api.parse(xml, only_trams=self._only_trams)
            data["active_stop_number"] = active_stop
            data["location_source"] = source
            data["distance_m"] = round(distance_m, 1) if distance_m is not None else None
            return data
        except Exception as err:
            raise UpdateFailed(f"Update failed: {err}") from err
