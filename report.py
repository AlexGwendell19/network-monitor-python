# =============================================================
#  report.py — Uptime Report Generator
#  Author: Rodrigo Alexis Guerra Wendell
# =============================================================

import csv
import os
from datetime import datetime
from collections import defaultdict
import config


def generate_report(stats: dict) -> None:
    """
    Print a formatted uptime report to the console.

    Args:
        stats: dict from monitor.py with per-host ping statistics.
               Structure: { label: { "up": int, "down": int, "latency": [float] } }
    """
    now   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    width = 72

    print("\n" + "=" * width)
    print(f"  NETWORK MONITOR — UPTIME REPORT")
    print(f"  Generated: {now}")
    print("=" * width)
    print(f"  {'HOST':<22} {'IP':<18} {'UP':>6} {'DOWN':>6} {'UPTIME':>8} {'AVG ms':>8}")
    print("  " + "-" * (width - 2))

    for label, data in stats.items():
        ip       = config.HOSTS.get(label, "unknown")
        total    = data["up"] + data["down"]
        uptime   = (data["up"] / total * 100) if total > 0 else 0.0
        avg_lat  = (sum(data["latency"]) / len(data["latency"])) if data["latency"] else 0.0

        # Color indicator
        if uptime == 100:
            indicator = "🟢"
        elif uptime >= 80:
            indicator = "🟡"
        else:
            indicator = "🔴"

        print(f"  {indicator} {label:<20} {ip:<18} {data['up']:>6} {data['down']:>6} "
              f"{uptime:>7.1f}% {avg_lat:>7.1f}")

    print("=" * width)
    print(f"  Total hosts monitored: {len(stats)}")
    print("=" * width + "\n")


def export_report_csv(stats: dict) -> str:
    """
    Export uptime summary to a separate report CSV file.

    Returns:
        Path to the generated report file.
    """
    os.makedirs(config.LOG_DIR, exist_ok=True)
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(config.LOG_DIR, f"report_{timestamp}.csv")

    with open(report_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Host", "IP", "Checks UP", "Checks DOWN",
                         "Uptime %", "Avg Latency ms", "Report Time"])

        for label, data in stats.items():
            ip      = config.HOSTS.get(label, "unknown")
            total   = data["up"] + data["down"]
            uptime  = round((data["up"] / total * 100), 2) if total > 0 else 0.0
            avg_lat = round(sum(data["latency"]) / len(data["latency"]), 2) \
                      if data["latency"] else 0.0
            writer.writerow([label, ip, data["up"], data["down"],
                             uptime, avg_lat, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

    return report_path


def parse_log_for_stats(log_file: str) -> dict:
    """
    Re-build stats dict by reading an existing CSV log file.
    Useful for generating reports from saved logs without re-running the monitor.

    Args:
        log_file: Path to the CSV log file.

    Returns:
        stats dict compatible with generate_report().
    """
    stats = defaultdict(lambda: {"up": 0, "down": 0, "latency": []})

    if not os.path.exists(log_file):
        print(f"[REPORT] Log file not found: {log_file}")
        return {}

    with open(log_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row.get("host", "unknown")
            if row.get("status") == "UP":
                stats[label]["up"] += 1
                try:
                    stats[label]["latency"].append(float(row.get("latency_ms", 0)))
                except ValueError:
                    pass
            else:
                stats[label]["down"] += 1

    return dict(stats)
