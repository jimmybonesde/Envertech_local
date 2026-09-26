<p align="center">
  <img src="brand/icon.png" alt="Envertech API icon" width="128">
</p>

<h1 align="center">Envertech API for Home Assistant</h1>

<p align="center">
  <strong>Local, cloud-free monitoring of Envertech micro-inverters via their TCP interface.</strong>
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg?logo=homeassistantcommunitystore&logoColor=white" alt="HACS Custom"></a>
  <a href="https://github.com/jimmybonesde/Envertech_local/releases/latest"><img src="https://img.shields.io/github/v/release/jimmybonesde/Envertech_local?sort=semver" alt="Latest release"></a>
  <a href="https://github.com/jimmybonesde/Envertech_local/actions/workflows/hassfest.yaml"><img src="https://github.com/jimmybonesde/Envertech_local/actions/workflows/hassfest.yaml/badge.svg" alt="hassfest"></a>
  <a href="https://github.com/jimmybonesde/Envertech_local/actions/workflows/hacs-validation.yaml"><img src="https://github.com/jimmybonesde/Envertech_local/actions/workflows/hacs-validation.yaml/badge.svg" alt="HACS validation"></a>
  <a href="https://github.com/jimmybonesde/Envertech_local/actions/workflows/pytest.yaml"><img src="https://github.com/jimmybonesde/Envertech_local/actions/workflows/pytest.yaml/badge.svg" alt="Python tests"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/jimmybonesde/Envertech_local" alt="License: MIT"></a>
</p>

<p align="center">
  <a href="#-features">Features</a> ·
  <a href="#-installation">Installation</a> ·
  <a href="#%EF%B8%8F-configuration">Configuration</a> ·
  <a href="#-sensors">Sensors</a> ·
  <a href="#-energy-dashboard">Energy Dashboard</a> ·
  <a href="#%EF%B8%8F-troubleshooting">Troubleshooting</a>
</p>

> **Envertech API** (integration domain `envertech_local`) reads live data straight from your Envertech inverter/gateway on your local network. You don't need a cloud account, and nothing leaves your LAN.

This fork is maintained by [JimmyBones](https://github.com/jimmybonesde). It is based on [Kaiserdragon2/Envertech_local](https://github.com/Kaiserdragon2/Envertech_local).

---

## ✨ Features

- 🏠 **100 % local**: a persistent TCP connection to the inverter (default port `14889`), polled every 5 seconds
- 🔍 **Automatic discovery** of inverters on your network (UDP broadcast), with a manual setup option as fallback
- ⚡ **Per-panel live values**: DC input voltage, power, energy, temperature, grid voltage and grid frequency
- 🏡 **System totals**: total power and lifetime energy
- 📅 **Daily / monthly / yearly energy** sensors that survive restarts
- 📈 **Energy Dashboard ready**: all energy sensors use `device_class: energy` and `state_class: total_increasing`
- 🌍 Translations: **English, German and Polish**
- 🧩 Installable via **HACS**, with no YAML to write

## 📦 Installation

### HACS (recommended)

> ℹ️ The integration is not in the HACS default list yet. The inclusion request is pending in [hacs/default#10850](https://github.com/hacs/default/pull/10850). Until it is merged, add it as a **custom repository**:

[![Open your Home Assistant instance and open this repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jimmybonesde&repository=Envertech_local&category=integration)

1. In Home Assistant, open **HACS → ⋮ (top right) → Custom repositories**.
2. Add `https://github.com/jimmybonesde/Envertech_local` with type **Integration**.
3. Search for **Envertech API** in HACS and click **Download**.
4. **Restart** Home Assistant.

### Manual

1. Download the [latest release](https://github.com/jimmybonesde/Envertech_local/releases/latest).
2. Copy `custom_components/envertech_local` into `<config>/custom_components/` of your Home Assistant installation.
3. **Restart** Home Assistant.

Requires Home Assistant **2024.6.0** or newer.

## ⚙️ Configuration

The integration is set up entirely in the UI through a config flow:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=envertech_local)

1. Go to **Settings → Devices & services → Add integration** and choose **Envertech API**.
2. **Discovery:** the integration spends about 5 seconds searching your network for inverters. It sends UDP broadcasts on ports `48889` (Ethernet/LOCALCON) and `48899` (Wi-Fi). Every inverter it finds is listed as `IP — serial number`, except those already set up.
3. Pick your inverter and check the **TCP port** (default `14889`).
4. If nothing is found, choose **Manual entry** and enter:
   - **IP address** of the inverter/gateway
   - **Serial number**: the 8-character hex ID of the inverter, e.g. `9A1B2C3D`
   - **TCP port**: default `14889`
5. Add one config entry for each inverter/gateway. The serial number is the unique ID, so an inverter can't be added twice.

After setup, the inverter-wide sensors show up right away. Per-panel sensors are added automatically once the first data packet reports the panels. Until data arrives, sensors are `unavailable`.

> 💡 Home Assistant must be able to reach the inverter on TCP port `14889`. Discovery also needs UDP broadcasts to work, which usually means the same subnet or VLAN and `host` networking for Docker installs. Give the inverter a fixed IP address (DHCP reservation) in your router.

## 📊 Sensors

The integration creates **one device per config entry** (`Envertech API <serial>`, manufacturer *JimmyBones*, model *Microinverter*). The firmware version is shown as the device's software version.

### ⚡ Per panel / module

These are created for every panel `n` (1, 2, …) that the inverter reports. The entity names are `P<n> …`, e.g. `sensor.p1_power`. If you have more than one inverter, Home Assistant adds a numeric suffix to entity IDs that would otherwise be the same.

| | Sensor (entity name) | Key | Unit | Device class | State class | Notes |
| :-: | --- | --- | :-: | --- | --- | --- |
| 🔌 | `P<n> Input Voltage` | `input_voltage` | V | `voltage` | `measurement` | DC input voltage of the panel |
| ⚡ | `P<n> Power` | `power` | W | `power` | `measurement` | Current power of the panel/module |
| 🔋 | `P<n> Energy` | `energy` | kWh | `energy` | `total_increasing` | Lifetime energy of the module |
| 🌡️ | `P<n> Temperature` | `temperature` | °C | `temperature` | `measurement` | Temperature reported by the micro-inverter module |
| 🏭 | `P<n> Grid Voltage` | `grid_voltage` | V | `voltage` | `measurement` | AC grid voltage measured by the module |
| 〰️ | `P<n> Frequency` | `frequency` | Hz | `frequency` | `measurement` | AC grid frequency |
| 🆔 | `P<n> Module Serial` | `mi_sn` | – | – | – | *Diagnostic* entity: serial number of the module |

Every per-panel sensor also has a `serial_number` attribute containing the module serial.

### 🏡 Inverter / system

These sensors belong to the device. Their names are translated (English, German, Polish). With Home Assistant set to English, the entity IDs look like `sensor.envertech_api_<serial>_total_power`.

| | Sensor | Key | Unit | Device class | State class | Notes |
| :-: | --- | --- | :-: | --- | --- | --- |
| ⚡ | Total power | `total_power` | W | `power` | `measurement` | Sum of all panel powers |
| 🔋 | Total energy | `total_energy` | kWh | `energy` | `total_increasing` | Sum of all panel lifetime energies |
| 📅 | Daily energy | `energy_daily` | kWh | `energy` | `total_increasing` | Energy since local midnight |
| 🗓️ | Monthly energy | `energy_monthly` | kWh | `energy` | `total_increasing` | Energy in the current month |
| 📆 | Yearly energy | `energy_yearly` | kWh | `energy` | `total_increasing` | Energy in the current year |
| 🧠 | Firmware version | `firmware_version` | – | – | – | *Diagnostic* entity, format `x/y` |

Numbers are rounded to 2 decimal places. The **daily/monthly/yearly** sensors are derived from *Total energy*. When a new period starts, they store the current total as an offset. They keep `offset`, `period_marker` and `last_reset` as attributes and restore them after a restart, so values don't jump back to zero when Home Assistant restarts.

> The integration does **not** provide per-panel current (A), per-panel AC power or MPPT-specific values, because the inverter's local protocol doesn't report them.

## 📈 Energy Dashboard

1. Open **Settings → Dashboards → Energy**.
2. Under **Solar panels**, click **Add solar production**.
3. Select **`sensor.envertech_api_<serial>_total_energy`** (*Total energy*). If you want per-module statistics, add the individual `P<n> Energy` sensors instead.

Use *Total energy* rather than the daily/monthly/yearly sensors. The Energy Dashboard does its own period calculations. The period sensors are meant for cards and automations.

## 🛠️ Troubleshooting

<details>
<summary><strong>No values after a Home Assistant restart (only a reload helped)</strong></summary>

Versions **≤ 1.1.1** could end up without values after a restart:

- If the inverter wasn't reachable within 60 seconds of startup, for example at night or because the network wasn't up yet, the sensors were never created.
- A dropped or silent TCP connection was never re-established.

This is fixed in **1.1.2** ([PR #8](https://github.com/jimmybonesde/Envertech_local/pull/8), available once released):

- The connection now reconnects automatically with backoff (5 s up to 2 min).
- Sensors are created immediately and stay `unavailable` until data arrives.
- New panels are added as soon as they report.

Update to the latest version. If it still happens, please enable debug logging (see below) and open an issue.
</details>

<details>
<summary><strong>Sensors are <code>unavailable</code> at night</strong></summary>

Micro-inverters are powered by the panels, so they switch off when there is no sunlight. The sensors become `unavailable` while the inverter is offline and recover on their own in the morning. The energy totals are unaffected.
</details>

<details>
<summary><strong>No inverter found during setup</strong></summary>

- Discovery relies on UDP broadcast, which doesn't cross VLANs/subnets or Docker bridge networks. Use **Manual entry** instead.
- Check that the inverter is powered (daylight!) and connected to your network.
- Check that port `14889` is reachable: `nc -vz <inverter-ip> 14889`.
</details>

<details>
<summary><strong>Per-panel sensors are missing</strong></summary>

Panel sensors are created when the inverter first reports the panel. If the inverter was offline when you set it up, they appear automatically as soon as it sends data. No reload is needed from 1.1.2 on.
</details>

<details>
<summary><strong>Enable debug logging</strong></summary>

Add this to `configuration.yaml` and restart:

```yaml
logger:
  default: info
  logs:
    custom_components.envertech_local: debug
    envertech_local: debug
```

You can also use **Settings → Devices & services → Envertech API → ⋮ → Enable debug logging**, reproduce the problem and then disable it again to download the log.
</details>

## 🔧 Supported devices

This integration supports Envertech micro-inverters and gateways with a local TCP interface on port `14889`, for example devices of the **EMT series**. It is designed for systems with multiple panels.

Does your model not work, or does it report different data? Please [open an issue](https://github.com/jimmybonesde/Envertech_local/issues) and include the model, the firmware version and, if possible, anonymized debug logs.

## 🤝 Contributing

Bug reports, ideas and pull requests are welcome:

- 🐛 [Report an issue](https://github.com/jimmybonesde/Envertech_local/issues)
- 🔀 [Open a pull request](https://github.com/jimmybonesde/Envertech_local/pulls)
- ✅ Run the unit tests locally with `pip install pytest && pytest -q` (no Home Assistant needed)
- ⭐ Star the repository if you find it useful

## 🙏 Credits & license

- Original integration: [Kaiserdragon2/Envertech_local](https://github.com/Kaiserdragon2/Envertech_local), including the [`envertech-local`](https://pypi.org/project/envertech-local/) protocol library
- Maintenance and development: **JimmyBones** ([@jimmybonesde](https://github.com/jimmybonesde))
- Polish translation: [@vaGpl](https://github.com/vaGpl)

Released under the [MIT License](LICENSE).
