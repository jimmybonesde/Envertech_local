# Envertech Local Integration for Home Assistant

**Local-only monitoring** for Envertech microinverters – no cloud, no internet required after setup.

[![HACS Repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jimmybonesde&repository=Envertech_local&category=integration)

[![GitHub Release](https://img.shields.io/github/v/release/jimmybonesde/Envertech_local?style=for-the-badge&logo=github&color=green)](https://github.com/jimmybonesde/Envertech_local/releases)
[![GitHub Stars](https://img.shields.io/github/stars/jimmybonesde/Envertech_local?style=for-the-badge&logo=github&color=yellow)](https://github.com/jimmybonesde/Envertech_local/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

**This is a maintained fork** of the original integration by [Kaiserdragon2](https://github.com/Kaiserdragon2/Envertech_local).

### What this integration does

This custom integration connects **directly** to your Envertech microinverters via local TCP communication. It reads real-time data from the inverter(s) and exposes it as sensors in Home Assistant – **completely without the Envertech cloud**.

You get:

- Per-panel data (if your inverter reports individual modules)
- Global inverter data (total power, total energy, grid values, etc.)
- **Daily, monthly and yearly production** as separate, persistent sensors (the main reason for this fork)

All data stays local – perfect for privacy, reliability and offline use.

### Features

- Fully **local polling** (no cloud calls after setup)
- Real-time monitoring of:
  - Input voltage per panel
  - Power output per panel
  - Energy yield per panel
  - Temperature
  - Grid voltage & frequency
  - Firmware version
  - Module serial numbers
- **Lifetime total energy** (`total_energy`)
- **Daily production** (`energy_daily`) – resets at midnight
- **Monthly production** (`energy_monthly`) – resets on the 1st of each month
- **Yearly production** (`energy_yearly`) – resets on January 1st
- Optimized for the **Home Assistant Energy Dashboard**
- Stable entity creation (no more missing P1 sensors after reloads)
- English & German translations included

### Installation

#### Via HACS (recommended)

1. Go to **HACS → Integrations** → click the three dots (top right) → **Custom repositories**
2. Paste this URL:  
   `https://github.com/jimmybonesde/Envertech_local`
3. Select category: **Integration**
4. Add repository → search for **Envertech Local (Fork)** → Install
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → + Add Integration** → search for “Envertech”

#### Manual Installation

1. Download or clone this repository
2. Copy the folder `custom_components/envertech_local` into your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant
4. Add the integration via the UI (as above)

### Configuration

1. **Settings → Devices & Services → + Add Integration**
2. Search for **Envertech Local**
3. Enter the **IP address** of your Envertech inverter
4. Enter the **TCP port** (default is usually 8899 – check your inverter manual)
5. Submit → the integration will connect and create all sensors automatically

### Created Entities (Examples)

- `sensor.envertech_[serial]_p1_input_voltage` → Input voltage of panel 1 (V)
- `sensor.envertech_[serial]_p1_power` → Current power output of panel 1 (W)
- `sensor.envertech_[serial]_p1_energy` → Energy yield of panel 1 (kWh)
- `sensor.envertech_[serial]_total_energy` → Lifetime total energy of the inverter (kWh)
- `sensor.envertech_[serial]_energy_daily` → **Production today** (kWh since midnight)
- `sensor.envertech_[serial]_energy_monthly` → **Production this month** (kWh)
- `sensor.envertech_[serial]_energy_yearly` → **Production this year** (kWh)

### Supported Devices

- Most Envertech microinverters with local TCP interface (e.g. EMT series)
- Tested with multi-panel setups (1–4+ panels)
- Report compatibility in issues if you have a different model

### License & Credits

Original work Copyright (c) [Original Year] Kaiserdragon2  
Fork, enhancements & maintenance Copyright (c) 2026 JimmyBonesDE (@jimmybonesde)

Licensed under the **MIT License** – see [LICENSE](LICENSE) for full details.

### Contributing

Found a bug? Want a new feature?  
→ Open an [issue](https://github.com/jimmybonesde/Envertech_local/issues) or submit a pull request.

Pull requests are very welcome – especially for bug fixes, new models or additional features.

Made with ❤️ in Karlsruhe, Germany
