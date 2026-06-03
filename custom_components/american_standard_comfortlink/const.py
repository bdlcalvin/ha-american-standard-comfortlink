DOMAIN = "american_standard_comfortlink"

BASE_URL = "https://www.htp-net.remotethermo.com/api/v2"
APP_ID = "com.remotethermo.htpnet"
APP_VERSION = "6.0.14.40302"
# The API is behind a WAF that 403s unknown User-Agents (e.g. aiohttp's
# default). Must match the app's HTTP client identifier.
USER_AGENT = "ktor-client"

CONF_GATEWAY = "gateway"

# opMode integer -> ComfortLink app mode name.
# Confirmed by testing each mode in the app against the API on 2026-06-01.
OP_MODE_ECO = 0      # "Eco"
OP_MODE_COMFORT = 1  # "Comfort"
OP_MODE_FAST = 2     # "Fast"
OP_MODE_IMEMORY = 3  # "i-Memory"

# The cloud API rate-limits aggressively: ~6 requests in 2 min triggers an
# HTTP 429 block lasting several minutes. Poll conservatively.
SCAN_INTERVAL_SECONDS = 120
