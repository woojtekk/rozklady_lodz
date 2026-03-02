from __future__ import annotations
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import API_URL, DEFAULT_SCAN_INTERVAL
from .api import RozkladyAPI

_LOGGER = logging.getLogger(__name__)


class RozkladyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        stop_number: int,
        scan_interval: int,
        only_trams: bool,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="rozklady_lodz",
            update_interval=timedelta(seconds=scan_interval or DEFAULT_SCAN_INTERVAL),
        )
        self._stop = stop_number
        self._only_trams = only_trams
        self._api = RozkladyAPI(async_get_clientsession(hass), API_URL)
        self._last_success_data: dict[str, Any] | None = None
        self._last_success_utc: datetime | None = None

    @property
    def last_success_utc(self) -> datetime | None:
        return self._last_success_utc

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            xml = await self._api.fetch_xml(self._stop)
            data = self._api.parse(xml, only_trams=self._only_trams)
            data["stale"] = False
            self._last_success_data = data
            self._last_success_utc = datetime.now(timezone.utc)
            return data
        except Exception as err:
            if self._last_success_data is not None:
                cached = dict(self._last_success_data)
                cached["stale"] = True
                if self._last_success_utc is not None:
                    age = datetime.now(timezone.utc) - self._last_success_utc
                    cached["stale_age_s"] = int(age.total_seconds())
                return cached
            raise UpdateFailed(f"Update failed: {err}") from err
