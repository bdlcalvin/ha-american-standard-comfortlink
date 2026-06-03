"""DataUpdateCoordinator for ComfortLink."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CannotConnect, ComfortLinkAPI, RateLimited
from .const import DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class ComfortLinkCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self, hass: HomeAssistant, api: ComfortLinkAPI, gateway: str
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.api = api
        self.gateway = gateway

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.get_plant_data(self.gateway)
        except RateLimited:
            # The API blocks bursts of requests for a few minutes. Rather than
            # drop every entity to "unavailable", keep serving the last known
            # reading until the block clears (water temp changes slowly).
            if self.data is not None:
                _LOGGER.debug("Rate limited (429); serving last known data")
                return self.data
            raise UpdateFailed("Rate limited by API and no cached data yet")
        except CannotConnect as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
