"""The Mario Kart Wii: Retro Rewind RWFC integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import RwfcDataUpdateCoordinator

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RWFC from a config entry."""
    # Initialize the domain data structure if it doesn't exist
    hass.data.setdefault(DOMAIN, {"coordinators": {}, "global_sensors_added": False})

    # Use a single, shared coordinator
    if not hass.data[DOMAIN].get("coordinator"):
        coordinator = RwfcDataUpdateCoordinator(hass)
        await coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN]["coordinator"] = coordinator
    
    coordinator = hass.data[DOMAIN]["coordinator"]
    hass.data[DOMAIN]["coordinators"][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN]["coordinators"].pop(entry.entry_id)
        # If no more entries are configured, clean up the coordinator
        if not hass.data[DOMAIN]["coordinators"]:
            hass.data[DOMAIN].pop("coordinator")
            hass.data[DOMAIN]["global_sensors_added"] = False


    return unload_ok