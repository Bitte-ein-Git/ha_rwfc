"""Sensor platform for the RWFC integration."""
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_PLAYER_NAME, CONF_FRIEND_CODE, RK_MAP
from .coordinator import RwfcDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: RwfcDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    player_name = entry.data[CONF_PLAYER_NAME]
    friend_code = entry.data[CONF_FRIEND_CODE]

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=player_name,
        manufacturer="Bitte-ein-Git!",
        model="🏎️ RWFC: player sensor",
        configuration_url="http://rwfc.net/",
    )
    
    if not hass.data[DOMAIN].get("global_sensors_added"):
        global_sensors = [
            RwfcGlobalroomsSensor(coordinator, "vs_10", "Retro VS rooms", "rwfc_vsrooms"),
            RwfcGlobalroomsSensor(coordinator, "vs_20", "Custom VS rooms", "rwfc_cvsrooms"),
            RwfcGlobalPlayersSensor(coordinator, "vs_10", "Retro VS players", "rwfc_vsplayers"),
            RwfcGlobalPlayersSensor(coordinator, "vs_20", "Custom VS players", "rwfc_cvsplayers"),
        ]
        async_add_entities(global_sensors)
        hass.data[DOMAIN]["global_sensors_added"] = True


    player_sensors = [
        PlayerStatusSensor(coordinator, device_info, player_name, friend_code),
        Playerroomsensor(coordinator, device_info, player_name, friend_code),
        PlayerVRPTSensor(coordinator, device_info, player_name, friend_code),
        PlayerCountSensor(coordinator, device_info, player_name, friend_code),
    ]

    async_add_entities(player_sensors)


class RwfcBaseSensor(CoordinatorEntity[RwfcDataUpdateCoordinator], SensorEntity):
    """Base class for RWFC sensors."""
    _attr_has_entity_name = True

    def __init__(self, coordinator: RwfcDataUpdateCoordinator):
        super().__init__(coordinator)
        self._attr_attribution = "Data provided by rwfc.net"


class PlayerSensor(RwfcBaseSensor):
    """Base class for player-specific sensors."""

    def __init__(
        self,
        coordinator: RwfcDataUpdateCoordinator,
        device_info: DeviceInfo,
        player_name: str,
        friend_code: str,
    ):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self.player_name = player_name
        self.friend_code = friend_code
        self._player_data = None
        self._session_data = None
        self._update_local_data()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_local_data()
        self.async_write_ha_state()

    def _update_local_data(self):
        """Update local player and session data based on coordinator data."""
        self._player_data = None
        self._session_data = None
        for session in self.coordinator.data or []:
            if "players" in session and isinstance(session["players"], dict):
                for player in session["players"].values():
                    if player.get("fc") == self.friend_code:
                        self._player_data = player
                        self._session_data = session
                        return


class PlayerStatusSensor(PlayerSensor):
    """Sensor for the player's overall status."""
    
    def __init__(self, coordinator, device_info, player_name, friend_code):
        super().__init__(coordinator, device_info, player_name, friend_code)
        self._attr_unique_id = f"{friend_code}_status"
        self._attr_name = "🏎️ RWFC: Status" 

    @property
    def native_value(self):
        if not self._session_data:
            return "🚫 OFFLINE"
        
        rk = self._session_data.get("rk", "unknown")
        room_name = RK_MAP.get(rk, rk)
        player_count = len(self._session_data.get("players", {}))
        
        suffix = '(lobby full!)' if player_count >= 12 else f'({player_count} players)'
        return f"{room_name} {suffix}"


class Playerroomsensor(PlayerSensor):
    """Sensor for the player's current room type."""

    def __init__(self, coordinator, device_info, player_name, friend_code):
        super().__init__(coordinator, device_info, player_name, friend_code)
        self._attr_unique_id = f"{friend_code}_room"
        self._attr_name = "🏎️ RWFC: room type"

    @property
    def native_value(self):
        if not self._session_data:
            return "none"
        
        rk = self._session_data.get("rk", "unknown")
        return RK_MAP.get(rk, rk)


class PlayerVRPTSensor(PlayerSensor):
    """Sensor for the player's VS points (EV)."""

    def __init__(self, coordinator, device_info, player_name, friend_code):
        super().__init__(coordinator, device_info, player_name, friend_code)
        self._attr_unique_id = f"{friend_code}_vs_ev"
        self._attr_name = "🏎️ RWFC: 🏆 R-points"
        self._attr_native_unit_of_measurement = "R-points"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        if self._player_data and "ev" in self._player_data:
            return self._player_data["ev"]
        return None


class PlayerCountSensor(PlayerSensor):
    """Sensor for the player count in the player's room."""

    def __init__(self, coordinator, device_info, player_name, friend_code):
        super().__init__(coordinator, device_info, player_name, friend_code)
        self._attr_unique_id = f"{friend_code}_players"
        self._attr_name = "🏎️ RWFC: room player count"

    @property
    def native_value(self):
        if not self._session_data:
            return "none"

        player_count = len(self._session_data.get("players", {}))
        suspend = self._session_data.get("suspend", 0)

        if suspend == 1 and player_count < 12:
            return f'🗺️ 𝙩𝙧𝙖𝙘𝙠 𝙨𝙚𝙡𝙚𝙘𝙩𝙞𝙤𝙣 | 👥 {player_count} players'
        
        suffix = '(lobby full!)' if player_count >= 12 else f'👥 {player_count} players'
        return f'🌎 𝗼𝗻𝗴𝗼𝗶𝗻𝗴 𝗿𝗮𝗰𝗲 | {suffix}'


class RwfcGlobalBaseSensor(RwfcBaseSensor):
    """Base class for global sensors."""
    _attr_has_entity_name = True

    def __init__(self, coordinator: RwfcDataUpdateCoordinator, name: str, unique_id: str):
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "global")},
            name="🏎️ Retro Rewind",
            manufacturer="Bitte-ein-Git!",
        )

class RwfcGlobalPlayersSensor(RwfcGlobalBaseSensor):
    """Sensor for global player counts in specific modes."""
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "players"

    def __init__(self, coordinator: RwfcDataUpdateCoordinator, rk_filter: str, name: str, unique_id: str):
        super().__init__(coordinator, name, unique_id)
        self._rk_filter = rk_filter

    @property
    def native_value(self):
        if not self.coordinator.data:
            return 0
        return sum(
            len(session.get("players", {}))
            for session in self.coordinator.data
            if session.get("rk") == self._rk_filter
        )


class RwfcGlobalroomsSensor(RwfcGlobalBaseSensor):
    """Sensor for global room counts in specific modes."""
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "rooms"

    def __init__(self, coordinator: RwfcDataUpdateCoordinator, rk_filter: str, name: str, unique_id: str):
        super().__init__(coordinator, name, unique_id)
        self._rk_filter = rk_filter

    @property
    def native_value(self):
        if not self.coordinator.data:
            return 0
        return sum(
            1 for session in self.coordinator.data if session.get("rk") == self._rk_filter
        )