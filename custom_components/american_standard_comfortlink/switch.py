"""Switch platform for ComfortLink — boost mode."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_GATEWAY, DOMAIN
from .coordinator import ComfortLinkCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ComfortLinkCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ComfortLinkBoostSwitch(coordinator, entry)])


class ComfortLinkBoostSwitch(CoordinatorEntity[ComfortLinkCoordinator], SwitchEntity):
    _attr_has_entity_name = True
    _attr_name = "Boost Mode"
    _attr_icon = "mdi:lightning-bolt"

    def __init__(self, coordinator: ComfortLinkCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        gateway = entry.data[CONF_GATEWAY]
        self._gateway = gateway
        self._attr_unique_id = f"{gateway}_boost"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, gateway)},
        }

    @property
    def is_on(self) -> bool:
        return (self.coordinator.data or {}).get("boostOn", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api.set_boost(self._gateway, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api.set_boost(self._gateway, False)
        await self.coordinator.async_request_refresh()
