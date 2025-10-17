"""配置流 for 天聚数行-节假日."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

class TianHolidayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """处理配置流."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """处理用户步骤."""
        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(
                title="天聚数行-节假日",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("api_key"): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """创建选项流."""
        return TianHolidayOptionsFlow(config_entry)


class TianHolidayOptionsFlow(config_entries.OptionsFlow):
    """处理选项流."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """初始化选项流."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """管理选项."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "api_key",
                        default=self.config_entry.data.get("api_key"),
                    ): str,
                }
            ),
        )