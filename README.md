<div align="center">

```
  ____             ____  _             
 |  _ \ _ __ ___  |  _ \(_)_ __   __ _ 
 | |_) | '__/ _ \ | |_) | | '_ \ / _` |
 |  __/| | | (_) ||  __/| | | | | (_| |
 |_|   |_|  \___/ |_|   |_|_| |_|\__, |
                                 |___/ 
```

# ProPing

### Global Cloud & Datacenter Latency Intelligence Suite
**High-Performance ICMP Benchmarking · Automated Cloud Provider Auditing · Zero-Dependency Studio Dashboards**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Zero Dependency UI](https://img.shields.io/badge/UI-Zero--Dependency%20HTML%2FCSS-00e599.svg)](#interactive-dashboard)
[![Verified Clouds](https://img.shields.io/badge/Verified%20Providers-609%20Live-38bdf8.svg)](#telemetry-database)
[![Countries](https://img.shields.io/badge/Global%20Reach-57%20Countries-fbbf24.svg)](#country-directory)
[![Direct Fiber](https://img.shields.io/badge/Direct%20Fiber-Sub--50ms-10b981.svg)](#latency-tiers)

[🌐 **Live Interactive Demo**](http://109.248.43.154/) · [⏱️ **Hourly Compute Directory**](http://109.248.43.154/master_hourly_directory.html) · [📊 **Raw Telemetry JSON**](http://109.248.43.154/master_cloud_directory.json)

</div>

---

## 📖 Table of Contents
- [Overview](#-overview)
- [Key Features](#-key-features)
- [Live Demo & Screenshots](#-live-demo--screenshots)
- [Quick Start](#-quick-start)
- [CLI Command Reference](#-cli-command-reference)
- [Telemetry Database & Schema](#-telemetry-database--schema)
- [Dashboard Architecture (NewUI)](#-dashboard-architecture-newui)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## ⚡ Overview

**ProPing** is an open-source, automated network latency intelligence and cloud provider discovery platform. Engineered specifically to solve the challenge of discovering true low-latency cloud routes, direct-fiber peering, hourly pay-as-you-go instances, and cryptocurrency-friendly hosting providers.

Unlike basic ping utilities or static lists, ProPing integrates:
1. **Multi-Threaded ICMP Telemetry Engine:** Measures packet round-trip time (`min`, `avg`, `max`), jitter, and packet loss from live network probe vantage points (e.g. Respina Telecom, Tehran).
2. **Automated Cloud Provider Auditor:** Scans provider domains, detects parked, expired, or cPanel-suspended domains, filters non-hosting sites, and verifies actual VPS/VDS server package offerings and pricing.
3. **Studio Telemetry Dashboard (NewUI):** Compiles benchmark telemetry into a single-file, zero-dependency, ultra-modern HTML/CSS/JS interface featuring responsive Bento Cards Grid and spacious 8-Column Data Table views, 11 categories, 4 KPI spotlights, and a 4-way side-by-side comparison dock.

---

## 🌟 Key Features

* **⚡ Ultra-Fast Concurrent Probing:** Benchmark hundreds of datacenter Looking Glasses, test IPs, and ASNs simultaneously with configurable thread pools and packet counts.
* **🛡️ Zero False Positives / Parking Filter:** Automatically identifies domain parking (Sedo, Dan, Namecheap), cPanel/Plesk defaults, and maintenance screens while whitelisting Tier-1 WAF-protected cloud giants (Linode, DigitalOcean, Hetzner, OVH, Natro, etc.).
* **💎 Dual View Modes (Table & Bento Grid):** Toggle instantly between a high-density 8-column telemetry table and responsive Bento Cards Grid with zero JavaScript DOM overhead (powered by pure CSS Grid).
* **🎯 11 Curated Categories & Presets:**
  * `Sub-50ms Direct (Iran)` — Ultra-low latency direct-fiber routes (<50ms).
  * `50–80ms Prime Europe` — High-speed Frankfurt & Amsterdam transit nodes.
  * `80–120ms West Europe` — Standard Western Europe cloud regions.
  * `Hourly Pay-As-You-Go` — 62 verified hourly billing providers.
  * `Crypto Accepted` — 264 hosts supporting Bitcoin, USDT, and Monero.
  * `Budget Friendly` — 341 servers starting under $4.00/mo.
  * `DDoS Protected` — Hardware-mitigated high-capacity anti-DDoS hosts.
  * `Privacy & Offshore` — Privacy-focused and offshore cloud providers.
  * `10Gbps+ Uplink` — High-bandwidth unmetered ports.
  * `Dedicated / Bare Metal` — Physical dedicated compute servers.
* **📊 Interactive Latency Spectrum Bar:** Real-time distribution visualization across 5 latency bands with live reactive counts.
* **🌍 57-Country Directory:** Searchable country directory with ISO codes, FlagCDN flags, and provider counts.
* **📌 Side-by-Side Comparison Dock:** Pin up to 4 cloud providers to compare hardware specs, test IPs, ping, jitter, and billing models in a side-by-side modal.
* **🌓 Intelligent Auto-Theme System:** Dynamic Dark/Light mode scheduled by solar daytime/nighttime with manual toggle and `localStorage` persistence.
* **📋 1-Click IPv4 Copier:** Quick-copy test IPv4 with animated checkmark feedback and direct Looking Glass launching.

---

## 🖥️ Live Demo & Screenshots

Explore the live production deployment hosted on our telemetry probe:

| Dashboard View | Live URL | Description |
| :--- | :--- | :--- |
| **Global Master Catalog** | [http://109.248.43.154/](http://109.248.43.154/) | Complete catalog of **609** verified live cloud providers. |
| **Hourly Compute Directory** | [http://109.248.43.154/master_hourly_directory.html](http://109.248.43.154/master_hourly_directory.html) | Filtered directory of **62** active hourly compute hosts. |
| **Raw Cloud Dataset** | [http://109.248.43.154/master_cloud_directory.json](http://109.248.43.154/master_cloud_directory.json) | Clean structured JSON database. |

---

## 🚀 Quick Start

### 1. Installation

Clone the repository and install the minimal dependencies:

```bash
git clone https://github.com/Lagtor-code/ProPing.git
cd ProPing
pip install -r requirements.txt
```

### 2. Check Database Status

View instant telemetry summary statistics:

```bash
python proping.py status
```

Output:
```text
============================================================
📊 ProPing Telemetry Database Overview
============================================================
  Total Verified Providers:  609
  Unique Countries:          57
  Average Iran Latency:      122.6 ms
  Best Minimum Latency:      36.97 ms
  Hourly Providers:          62
  Crypto Accepted:           264
  Budget Friendly (<$4/mo):  341
============================================================
```

### 3. Build Standalone Dashboards

Compile the verified dataset into zero-dependency HTML dashboards:

```bash
python proping.py build
```

This compiles:
* `dist/index.html` (Master Catalog with all 609 providers)
* `dist/hourly.html` (Hourly compute catalog with 62 providers)

### 4. Preview in Browser

Launch the built-in local web server and automatically open the dashboard:

```bash
python proping.py serve --port 8080
```

---

## 💻 CLI Command Reference

ProPing provides a unified CLI with subcommands:

```bash
python proping.py [command] [options]
```

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`build`** | `-i, --input`<br>`-o, --output`<br>`--hourly-output` | Compiles raw JSON datasets into the NewUI HTML dashboards. |
| **`status`** | `-i, --input` | Prints high-level metrics, provider counts, and latency stats. |
| **`serve`** | `-p, --port`<br>`-d, --dir`<br>`--no-browser` | Spawns a local HTTP server and opens the dashboard in your default browser. |
| **`benchmark`** | `-t, --target`<br>`-i, --input`<br>`-c, --count`<br>`-w, --workers` | Runs multi-threaded ICMP ping tests and calculates min/avg/max/jitter. |

### Single-Target Ping Example:
```bash
python proping.py benchmark --target 1.1.1.1 --count 4
```

### Batch Benchmark Example:
```bash
python proping.py benchmark --input data/master_cloud_directory.json --workers 25 --count 4
```

---

## 🗄️ Telemetry Database & Schema

All providers in `data/master_cloud_directory.json` are structured with clean, standardized schemas:

```json
{
  "brand": "Trserverim",
  "website": "https://trserverim.com",
  "domain": "trserverim.com",
  "test_ip": "194.169.120.3",
  "looking_glass_url": "http://lg.trserverim.com",
  "country": "Turkey",
  "country_code": "TR",
  "city": "Istanbul",
  "region": "Middle East",
  "datacenter_location": "Istanbul, Turkey",
  "verified_asn": "AS42724",
  "starting_price": "$2.90/mo",
  "hourly_billing": false,
  "billing_model": "Monthly",
  "crypto": false,
  "server_type": "Cloud VPS & Dedicated Servers",
  "port_speed": "1Gbps - 10Gbps",
  "tags": [
    "Ultra-Low Latency (<50ms)",
    "NVMe SSD",
    "Anti-DDoS"
  ],
  "status": "ONLINE",
  "avg_ms": 36.97,
  "min_ms": 36.9,
  "max_ms": 37.0,
  "jitter_ms": 0.1,
  "loss_pct": 0.0,
  "protocol": "ICMP",
  "is_iran_benchmark": true,
  "tested_at": "2026-10-06 13:22:05 UTC"
}
```

---

## 🏛️ Project Architecture

```text
ProPing/
├── proping/                    # Core Python Package
│   ├── __init__.py             # Package exports & version
│   ├── cli.py                  # CLI argument parser & subcommands
│   ├── pinger.py               # Concurrent ICMP latency & jitter prober
│   ├── auditor.py              # Website validity & server package scanner
│   ├── builder.py              # NewUI HTML/CSS/JS dashboard compiler
│   └── utils.py                # ISO country mapping & price normalizer
│
├── proping.py                  # Root CLI entrypoint (`python proping.py ...`)
│
├── data/                       # Ground Truth Telemetry Datasets
│   ├── master_cloud_directory.json   # 609 verified live cloud providers
│   └── master_hourly_directory.json  # 62 active hourly compute providers
│
├── dist/                       # Production Compiled Web Artifacts
│   ├── index.html              # Standalone Master Catalog (609 nodes)
│   └── hourly.html             # Standalone Hourly Catalog (62 nodes)
│
├── requirements.txt            # Minimal dependencies (requests, urllib3)
├── pyproject.toml              # Modern Python build specification
├── LICENSE                     # MIT Open-Source License
└── README.md                   # Complete Documentation
```

---

## 🌐 Deployment to VPS / Nginx

To deploy ProPing dashboards directly to a remote Linux VPS running Nginx:

1. Configure connection settings in `deploy_to_vps.py` (or environment variables `VPS_HOST`, `VPS_USER`, `VPS_PASS`).
2. Run:
   ```bash
   python deploy_to_vps.py
   ```
3. Nginx serves `dist/index.html` with Gzip compression enabled, delivering the full 609-provider dashboard in ~130 KB over the wire!

---

## 🤝 Contributing

Contributions are warmly welcomed! You can help by:
1. Adding new datacenter Looking Glass nodes and test IPs.
2. Reporting inactive, acquired, or rebranded hosting providers.
3. Adding new network probe vantage points across different ISPs and IXPs.

To contribute:
1. Fork the repo (`https://github.com/Lagtor-code/ProPing`).
2. Create your feature branch (`git checkout -b feature/new-providers`).
3. Commit your changes (`git commit -m 'Add new verified EU providers'`).
4. Push to the branch (`git push origin feature/new-providers`).
5. Open a Pull Request.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

Developed with ❤️ by the **ProPing** Community.
