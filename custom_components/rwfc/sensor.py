"""Sensor platform for the RWFC integration."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_PLAYER_NAME,
    CONF_FRIEND_CODE,
    CONF_ENABLE_RETRO_VS,
    CONF_ENABLE_CUSTOM_VS,
    RK_MAP,
)
from .coordinator import RwfcDataUpdateCoordinator


@dataclass(frozen=True)
class RwfcSensorEntityDescription(SensorEntityDescription):
    """Describes a RWFC sensor entity."""


PLAYER_SENSORS: tuple[RwfcSensorEntityDescription, ...] = (
    RwfcSensorEntityDescription(
        key="status",
        translation_key="status",
        icon="mdi:information-outline",
    ),
    RwfcSensorEntityDescription(
        key="room_type",
        translation_key="room_type",
        icon="mdi:application-cog-outline",
        device_class=SensorDeviceClass.ENUM,
        options=[
            "retro_vs",
            "retro_tt",
            "retro_200cc",
            "custom_vs",
            "custom_tt",
            "custom_200cc",
            "none",
            "unknown",
        ],
    ),
    RwfcSensorEntityDescription(
        key="vr_pts",
        name="VR points",
        icon="mdi:counter",
        native_unit_of_measurement="VR",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RwfcSensorEntityDescription(
        key="player_count",
        name="Room Player Count",
        icon="mdi:google-classroom",
        native_unit_of_measurement="Players",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: RwfcDataUpdateCoordinator = hass.data[DOMAIN]["coordinators"][entry.entry_id]
    entities_to_add: list[SensorEntity] = []

    # Player-specific sensors
    if friend_code := entry.data.get(CONF_FRIEND_CODE):
        player_name = entry.data.get(CONF_PLAYER_NAME, f"Player {friend_code}")

        device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"{player_name} ({friend_code})",
            manufacturer="🗿 Bitte ein Git!",
            model="RetroWFC Player 🏎️",
            configuration_url="https://status.rwfc.net/",
        )

        for description in PLAYER_SENSORS:
            entities_to_add.append(
                RwfcPlayerSensor(coordinator, device_info, friend_code, description)
            )

    # Global sensors
    if not hass.data[DOMAIN].get("global_sensors_added"):
        global_sensors: list[SensorEntity] = []
        if entry.data.get(CONF_ENABLE_RETRO_VS):
            global_sensors.extend([
                RwfcGlobalRoomsSensor(coordinator, "vs_10", "🕹️Retro VS: Rooms", "rwfc_vsrooms"),
                RwfcGlobalPlayersSensor(coordinator, "vs_10", "🕹️Retro VS: Players", "rwfc_vsplayers"),
            ])
        if entry.data.get(CONF_ENABLE_CUSTOM_VS):
            global_sensors.extend([
                RwfcGlobalRoomsSensor(coordinator, "vs_20", "🚧Custom VS: Rooms", "rwfc_cvsrooms"),
                RwfcGlobalPlayersSensor(coordinator, "vs_20", "🚧Custom VS: Players", "rwfc_cvsplayers"),
            ])

        if global_sensors:
            entities_to_add.extend(global_sensors)
            hass.data[DOMAIN]["global_sensors_added"] = True

    if entities_to_add:
        async_add_entities(entities_to_add)


class RwfcPlayerSensor(CoordinatorEntity[RwfcDataUpdateCoordinator], SensorEntity):
    """Implementation of a RWFC player sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RwfcDataUpdateCoordinator,
        device_info: DeviceInfo,
        friend_code: str,
        description: RwfcSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self.friend_code = friend_code
        self._attr_device_info = device_info
        self._attr_unique_id = f"{friend_code}_{description.key}"
        self._attr_attribution = "Data provided by rwfc.net"
        self._player_data: dict[str, Any] | None = None
        self._session_data: dict[str, Any] | None = None
        self._update_local_data()  # Initial poll

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_local_data()
        self.async_write_ha_state()

    def _update_local_data(self) -> None:
        """Update local player and session data based on coordinator data."""
        self._player_data = None
        self._session_data = None
        for session in self.coordinator.data or []:
            players = session.get("players")
            if isinstance(players, dict):
                for player in players.values():
                    if player.get("fc") == self.friend_code:
                        self._player_data = player
                        self._session_data = session
                        return

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        key = self.entity_description.key

        if key == "status":
            if not self._session_data:
                return "🚫 Offline"
            suspend = self._session_data.get("suspend", 0)
            player_count = len(self._session_data.get("players", {}) or {})
            if suspend == 1 and player_count < 12:
                return "track_selection"
            if player_count >= 12:
                return "ongoing_race_full"
            return "ongoing_race"

        if key == "room_type":
            if not self._session_data:
                return "none"
            rk = self._session_data.get("rk", "unknown")
            return RK_MAP.get(rk, "unknown").split(".")[-1]

        if key == "vr_pts":
            if self._player_data and "ev" in self._player_data:
                return self._player_data["ev"]
            return None

        if key == "player_count":
            if not self._session_data:
                return 0
            return len(self._session_data.get("players", {}) or {})

        return None

    @property
    def translation_placeholders(self) -> dict[str, Any]:
        """Placeholders for translated strings (used by frontend)."""
        if self.entity_description.key == "status":
            count = 0
            if self._session_data:
                players = self._session_data.get("players")
                if isinstance(players, dict):
                    count = len(players)
            return {"player_count": count}
        return {}


# --- Global Sensors ---

class RwfcGlobalBaseSensor(CoordinatorEntity[RwfcDataUpdateCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: RwfcDataUpdateCoordinator, name: str, unique_id: str):
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_attribution = "Data provided by rwfc.net"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "global")},
            name="Retro Rewind Status",
            manufacturer="🗿 Bitte ein Git!",
            model="🌎RetroWFC Status",
        )


class RwfcGlobalPlayersSensor(RwfcGlobalBaseSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "Players"
    _attr_icon = "mdi:account-group"

    def __init__(self, coordinator: RwfcDataUpdateCoordinator, rk_filter: str, name: str, unique_id: str):
        super().__init__(coordinator, name, unique_id)
        self._rk_filter = rk_filter

    @property
    def native_value(self) -> int:
        if not self.coordinator.data:
            return 0
        return sum(len(s.get("players", {}) or {}) for s in self.coordinator.data if s.get("rk") == self._rk_filter)


class RwfcGlobalRoomsSensor(RwfcGlobalBaseSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "Rooms"

    def __init__(self, coordinator: RwfcDataUpdateCoordinator, rk_filter: str, name: str, unique_id: str):
        super().__init__(coordinator, name, unique_id)
        self._rk_filter = rk_filter
        self._attr_icon = "mdi:hammer-wrench" if "Custom" in name else "mdi:controller-classic-outline"

    @property
    def native_value(self) -> int:
        if not self.coordinator.data:
            return 0
        return sum(1 for s in self.coordinator.data if s.get("rk") == self._rk_filter)