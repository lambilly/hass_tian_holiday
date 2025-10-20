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
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# 重试配置
MAX_RETRIES = 2
RETRY_DELAY = 300  # 5分钟，单位秒

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置传感器条目."""
    api_key = entry.data["api_key"]
    
    sensor = TianHolidaySensor(hass, api_key, entry)
    await sensor.async_first_update()  # 立即执行第一次更新
    
    async_add_entities([sensor])


class TianHolidaySensor(SensorEntity):
    """节假日传感器实体."""

    def __init__(self, hass: HomeAssistant, api_key: str, entry: ConfigEntry) -> None:
        """初始化传感器."""
        self.hass = hass
        self.api_key = api_key
        self._attr_unique_id = f"{entry.entry_id}_jie_jia_ri"
        self._attr_name = "节假日"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Node-RED",
            name="信息查询",
        )
        self._data = {}
        self._update_time = ""  # 新增：更新时间字段
        self._retry_count = 0
        self._unsub_timer = None

    @property
    def state(self) -> str:
        """返回实体状态."""
        return self._data.get("day_type", "未知")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """返回额外状态属性."""
        if not self._data:
            return {}
        
        data = self._data.copy()
        # 添加更新时间属性
        data["update_time"] = self._update_time
        
        # 展平嵌套字典
        attributes = {}
        for key, value in data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    attributes[sub_key] = sub_value
            else:
                attributes[key] = value
        return attributes

    async def async_added_to_hass(self) -> None:
        """当实体添加到HA时."""
        # 设置每天00:01的定时更新
        self._unsub_timer = async_track_time_change(
            self.hass, 
            self._async_scheduled_update, 
            hour=0, minute=1, second=0
        )

    async def async_will_remove_from_hass(self) -> None:
        """当实体从HA移除时."""
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None

    async def async_first_update(self) -> None:
        """执行第一次更新."""
        await self._async_update_holiday_data()

    async def _async_scheduled_update(self, now=None) -> None:
        """定时更新回调."""
        _LOGGER.info("执行定时节假日数据更新")
        self._retry_count = 0  # 重置重试计数
        await self._async_update_holiday_data()

    def _get_current_time_string(self) -> str:
        """获取当前时间的格式化字符串."""
        # 使用 Home Assistant 的时区设置
        now = dt_util.now()
        return now.strftime("%Y-%m-%d %H:%M:%S")

    async def _async_update_holiday_data(self) -> None:
        """更新节假日数据."""
        try:
            data = await self.fetch_holiday_data()
            if data:
                self._data = data
                # 更新成功时设置更新时间
                self._update_time = self._get_current_time_string()
                self._retry_count = 0  # 成功时重置重试计数
                self.async_write_ha_state()
                _LOGGER.info("节假日数据更新成功，更新时间: %s", self._update_time)
            else:
                raise Exception("获取到的数据为空")
                
        except Exception as err:
            _LOGGER.error("获取节假日数据失败: %s", err)
            await self._async_handle_retry()

    async def _async_handle_retry(self) -> None:
        """处理重试逻辑."""
        self._retry_count += 1
        
        if self._retry_count <= MAX_RETRIES:
            _LOGGER.info("将在 %d 秒后重试 (第 %d/%d 次)", 
                        RETRY_DELAY, self._retry_count, MAX_RETRIES)
            
            # 使用async_call_later进行延迟重试
            self.hass.loop.call_later(
                RETRY_DELAY, 
                lambda: self.hass.async_create_task(self._async_update_holiday_data())
            )
        else:
            _LOGGER.error("已达到最大重试次数 (%d次)，停止重试", MAX_RETRIES)
            self._retry_count = 0  # 重置计数，等待下一次定时更新

    async def fetch_holiday_data(self) -> dict:
        """从API获取节假日数据."""
        url = f"https://apis.tianapi.com/jiejiari/index?key={self.api_key}"
        
        async with async_timeout.timeout(10):
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

    async def async_update(self) -> None:
        """手动更新实体."""
        await self._async_update_holiday_data()