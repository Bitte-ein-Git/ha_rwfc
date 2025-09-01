"""Constants for the RWFC integration."""

DOMAIN = "rwfc"

# Configuration
CONF_PLAYER_NAME = "player_name"
CONF_FRIEND_CODE = "friend_code"
CONF_ENABLE_RETRO_VS = "enable_retro_vs"
CONF_ENABLE_CUSTOM_VS = "enable_custom_vs"

# API
API_URL = "http://rwfc.net/api/groups"
SCAN_INTERVAL_SECONDS = 5

# Sensor Maps
RK_MAP = {
    'vs_10': 'state.sensor.rwfc_room_type.retro_vs',
    'vs_11': 'state.sensor.rwfc_room_type.retro_tt',
    'vs_12': 'state.sensor.rwfc_room_type.retro_200cc',
    'vs_20': 'state.sensor.rwfc_room_type.custom_vs',
    'vs_21': 'state.sensor.rwfc_room_type.custom_tt',
    'vs_22': 'state.sensor.rwfc_room_type.custom_200cc'
}