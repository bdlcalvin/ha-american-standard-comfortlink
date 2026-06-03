"""American Standard ComfortLink integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CannotConnect, ComfortLinkAPI, InvalidAuth
from .const import CONF_GATEWAY, DOMAIN
from .coordinator import ComfortLinkCoordinator

PLATFORMS = [Platform.WATER_HEATER, Platform.SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    api = ComfortLinkAPI(
        session,
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
    )
    # Wrap login so a transient failure (e.g. a 429 at startup) makes HA retry
    # cleanly instead of throwing and leaving the entry half-set-up.
    try:
        await api.login()
    except InvalidAuth as err:
        raise ConfigEntryAuthFailed("Invalid ComfortLink credentials") from err
    except CannotConnect as err:
        raise ConfigEntryNotReady("Cannot reach ComfortLink cloud") from err

    coordinator = ComfortLinkCoordinator(hass, api, entry.data[CONF_GATEWAY])
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
