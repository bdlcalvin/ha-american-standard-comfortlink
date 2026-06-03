"""HTTP client for the remotethermo.com API."""
from __future__ import annotations

import logging
import uuid
from typing import Any

import aiohttp

from .const import APP_ID, APP_VERSION, BASE_URL, USER_AGENT

_LOGGER = logging.getLogger(__name__)

LOGIN_URL = f"{BASE_URL}/accounts/login"
SESSION_URL = f"{BASE_URL}/accounts/newMobileAppUserSession"


class CannotConnect(Exception):
    pass


class InvalidAuth(Exception):
    pass


class RateLimited(Exception):
    """Raised on HTTP 429 — the API is temporarily blocking requests."""


class ComfortLinkAPI:
    def __init__(self, session: aiohttp.ClientSession, email: str, password: str) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._token: str | None = None
        self._device_uuid = str(uuid.uuid4()).replace("-", "")

    async def login(self) -> None:
        """Authenticate and store the ar.authtoken."""
        payload = {
            "usr": self._email,
            "pwd": self._password,
            "imp": False,
            "notTrack": True,
            "appInfo": {
                "os": 2,
                "appVer": APP_VERSION,
                "appId": APP_ID,
            },
        }
        try:
            async with self._session.post(
                LOGIN_URL,
                json=payload,
                headers={
                    "Accept": "application/json",
                    "x-app-version": APP_VERSION,
                    "User-Agent": USER_AGENT,
                },
            ) as resp:
                if resp.status in (401, 403):
                    raise InvalidAuth
                resp.raise_for_status()
                data = await resp.json()
        except aiohttp.ClientError as err:
            raise CannotConnect from err

        token = data.get("token") or data.get("authToken")
        if not token:
            raise InvalidAuth

        self._token = token
        await self._new_session()

    async def _new_session(self) -> None:
        payload = {
            "TimeZoneOffsetAsSeconds": -18000,
            "UserId": self._email,
            "UserCountry": "US",
            "MobileOperatingSystem": 2,
            "AppId": APP_ID,
            "AppVersion": APP_VERSION,
            "MobileOperatingSystemVersion": "17.0",
            "DeviceUuid": f"ha{self._device_uuid[:32]}",
        }
        try:
            async with self._session.post(
                SESSION_URL, json=payload, headers=self._headers()
            ) as resp:
                resp.raise_for_status()
        except aiohttp.ClientError as err:
            _LOGGER.warning("newMobileAppUserSession failed: %s", err)

    def _headers(self) -> dict[str, str]:
        return {
            "ar.authtoken": self._token or "",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-app-version": APP_VERSION,
            "User-Agent": USER_AGENT,
        }

    async def _reauth_and_retry_get(self, url: str) -> Any:
        await self.login()
        async with self._session.get(url, headers=self._headers()) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _reauth_and_retry_post(self, url: str, body: Any) -> None:
        await self.login()
        async with self._session.post(url, json=body, headers=self._headers()) as resp:
            resp.raise_for_status()

    async def get_plant_data(self, gateway: str) -> dict[str, Any]:
        url = f"{BASE_URL}/velis/slpPlantData/{gateway}?umSys=us"
        try:
            async with self._session.get(url, headers=self._headers()) as resp:
                if resp.status == 401:
                    return await self._reauth_and_retry_get(url)
                if resp.status == 429:
                    raise RateLimited
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientError as err:
            raise CannotConnect from err

    async def get_plant_settings(self, gateway: str) -> dict[str, Any]:
        url = f"{BASE_URL}/velis/slpPlantData/{gateway}/plantSettings?umSys=us"
        try:
            async with self._session.get(url, headers=self._headers()) as resp:
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientError as err:
            raise CannotConnect from err

    async def get_energy_report(self, gateway: str, usage: str) -> list[dict]:
        url = f"{BASE_URL}/remote/reports/{gateway}/consSequencesApi8?usages={usage}"
        try:
            async with self._session.get(url, headers=self._headers()) as resp:
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientError as err:
            raise CannotConnect from err

    async def set_switch(self, gateway: str, on: bool) -> None:
        await self._post(f"{BASE_URL}/velis/slpPlantData/{gateway}/switch", on)

    async def set_boost(self, gateway: str, on: bool) -> None:
        await self._post(f"{BASE_URL}/velis/slpPlantData/{gateway}/boost", on)

    async def set_operative_mode(self, gateway: str, new_mode: int, old_mode: int) -> None:
        await self._post(
            f"{BASE_URL}/velis/slpPlantData/{gateway}/operativeMode",
            {"new": new_mode, "old": old_mode},
        )

    async def set_temperature(self, gateway: str, new_temp: float, old_temp: float) -> None:
        await self._post(
            f"{BASE_URL}/velis/slpPlantData/{gateway}/temperatures?umSys=us",
            {"new": {"comfort": new_temp}, "old": {"comfort": old_temp}},
        )

    async def _post(self, url: str, body: Any) -> None:
        try:
            async with self._session.post(url, json=body, headers=self._headers()) as resp:
                if resp.status == 401:
                    await self._reauth_and_retry_post(url, body)
                    return
                resp.raise_for_status()
        except aiohttp.ClientError as err:
            raise CannotConnect from err
