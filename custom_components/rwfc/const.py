"""Constants for the RWFC integration."""

DOMAIN = "rwfc"

# Configuration
CONF_PLAYER_NAME = "player_name"
CONF_FRIEND_CODE = "friend_code"

# API
API_URL = "http://rwfc.net/api/groups"
SCAN_INTERVAL_SECONDS = 5

# Sensor Maps
RK_MAP = {
    'vs_10': '🕹️ Retro VS',
    'vs_11': '⏰ Retro ZF',
    'vs_12': '🚀 Retro 200cc',
    'vs_20': '🚧 Custom VS',
    'vs_21': '⏰ Custom ZF',
    'vs_22': '💥 Custom 200cc',
    'vs_668': '🏁 CTGP-C',
    'vs_69': '🏁 Insane Kart',
    'vs_-1': '🚗 Standard',
    'vs': '🚗 Standard',
    'vs_666': 'Luminous'
}