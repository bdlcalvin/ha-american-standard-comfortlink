"""Config flow for American Standard ComfortLink."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CannotConnect, ComfortLinkAPI, InvalidAuth
from .const import CONF_GATEWAY, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_GATEWAY): str,
    }
)


class ComfortLinkConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip()
            password = user_input[CONF_PASSWORD]
            gateway = user_input[CONF_GATEWAY].strip().upper().replace(":", "")

            await self.async_set_unique_id(gateway)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            api = ComfortLinkAPI(session, email, password)

            try:
                await api.login()
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during login")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Water Heater ({gateway})",
                    data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                        CONF_GATEWAY: gateway,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
            description_placeholders={
                "gateway_help": "Found on your router as EWH_REM4 — use the MAC address (e.g. AABBCCDDEEFF)"
            },
        )
