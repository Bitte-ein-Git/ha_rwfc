"""Config flow for Mario Kart Wii RWFC integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_PLAYER_NAME, CONF_FRIEND_CODE

class RwfcConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RWFC."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            if not user_input[CONF_FRIEND_CODE]:
                errors["base"] = "invalid_friend_code"
            else:
                await self.async_set_unique_id(user_input[CONF_FRIEND_CODE])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_PLAYER_NAME], data=user_input
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_PLAYER_NAME): str,
                vol.Required(CONF_FRIEND_CODE): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )