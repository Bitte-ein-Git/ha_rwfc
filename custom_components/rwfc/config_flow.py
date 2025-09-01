"""Config flow for Mario Kart Wii RWFC integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_PLAYER_NAME,
    CONF_FRIEND_CODE,
    CONF_ENABLE_RETRO_VS,
    CONF_ENABLE_CUSTOM_VS,
)


class RwfcConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RWFC."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            friend_code = user_input.get(CONF_FRIEND_CODE)
            enable_retro = user_input.get(CONF_ENABLE_RETRO_VS)
            enable_custom = user_input.get(CONF_ENABLE_CUSTOM_VS)

            if not friend_code and not enable_retro and not enable_custom:
                errors["base"] = "at_least_one_option"
            else:
                if friend_code:
                    await self.async_set_unique_id(friend_code)
                    self._abort_if_unique_id_configured()
                    title = user_input.get(
                        CONF_PLAYER_NAME, f"RWFC Player ({friend_code})"
                    )
                else:
                    # Create a unique ID for global-only sensors
                    await self.async_set_unique_id("rwfc_global_sensors")
                    self._abort_if_unique_id_configured()
                    title = "RWFC Global Sensors"

                return self.async_create_entry(title=title, data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_PLAYER_NAME): str,
                vol.Optional(CONF_FRIEND_CODE): str,
                vol.Optional(CONF_ENABLE_RETRO_VS, default=False): bool,
                vol.Optional(CONF_ENABLE_CUSTOM_VS, default=False): bool,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )