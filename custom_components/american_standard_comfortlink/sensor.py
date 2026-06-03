"""Sensor platform for ComfortLink — energy usage and temperatures."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_GATEWAY, DOMAIN
from .coordinator import ComfortLinkCoordinator


@dataclass(frozen=True, kw_only=True)
class ComfortLinkSensorDescription(SensorEntityDescription):
    data_key: str
    value_fn: Any = None


SENSORS: tuple[ComfortLinkSensorDescription, ...] = (
    ComfortLinkSensorDescription(
        key="water_temp",
        name="Water Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        data_key="waterTemp",
    ),
    ComfortLinkSensorDescription(
        key="comfort_temp",
        name="Comfort Setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        data_key="comfortTemp",
    ),
    ComfortLinkSensorDescription(
        key="hp_state",
        name="Heat Pump State",
        data_key="hpState",
        # PROVISIONAL mapping — enum not fully confirmed. The raw integer is
        # exposed as the `raw_value` attribute so it can be mapped correctly.
        value_fn=lambda v: {
            0: "off",
            1: "standby",
            2: "heating",
            3: "anti_legionella",
        }.get(int(v), f"state {int(v)}"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ComfortLinkCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ComfortLinkSensor(coordinator, entry, desc) for desc in SENSORS
    )


class ComfortLinkSensor(CoordinatorEntity[ComfortLinkCoordinator], SensorEntity):
    _attr_has_entity_name = True
    entity_description: ComfortLinkSensorDescription

    def __init__(
        self,
        coordinator: ComfortLinkCoordinator,
        entry: ConfigEntry,
        description: ComfortLinkSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        gateway = entry.data[CONF_GATEWAY]
        self._attr_unique_id = f"{gateway}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, gateway)},
        }

    @property
    def native_value(self) -> Any:
        raw = (self.coordinator.data or {}).get(self.entity_description.data_key)
        if raw is None:
            return None
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(raw)
        return raw

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        # For mapped sensors (e.g. heat pump state) surface the raw API value
        # so unconfirmed enum values can be identified and mapped.
        if self.entity_description.value_fn is None:
            return None
        raw = (self.coordinator.data or {}).get(self.entity_description.data_key)
        return {"raw_value": raw}
