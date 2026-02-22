# Envertech Local Integration for Home Assistant

A custom, **local-only** integration for Envertech microinverters – no cloud required.

[![HACS Repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jimmybonesde&repository=Envertech_local&category=integration)

[![GitHub Release](https://img.shields.io/github/v/release/jimmybonesde/Envertech_local?style=for-the-badge&logo=github&color=green)](https://github.com/jimmybonesde/Envertech_local/releases)
[![GitHub Stars](https://img.shields.io/github/stars/jimmybonesde/Envertech_local?style=for-the-badge&logo=github&color=yellow)](https://github.com/jimmybonesde/Envertech_local/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

**This is a maintained fork** of the original integration by [Kaiserdragon2](https://github.com/Kaiserdragon2/Envertech_local).

### Key Improvements in this Fork

- Added **daily, monthly, and yearly production** sensors (`energy_daily`, `energy_monthly`, `energy_yearly`)
- Removed problematic `RestoreEntity` logic → much more stable initialization (no more missing P1 sensors)
- Improved availability checks for panel sensors
- Cleaned up code structure and added better logging
- Full English & German translations

### Features

- 🔌 **Fully local** communication with Envertech inverters (TCP)
- ☁️ **Zero cloud dependency**
- ⚡ Real-time monitoring of power, voltage, temperature, frequency, etc.
- 📈 Daily / monthly / yearly energy production (perfect for HA Energy Dashboard)
- 🛠️ Reliable even after restarts or reloads

### Installation

#### Via HACS (recommended)

1. Go to **HACS → Integrations** → click the three dots (top right) → **Custom repositories**
2. Add this URL:  
   `https://github.com/jimmybonesde/Envertech_local`
3. Category: **Integration**
4. Click **Add** → search for **Envertech Local (Fork)** → Install
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → + Add Integration** → search for “Envertech”

#### Manual Installation

1. Download or clone this repository
2. Copy the folder `custom_components/envertech_local` into your Home Assistant `config` directory
3. Restart Home Assistant
4. Add the integration via the UI (as above)

### Configuration

1. Go to **Settings → Devices & Services → + Add Integration**
2. Search for “Envertech Local”
3. Enter the **IP address** and **TCP port** of your inverter (default port is usually 8899)
4. Submit → entities appear automatically

### Created Entities (Examples)

- `sensor.envertech_[sn]_p1_input_voltage` → Panel 1 input voltage
- `sensor.envertech_[sn]_total_energy` → Lifetime total energy
- `sensor.envertech_[sn]_energy_daily` → **Production today** (since midnight)
- `sensor.envertech_[sn]_energy_monthly` → **Production this month**
- `sensor.envertech_[sn]_energy_yearly` → **Production this year**

### Screenshots

*(Coming soon: Energy dashboard example, panel overview, configuration flow)*

### License & Credits

Original work Copyright (c) [Year] Kaiserdragon2  
Fork & enhancements Copyright (c) 2026 JimmyBonesDE (@jimmybonesde)

Licensed under the **MIT License** – see [LICENSE](LICENSE) for details.

### Contributing

Bug reports, feature requests, and pull requests are very welcome!  
Please open an [issue](https://github.com/jimmybonesde/Envertech_local/issues) first.

Made with ❤️ in Karlsruhe, Germany
