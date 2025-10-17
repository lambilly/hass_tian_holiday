"""天聚数行-节假日传感器."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
import async_timeout
import voluptuous as vol
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=24)  # 每天更新一次

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置传感器条目."""
    api_key = entry.data["api_key"]
    
    coordinator = TianHolidayCoordinator(hass, api_key)
    await coordinator.async_config_entry_first_refresh()
    
    async_add_entities([TianHolidaySensor(coordinator, entry)])


class TianHolidayCoordinator(DataUpdateCoordinator):
    """数据更新协调器."""

    def __init__(self, hass: HomeAssistant, api_key: str) -> None:
        """初始化协调器."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.api_key = api_key

    async def _async_update_data(self):
        """获取最新数据."""
        try:
            async with async_timeout.timeout(10):
                return await self.fetch_holiday_data()
        except Exception as err:
            _LOGGER.error("获取节假日数据错误: %s", err)
            return {}

    async def fetch_holiday_data(self):
        """从API获取节假日数据."""
        url = f"https://apis.tianapi.com/jiejiari/index?key={self.api_key}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"API请求失败: {response.status}")
                
                data = await response.json()
                
                if data.get("code") != 200:
                    raise Exception(f"API返回错误: {data.get('msg')}")
                
                result = data.get("result", {})
                if not result or "list" not in result or not result["list"]:
                    return {}
                
                holiday_data = result["list"][0]
                return self.process_holiday_data(holiday_data)

    def process_holiday_data(self, data: dict) -> dict:
        """处理节假日数据."""
        DAYCODE_MAP = {
            0: "工作日",
            1: "节假日", 
            2: "双休日",
            3: "调休日"
        }
        
        # 处理假期数组
        vacation = data.get("vacation", [])
        vacation_dict = {}
        for i in range(7):
            key = f"vacation_{str(i+1).zfill(2)}"
            vacation_dict[key] = vacation[i] if i < len(vacation) else ""
        
        # 处理备注数组
        remark = data.get("remark", [])
        remark_dict = {}
        for i in range(4):
            key = f"remark_{str(i+1).zfill(2)}"
            remark_dict[key] = remark[i] if i < len(remark) else ""
        
        return {
            "date": data.get("date", ""),
            "daycode": data.get("daycode", ""),
            "day_type": DAYCODE_MAP.get(data.get("daycode", 0), ""),
            "weekday": data.get("weekday", ""),
            "weekday_cn": data.get("cnweekday", ""),
            "lunar_year": data.get("lunaryear", ""),
            "lunar_month": data.get("lunarmonth", ""),
            "lunar_day": data.get("lunarday", ""),
            "info": data.get("info", ""),
            "start": data.get("start", 0),
            "now": data.get("now", 0),
            "end": data.get("end", 0),
            "holiday": data.get("holiday", ""),
            "name": data.get("name", ""),
            "name_en": data.get("enname", ""),
            "isnotwork": data.get("isnotwork", 1),
            "wage": data.get("wage", 0),
            "tip": data.get("tip", ""),
            "rest": data.get("rest", ""),
            "vacation": vacation_dict,
            "remark": remark_dict
        }


class TianHolidaySensor(SensorEntity):
    """节假日传感器实体."""

    def __init__(self, coordinator: TianHolidayCoordinator, entry: ConfigEntry) -> None:
        """初始化传感器."""
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_jie_jia_ri"
        self._attr_name = "节假日"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Node-RED",
            name="信息查询",
        )

    @property
    def state(self) -> str:
        """返回实体状态."""
        if self.coordinator.data:
            return self.coordinator.data.get("day_type", "未知")
        return "未知"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """返回额外状态属性."""
        if not self.coordinator.data:
            return {}
        
        data = self.coordinator.data.copy()
        # 展平嵌套字典
        attributes = {}
        for key, value in data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    attributes[sub_key] = sub_value
            else:
                attributes[key] = value
        return attributes

    @property
    def should_poll(self) -> bool:
        """不需要轮询，使用协调器."""
        return False

    async def async_added_to_hass(self) -> None:
        """当实体添加到HA时."""
        self.async_on_remove(
            self.coordinator.async_add_listener(
                self.async_write_ha_state
            )
        )

    async def async_update(self) -> None:
        """更新实体."""
        await self.coordinator.async_request_refresh()