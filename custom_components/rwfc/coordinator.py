"""DataUpdateCoordinator for the RWFC integration."""
from datetime import timedelta
import logging

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, API_URL, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class RwfcDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching RWFC data from the API."""

    def __init__(self, hass):
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.websession = async_get_clientsession(hass)

    async def _async_update_data(self):
        """Fetch data from API."""
        headers = {"User-Agent": "HomeAssistant/69.420"}
        try:
            response = await self.websession.get(API_URL, headers=headers)
            response.raise_for_status()
            data = await response.json()
            return data if data else []
        except Exception as err:
            raise UpdateFailed(f"Error communicating with RWFC API: {err}") from err