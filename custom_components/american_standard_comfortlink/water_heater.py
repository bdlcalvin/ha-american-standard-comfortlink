"""Water heater platform for ComfortLink."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.water_heater import (
    STATE_OFF,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_GATEWAY,
    DOMAIN,
    OP_MODE_COMFORT,
    OP_MODE_ECO,
    OP_MODE_FAST,
    OP_MODE_IMEMORY,
)
from .coordinator import ComfortLinkCoordinator

_LOGGER = logging.getLogger(__name__)

# Operating-mode labels match the ComfortLink app exactly.
MODE_ECO = "Eco"
MODE_COMFORT = "Comfort"
MODE_FAST = "Fast"
MODE_IMEMORY = "i-Memory"

_OP_MODE_TO_NAME = {
    OP_MODE_ECO: MODE_ECO,
    OP_MODE_COMFORT: MODE_COMFORT,
    OP_MODE_FAST: MODE_FAST,
    OP_MODE_IMEMORY: MODE_IMEMORY,
}
_NAME_TO_OP_MODE = {v: k for k, v in _OP_MODE_TO_NAME.items()}

OPERATION_LIST = [STATE_OFF, MODE_ECO, MODE_COMFORT, MODE_FAST, MODE_IMEMORY]

# From the captured plantSettings: SlpMinSetpointTemperature / SlpMaxSetpointTemperature
MIN_TEMP_F = 104.0
MAX_TEMP_F = 151.0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ComfortLinkCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ComfortLinkWaterHeater(coordinator, entry)])


class ComfortLinkWaterHeater(CoordinatorEntity[ComfortLinkCoordinator], WaterHeaterEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
        | WaterHeaterEntityFeature.ON_OFF
    )
    _attr_operation_list = OPERATION_LIST
    _attr_min_temp = MIN_TEMP_F
    _attr_max_temp = MAX_TEMP_F

    def __init__(self, coordinator: ComfortLinkCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._gateway = entry.data[CONF_GATEWAY]
        self._attr_unique_id = self._gateway
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._gateway)},
            "name": "ComfortLink Water Heater",
            "manufacturer": "American Standard",
            "model": "ComfortLink Heat Pump Water Heater",
        }

    @property
    def _data(self) -> dict:
        return self.coordinator.data or {}

    @property
    def is_on(self) -> bool:
        return self._data.get("on", False)

    @property
    def current_temperature(self) -> float | None:
        temp = self._data.get("waterTemp")
        return float(temp) if temp is not None else None

    @property
    def target_temperature(self) -> float | None:
        # The /temperatures endpoint writes the "comfort" setpoint, so the
        # slider must track comfortTemp (not procReqTemp, which can reflect a
        # scheduled reduced setpoint and would desync reads from writes).
        temp = self._data.get("comfortTemp")
        return float(temp) if temp is not None else None

    @property
    def current_operation(self) -> str:
        if not self._data.get("on", True):
            return STATE_OFF
        op_mode = self._data.get("opMode", 0)
        return _OP_MODE_TO_NAME.get(op_mode, MODE_ECO)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temp = kwargs.get("temperature")
        if temp is None:
            return
        # The API uses optimistic concurrency: "old" must be the current
        # comfort setpoint the server has on record.
        old_temp = self.target_temperature
        if old_temp is None:
            old_temp = temp
        await self.coordinator.api.set_temperature(self._gateway, float(temp), float(old_temp))
        await self.coordinator.async_request_refresh()

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        # Boost is a separate concern exposed via its own switch entity; it is
        # intentionally NOT driven from here so every operative mode (including
        # fast / HIGH_DEMAND) stays selectable.
        if operation_mode == STATE_OFF:
            await self.coordinator.api.set_switch(self._gateway, False)
        else:
            if not self.is_on:
                await self.coordinator.api.set_switch(self._gateway, True)
            new_mode = _NAME_TO_OP_MODE.get(operation_mode)
            old_mode = self._data.get("opMode", OP_MODE_ECO)
            if new_mode is not None and new_mode != old_mode:
                await self.coordinator.api.set_operative_mode(
                    self._gateway, new_mode, old_mode
                )
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api.set_switch(self._gateway, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api.set_switch(self._gateway, False)
        await self.coordinator.async_request_refresh()
