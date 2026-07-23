# 🖧 Network Monitor

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)
![Stdlib](https://img.shields.io/badge/Dependencies-stdlib%20only-blue?style=for-the-badge)

**Cross-platform network monitoring tool** — ping multiple hosts simultaneously, log results to CSV, send email alerts on failures, and generate uptime reports.

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Output](#-output)
- [Email Alerts](#-email-alerts)
- [Project Structure](#-project-structure)
- [Sample Output](#-sample-output)
- [Future Improvements](#-future-improvements)
- [Author](#-author)

---

## 📌 Overview

This tool monitors the availability and response time of a configurable list of network hosts. It was built to complement a [multi-service enterprise branch network](https://github.com/rodrigo-guerra/enterprise-network-lab) deployed on Cisco hardware, but works for any IP/hostname you want to track.

Every host runs in its own thread, so all pings happen in parallel — no waiting for slow hosts to time out before checking the next one.

---

## ✨ Features

| Feature | Details |
|---------|---------|
| **Parallel ping** | All hosts monitored simultaneously via threads |
| **Cross-platform** | Works on Windows, Linux, and macOS |
| **CSV logging** | Every result saved with timestamp and latency |
| **Email alerts** | Notifies on DOWN and recovery (UP) events |
| **Alert dedup** | Only alerts once per outage, not every failed ping |
| **Uptime report** | Shows UP %, checks count, avg latency per host |
| **Color console** | Green/red color-coded live output |
| **Zero dependencies** | Uses Python standard library only |

---

## 🏗 Architecture

```
monitor.py          ← Entry point, threads, console output
    │
    ├── config.py   ← All settings (hosts, email, intervals)
    ├── alerts.py   ← Email alert logic (smtplib)
    └── report.py   ← Uptime % calculation and CSV export
         │
         └── logs/
             ├── network_log.csv      ← Live ping log (appended each run)
             └── report_YYYYMMDD.csv  ← Snapshot report (on exit)
```

Each host runs in a `daemon` thread that pings, logs, prints, and checks alert conditions in an infinite loop separated by `PING_INTERVAL_SECONDS`. The main thread re-prints the header periodically and listens for `Ctrl+C` via `signal.SIGINT` to trigger a clean shutdown and final report.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- `ping` command available (built into Windows and Linux)

### 1. Clone the repository

```bash
git clone https://github.com/rodrigo-guerra/network-monitor-python.git
cd network-monitor-python
```

### 2. Configure your hosts

Edit `config.py` and replace the default hosts with your own:

```python
HOSTS = {
    "Gateway":    "192.168.1.1",
    "Google DNS": "8.8.8.8",
    "My Server":  "192.168.1.100",
}
```

### 3. Run the monitor

```bash
python monitor.py
```

Press `Ctrl+C` at any time to stop and generate a final uptime report.

---

## ⚙️ Configuration

All settings live in `config.py`. No need to touch any other file.

```python
# Hosts to monitor
HOSTS = {
    "Label": "ip_or_hostname",
}

# Timing
PING_INTERVAL_SECONDS = 30    # How often to ping
PING_TIMEOUT_SECONDS  = 2     # Max wait per ping
DOWN_THRESHOLD        = 2     # Consecutive failures before alert

# Email
EMAIL_ENABLED  = False        # Set True to enable
EMAIL_SENDER   = "you@gmail.com"
EMAIL_PASSWORD = "your_app_password"
EMAIL_RECEIVER = "you@gmail.com"
```

---

## 📊 Output

### Live console (color-coded)

```
========================================================================
  NETWORK MONITOR  |  2026-06-27 14:32:01  |  Hosts: 7  |  Interval: 30s
========================================================================
  HOST                   IP                 STATUS     LATENCY  TIME
  ----------------------------------------------------------------------
  Gateway                192.168.1.1        ● UP         1.2 ms  14:32:01
  Google DNS             8.8.8.8            ● UP         9.8 ms  14:32:01
  HTTP Server            172.16.60.10       ● UP         2.1 ms  14:32:02
  NTP Server             172.16.60.74       ✖ DOWN      timeout  14:32:03

  [ALERT] NTP Server (172.16.60.74) is DOWN — sending email alert...
  [ALERT] Email sent.
```

### CSV log (`logs/network_log.csv`)

```csv
timestamp,host,ip,status,latency_ms
2026-06-27 14:32:01,Gateway,192.168.1.1,UP,1.2
2026-06-27 14:32:01,Google DNS,8.8.8.8,UP,9.8
2026-06-27 14:32:03,NTP Server,172.16.60.74,DOWN,0.0
```

### Uptime report (on Ctrl+C)

```
========================================================================
  NETWORK MONITOR — UPTIME REPORT
  Generated: 2026-06-27 15:00:00
========================================================================
  HOST                   IP                   UP    DOWN   UPTIME   AVG ms
  ------------------------------------------------------------------------
  🟢 Gateway             192.168.1.1          60       0   100.0%      1.2
  🟢 Google DNS          8.8.8.8              60       0   100.0%      9.8
  🟡 NTP Server          172.16.60.74         48      12    80.0%      2.3
  🔴 FTP Server          172.16.60.202        10      50    16.7%      0.0
========================================================================
```

---

## 📧 Email Alerts

The monitor sends two types of alerts:

- **DOWN alert** — triggered after `DOWN_THRESHOLD` consecutive failed pings (default: 2)
- **UP / Recovery alert** — triggered when a previously DOWN host starts responding again

Alert deduplication is built in: you get **one email when the host goes down**, not one per failed ping.

### Gmail setup

1. Enable 2-Step Verification on your Google account
2. Go to **Google Account → Security → App Passwords**
3. Create an app password for "Mail"
4. Set `EMAIL_PASSWORD` to that 16-character password in `config.py`
5. Set `EMAIL_ENABLED = True`

> ⚠️ Never commit your real password to GitHub. Use `.gitignore` to exclude `config.py` if it contains credentials, or use environment variables.

---

## 📁 Project Structure

```
network-monitor-python/
│
├── monitor.py              ← Main engine: threads, ping, console, signal handling
├── config.py               ← All user settings (hosts, email, timing)
├── alerts.py               ← Email alert module (smtplib + MIME)
├── report.py               ← Uptime report generator + CSV export
├── requirements.txt        ← No external deps (stdlib only)
├── README.md               ← This file
│
└── logs/                   ← Auto-created on first run
    ├── network_log.csv     ← Continuous ping log
    └── report_*.csv        ← Uptime snapshots (generated on exit)
```

---

## 🔮 Future Improvements

- [ ] Web dashboard with Flask or Streamlit showing live charts from the CSV log
- [ ] Telegram / WhatsApp alerts via bot API
- [ ] ICMP latency trend graph with matplotlib
- [ ] Configurable alert cooldown period
- [ ] Docker container for always-on deployment on a Linux server
- [ ] Export to InfluxDB + Grafana dashboard

---

## 👤 Author

**Rodrigo Alexis Guerra Wendell**

[![GitHub](https://img.shields.io/badge/GitHub-rodrigo--guerra-181717?style=flat-square&logo=github)](https://github.com/rodrigo-guerra)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat-square&logo=linkedin)](https://linkedin.com/in/rodrigo-guerra)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

*Built with Python standard library only — no pip install required.*

</div>
