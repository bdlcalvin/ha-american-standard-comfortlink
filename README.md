# American Standard ComfortLink — Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/bdlcalvin/ha-american-standard-comfortlink?include_prereleases)](https://github.com/bdlcalvin/ha-american-standard-comfortlink/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Maintenance](https://img.shields.io/maintenance/yes/2026.svg)](https://github.com/bdlcalvin/ha-american-standard-comfortlink)

A custom [Home Assistant](https://www.home-assistant.io/) integration for
**American Standard ComfortLink** Wi-Fi heat pump water heaters. It lets you
monitor and control your water heater from Home Assistant: read the water
temperature, set the target temperature, change the operating mode, toggle
boost, and see what the heat pump is doing.

> **Disclaimer:** This is an unofficial, community-built integration. It is not
> affiliated with, endorsed by, or supported by American Standard, Ariston, or
> HTP. It works by talking to the same cloud API the official **ComfortLink** app
> uses (`com.remotethermo.htpnet`). Use at your own risk; the cloud API can
> change at any time.

## Features

- 🌡️ Current water temperature & comfort setpoint (sensors)
- 🎛️ `water_heater` entity: on/off, target temperature, and operating mode
  (Eco / Comfort / Fast / i-Memory)
- ⚡ Boost (resistance heating) switch
- ♨️ Heat pump state sensor (off / standby / heating / anti-legionella)

## Supported devices

American Standard ComfortLink heat pump water heaters that are managed through
the **ComfortLink** mobile app (these are built on the Ariston/HTP
`remotethermo.com` "Velis" cloud platform). If your heater uses the ComfortLink
app and logs in with an email + password, it should work.

## Requirements

- Home Assistant **2023.1** or newer
- A ComfortLink account (email + password) already set up with your heater in the
  app
- The heater online and connected to the internet (this is a **cloud**
  integration — there is no local control)

## Installation

### HACS (recommended)

1. In Home Assistant, open **HACS → Integrations**.
2. Click the **⋮** menu → **Custom repositories**.
3. Add `https://github.com/bdlcalvin/ha-american-standard-comfortlink`,
   category **Integration**, and click **Add**.
4. Find **American Standard ComfortLink** in the list and **Download** it.
5. **Restart Home Assistant.**

### Manual

1. Copy `custom_components/american_standard_comfortlink/` into your Home
   Assistant `config/custom_components/` directory.
2. **Restart Home Assistant.**

## Configuration

1. Go to **Settings → Devices & Services → + Add Integration**.
2. Search for **American Standard ComfortLink**.
3. Enter:
   - **Email** — your ComfortLink account email
   - **Password** — your ComfortLink account password
   - **Gateway ID** — your heater's 12-character ID (its Wi-Fi MAC address,
     no colons, e.g. `AABBCCDDEEFF`)

> **Finding your Gateway ID:** it's the heater's Wi-Fi MAC address. The device
> usually appears on your router's client list with a hostname like `EWH_REM4` —
> use that client's MAC, written as 12 hex characters with no colons.

## Entities

| Entity | Type | Description |
|---|---|---|
| `water_heater.*` | Water heater | On/off, target temperature (104–151 °F), operating mode |
| `sensor.*_water_temperature` | Sensor | Current water temperature |
| `sensor.*_comfort_setpoint` | Sensor | Target comfort temperature |
| `sensor.*_heat_pump_state` | Sensor | off / standby / heating / anti_legionella |
| `switch.*_boost_mode` | Switch | Boost (resistance heating) on/off |

### Operating modes

The operating modes use the ComfortLink app's own names:

| HA Operation | App mode | API `opMode` |
|---|---|---|
| `Off` | Off | — (uses the on/off control) |
| `Eco` | Eco | 0 |
| `Comfort` | Comfort | 1 |
| `Fast` | Fast | 2 |
| `i-Memory` | i-Memory | 3 |

### Heat pump state (`hpState`)

| Value | Label | Meaning |
|---|---|---|
| 0 | `off` | Heat pump off |
| 1 | `standby` | Idle / not actively heating |
| 2 | `heating` | Normal heat-pump heating toward setpoint |
| 3 | `anti_legionella` | Periodic high-temperature sanitizing cycle |

> The exact `hpState` enum is partially inferred. The raw integer is always
> available as the `raw_value` attribute on the sensor, so you can confirm the
> mapping against your own unit.

## Troubleshooting

**"Invalid authentication" during setup**
- Confirm the email/password work by signing in to the ComfortLink app first.
- Double-check the Gateway ID (12 hex characters, no colons).

**Entities show "Unavailable"**
- Usually a temporary cloud hiccup or rate-limit. The integration keeps the last
  known reading through brief blocks and recovers on the next poll. If it
  persists, reload the integration (**Settings → Devices & Services → American
  Standard ComfortLink → ⋮ → Reload**).

**Enable debug logging** (to report an issue), add to `configuration.yaml`:
```yaml
logger:
  logs:
    custom_components.american_standard_comfortlink: debug
```

## How it works

The heater's Wi-Fi module connects **outbound** to the cloud over MQTT/TLS;
there is no local API, so all control goes through `htp-net.remotethermo.com`.
The integration authenticates with your email/password to obtain a session
token (refreshed automatically), and polls the cloud REST API every **120
seconds**. The cloud rate-limits aggressive polling, so the interval is
deliberately conservative and the integration serves cached data during any
temporary block rather than going unavailable.

## Contributing

Issues and pull requests are welcome. Because device behavior varies across
models, real-world confirmation of the mode and `hpState` mappings on different
units is especially helpful.

## License

Released under the MIT License. Not affiliated with American Standard, Ariston,
or HTP.
