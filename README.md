# Envertech API for Home Assistant

Local TCP monitoring for Envertech microinverters — by **JimmyBones** (`@jimmybonesde`). No cloud account required after setup.

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/jimmybonesde/Envertech_local?style=flat)](https://github.com/jimmybonesde/Envertech_local/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Maintained fork by [JimmyBones](https://github.com/jimmybonesde), based on [Kaiserdragon2/Envertech_local](https://github.com/Kaiserdragon2/Envertech_local).

## Features

- Fully local polling over TCP (no cloud dependency)
- Per-panel and plant-level sensors (voltage, power, energy, temperature, frequency, …)
- Daily / monthly / yearly production sensors (derived from lifetime total, restored across restarts)
- Stable entity IDs for multi-panel setups
- Translations: English, German, Polish
- Works with Home Assistant Energy dashboard

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jimmybonesde&repository=Envertech_local&category=integration)

1. HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/jimmybonesde/Envertech_local` as category **Integration**
3. Search for **Envertech API** → Install
4. Restart Home Assistant
5. Settings → Devices & Services → Add Integration → **Envertech API**

### Manual

1. Copy `custom_components/envertech_local` into your HA `config/custom_components/` folder
2. Restart Home Assistant
3. Add the integration via the UI

## Configuration

1. Settings → Devices & Services → Add Integration → **Envertech API**
2. Pick a discovered inverter, or choose **Manual entry**
3. Confirm IP and TCP port (default `14889`)

Sensors appear automatically once the first data packet arrives (setup itself does not block).

## Example sensors

| Sensor | Meaning |
| --- | --- |
| `…_p1_power` | Panel 1 instantaneous power (W) |
| `…_total_energy` | Lifetime energy (kWh) |
| `…_energy_daily` | Production since local midnight (kWh) |
| `…_energy_monthly` | Production this month (kWh) |
| `…_energy_yearly` | Production this year (kWh) |

## Supported devices

Most Envertech microinverters with local TCP (e.g. EMT series). Tested with multi-panel setups.

If your model works (or doesn’t), please [open an issue](https://github.com/jimmybonesde/Envertech_local/issues).

## Credits & license

- Original work: [Kaiserdragon2](https://github.com/Kaiserdragon2/Envertech_local)
- Fork maintenance & enhancements: **JimmyBones** ([@jimmybonesde](https://github.com/jimmybonesde))
- Polish translation: [@vaGpl](https://github.com/vaGpl)

MIT License — see [LICENSE](LICENSE).

## Contributing

Bug reports and pull requests are welcome:

- Issues: https://github.com/jimmybonesde/Envertech_local/issues
- PRs: https://github.com/jimmybonesde/Envertech_local/pulls
