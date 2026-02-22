# Envertech Local Integration for Home Assistant 🌞🔌

**Local-only** monitoring for Envertech microinverters – **no cloud, no internet** needed after setup! 🚀

[![HACS Repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jimmybonesde&repository=Envertech_local&category=integration)
[![GitHub Release](https://img.shields.io/github/v/release/jimmybonesde/Envertech_local?style=for-the-badge&logo=github&color=green)](https://github.com/jimmybonesde/Envertech_local/releases)
[![GitHub Stars](https://img.shields.io/github/stars/jimmybonesde/Envertech_local?style=for-the-badge&logo=github&color=yellow)](https://github.com/jimmybonesde/Envertech_local/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

This is a **maintained fork** of the original by [Kaiserdragon2](https://github.com/Kaiserdragon2/Envertech_local) with added daily/monthly/yearly production tracking.

### 🔥 What This Integration Does

Connects **directly** to your Envertech inverter via local TCP – reads real-time data and turns it into beautiful sensors in Home Assistant.  
No cloud calls, no account, no data leaves your network! 🔒

### ✨ Features at a Glance

- 🏠 **Fully local** polling (TCP) – zero cloud dependency  
- ⚡ Real-time per-panel & global values  
- 📈 **Daily, monthly & yearly production** sensors (perfect for Energy Dashboard)  
- 🌡️ Voltage, power, energy, temperature, frequency, firmware & serial numbers  
- 🛡️ Stable entity creation – no more disappearing P1 sensors  
- 🇬🇧🇩🇪 English & German translations included  
- ❤️ Optimized for Home Assistant Energy & Lovelace cards

### 🚀 Installation

#### Via HACS (recommended & fastest)

1. Go to **HACS → Integrations** → click the three dots (top right) → **Custom repositories**  
2. Add this URL:  
   `https://github.com/jimmybonesde/Envertech_local`  
3. Category: **Integration** → Add  
4. Search for **Envertech Local (Fork)** → Install  
5. **Restart Home Assistant**  
6. Go to **Settings → Devices & Services → + Add Integration** → search “Envertech”

#### Manual Installation

1. Download or clone this repo  
2. Copy the folder `custom_components/envertech_local` into your `config/custom_components/` directory  
3. Restart Home Assistant  
4. Add via UI (as above)

### ⚙️ Configuration

1. **Settings → Devices & Services → + Add Integration**  
2. Search for **Envertech Local**  
3. Enter your inverter’s **IP address** (e.g. 192.168.1.100)  
4. Enter the **TCP port** (default: 8899)  
5. Submit → all sensors appear automatically 🎉

### 📊 Created Sensors (Examples)

- `sensor.envertech_[sn]_p1_input_voltage` → Panel 1 input voltage (V)  
- `sensor.envertech_[sn]_p1_power` → Panel 1 current power (W)  
- `sensor.envertech_[sn]_total_energy` → Lifetime total energy (kWh)  
- `sensor.envertech_[sn]_energy_daily`   → **Today's production** (kWh since midnight)  
- `sensor.envertech_[sn]_energy_monthly` → **This month's production** (kWh)  
- `sensor.envertech_[sn]_energy_yearly`  → **This year's production** (kWh)

### 🛠️ Supported Devices

- Most Envertech microinverters with local TCP (EMT series, etc.)  
- Tested with 1–4+ panel setups  
- If your model works or doesn't – please open an issue! 🙏

### 📄 License & Credits

Original work Copyright (c) [Year] Kaiserdragon2  
Fork, enhancements & maintenance Copyright (c) 2026 JimmyBonesDE (@jimmybonesde)

Licensed under the **MIT License** – see [LICENSE](LICENSE) for details.

### 💬 Contributing

- Found a bug? → [Open an issue](https://github.com/jimmybonesde/Envertech_local/issues)  
- Got a feature idea? → Tell me!  
- Want to help? → Pull requests are very welcome ❤️

Made with ☕ & ❤️ in Karlsruhe, Germany

Enjoy your local solar monitoring! 🌞
