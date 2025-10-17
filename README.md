# 天聚数行-节假日 Home Assistant 集成

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

这是一个用于获取中国节假日信息的 Home Assistant 自定义集成，基于天聚数行数据 API。

## 功能特性

- 📅 获取当日节假日信息
- 🏠 在 Home Assistant 中显示节假日状态
- 🔄 每天自动更新数据
- 📊 提供丰富的节假日属性信息
- 🇨🇳 完整的中文支持

## 安装

### 通过 HACS 安装（推荐）

1. 确保已安装 [HACS](https://hacs.xyz/)
2. 在 HACS 中点击「集成」
3. 点击右上角三个点，选择「自定义仓库」
4. 添加仓库地址：https://github.com/lambilly/hass_tian_holiday
5. 选择分类为「集成」，点击「添加」。搜索「天聚数行-实时动态」并安装
6. 重启 Home Assistant

### 手动安装

1. 将 `tian_holiday` 文件夹复制到 `custom_components` 目录
2. 重启 Home Assistant
3. 在集成页面添加「天聚数行-节假日」

## 配置

### 获取 API Key

1. 访问 [天聚数行数据](https://www.tianapi.com/)
2. 注册账号并登录
3. 在控制台找到「节假日」API
4. 申请 API Key

### 添加集成

1. 进入 Home Assistant
2. 点击「配置」->「设备与服务」
3. 点击「添加集成」
4. 搜索「天聚数行-节假日」
5. 输入您的 API Key
6. 完成配置

## 实体

集成会创建一个传感器实体：

- **实体ID**: `sensor.jie_jia_ri`
- **实体名称**: 节假日
- **状态**: 工作日 / 节假日 / 双休日 / 调休日

### 属性说明

| 属性名 | 说明 |
|--------|------|
| `date` | 当前日期 |
| `daycode` | 日期类型代码 |
| `weekday_cn` | 中文星期 |
| `lunar_year` | 农历年 |
| `lunar_month` | 农历月 |
| `lunar_day` | 农历日 |
| `info` | 节假日信息 |
| `holiday` | 节假日名称 |
| `name` | 节日名称 |
| `name_en` | 节日英文名称 |
| `isnotwork` | 是否工作日 |
| `wage` | 工资倍数 |
| `tip` | 提示信息 |
| `rest` | 休息信息 |
| `vacation_01` ~ `vacation_07` | 假期安排 |
| `remark_01` ~ `remark_04` | 备注信息 |

## 更新日志
v1.0.0
•	初始版本发布
•	支持基本的节假日查询功能
•	完整的属性展示

## 支持
如果遇到问题，请：
1.	检查 API Key 是否正确
2.	确认网络连接正常
3.	查看 Home Assistant 日志文件

## 许可证
MIT License

## 贡献
欢迎提交 Issue 和 Pull Request！


