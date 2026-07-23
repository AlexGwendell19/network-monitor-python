#!/usr/bin/env python3
# =============================================================
#  monitor.py — Network Monitor — Main Engine
#  Author: Rodrigo Alexis Guerra Wendell
#
#  Features:
#    - Cross-platform ping (Windows & Linux)
#    - Threaded: all hosts pinged simultaneously
#    - CSV logging with timestamp and latency
#    - Email alerts on DOWN / recovery UP
#    - Color-coded console output
#    - Uptime % report on exit (Ctrl+C)
# =============================================================

import subprocess
import platform
import threading
import csv
import os
import sys
import time
import re
import signal
from datetime import datetime
from collections import defaultdict

import config
import alerts
import report


# ── ANSI Color codes (work on Linux/macOS and Windows 10+) ───
class Color:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"
    GRAY   = "\033[90m"


def enable_windows_ansi():
    """Enable ANSI escape codes on Windows terminals."""
    if platform.system() == "Windows":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


# ── Global state ──────────────────────────────────────────────
stats_lock = threading.Lock()
stats      = defaultdict(lambda: {"up": 0, "down": 0, "latency": []})

# Track consecutive failures per host to avoid alert spam
consecutive_down = defaultdict(int)
host_alerted     = defaultdict(bool)   # True = currently in DOWN alert state

# CSV log file handle (opened once, shared across threads)
log_file_handle = None
csv_writer      = None
log_lock        = threading.Lock()


# ── Ping function (cross-platform) ───────────────────────────
def ping(ip: str) -> tuple[bool, float]:
    """
    Ping a host once and return (is_reachable, latency_ms).
    Uses subprocess to call the OS ping command.
    Works on both Windows and Linux/macOS.
    """
    system = platform.system()

    if system == "Windows":
        cmd = ["ping", "-n", str(config.PING_COUNT),
               "-w", str(config.PING_TIMEOUT_SECONDS * 1000), ip]
    else:
        cmd = ["ping", "-c", str(config.PING_COUNT),
               "-W", str(config.PING_TIMEOUT_SECONDS), ip]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=config.PING_TIMEOUT_SECONDS + 2
        )
        output = result.stdout.decode("utf-8", errors="replace")

        if result.returncode != 0:
            return False, 0.0

        # Extract latency from ping output
        latency = _parse_latency(output, system)
        return True, latency

    except subprocess.TimeoutExpired:
        return False, 0.0
    except FileNotFoundError:
        print(f"{Color.RED}[ERROR] 'ping' command not found on this system.{Color.RESET}")
        return False, 0.0


def _parse_latency(output: str, system: str) -> float:
    """Extract average latency in ms from ping output string."""
    try:
        if system == "Windows":
            # "Average = 12ms"
            match = re.search(r"Average\s*=\s*(\d+)ms", output)
        else:
            # "rtt min/avg/max/mdev = 0.123/0.456/0.789/0.111 ms"
            match = re.search(r"rtt .+= [\d.]+/([\d.]+)/", output)
        return float(match.group(1)) if match else 0.0
    except Exception:
        return 0.0


# ── CSV Logging ───────────────────────────────────────────────
def init_log():
    """Open (or create) the CSV log file and write the header if new."""
    global log_file_handle, csv_writer
    os.makedirs(config.LOG_DIR, exist_ok=True)

    file_exists = os.path.isfile(config.LOG_FILE)
    log_file_handle = open(config.LOG_FILE, "a", newline="", encoding="utf-8")
    csv_writer = csv.writer(log_file_handle)

    if not file_exists:
        csv_writer.writerow(["timestamp", "host", "ip", "status", "latency_ms"])
        log_file_handle.flush()


def log_result(label: str, ip: str, is_up: bool, latency: float):
    """Append one ping result to the CSV log (thread-safe)."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status    = "UP" if is_up else "DOWN"
    with log_lock:
        csv_writer.writerow([timestamp, label, ip, status, round(latency, 2)])
        log_file_handle.flush()


# ── Console output ────────────────────────────────────────────
def print_header():
    width = 72
    now   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{Color.BOLD}{Color.CYAN}{'=' * width}{Color.RESET}")
    print(f"{Color.BOLD}{Color.CYAN}  NETWORK MONITOR{Color.RESET}"
          f"  |  {Color.GRAY}{now}{Color.RESET}"
          f"  |  Hosts: {len(config.HOSTS)}"
          f"  |  Interval: {config.PING_INTERVAL_SECONDS}s")
    print(f"{Color.BOLD}{Color.CYAN}{'=' * width}{Color.RESET}")
    print(f"  {Color.BOLD}{'HOST':<22} {'IP':<18} {'STATUS':<10} {'LATENCY':>9} {'TIME'}{Color.RESET}")
    print(f"  {Color.GRAY}{'-' * (width - 2)}{Color.RESET}")


def print_result(label: str, ip: str, is_up: bool, latency: float):
    """Print one color-coded result line to the console."""
    timestamp = datetime.now().strftime("%H:%M:%S")

    if is_up:
        status_str = f"{Color.GREEN}● UP   {Color.RESET}"
        lat_str    = f"{Color.GREEN}{latency:>7.1f} ms{Color.RESET}"
    else:
        status_str = f"{Color.RED}✖ DOWN {Color.RESET}"
        lat_str    = f"{Color.RED}{'timeout':>9}{Color.RESET}"

    print(f"  {label:<22} {ip:<18} {status_str}  {lat_str}  {Color.GRAY}{timestamp}{Color.RESET}")


# ── Per-host monitor thread ───────────────────────────────────
def monitor_host(label: str, ip: str):
    """
    Continuously ping one host every PING_INTERVAL_SECONDS.
    Logs result, updates stats, prints to console, triggers alerts.
    Runs in its own daemon thread.
    """
    global consecutive_down, host_alerted

    while True:
        is_up, latency = ping(ip)

        # Update global stats (thread-safe)
        with stats_lock:
            if is_up:
                stats[label]["up"] += 1
                stats[label]["latency"].append(latency)
            else:
                stats[label]["down"] += 1

        # Log to CSV
        log_result(label, ip, is_up, latency)

        # Print to console
        print_result(label, ip, is_up, latency)

        # ── Alert logic ──────────────────────────────────────
        if not is_up:
            consecutive_down[label] += 1
            if (consecutive_down[label] >= config.DOWN_THRESHOLD
                    and not host_alerted[label]):
                host_alerted[label] = True
                print(f"\n  {Color.RED}{Color.BOLD}"
                      f"[ALERT] {label} ({ip}) is DOWN — sending email alert...{Color.RESET}")
                sent = alerts.send_alert(label, ip, "DOWN")
                if sent:
                    print(f"  {Color.YELLOW}[ALERT] Email sent.{Color.RESET}\n")
        else:
            if host_alerted[label]:
                # Host recovered
                host_alerted[label] = False
                print(f"\n  {Color.GREEN}{Color.BOLD}"
                      f"[RECOVERY] {label} ({ip}) is back UP — sending email alert...{Color.RESET}")
                sent = alerts.send_alert(label, ip, "UP")
                if sent:
                    print(f"  {Color.YELLOW}[ALERT] Recovery email sent.{Color.RESET}\n")
            consecutive_down[label] = 0

        time.sleep(config.PING_INTERVAL_SECONDS)


# ── Graceful shutdown ─────────────────────────────────────────
def shutdown(signum=None, frame=None):
    """Print final report and close log file on Ctrl+C."""
    print(f"\n\n{Color.YELLOW}[MONITOR] Stopping... generating final report.{Color.RESET}")

    with stats_lock:
        current_stats = dict(stats)

    report.generate_report(current_stats)

    report_path = report.export_report_csv(current_stats)
    print(f"{Color.CYAN}[MONITOR] Report saved to: {report_path}{Color.RESET}\n")

    if log_file_handle:
        log_file_handle.close()

    sys.exit(0)


# ── Entry point ───────────────────────────────────────────────
def main():
    enable_windows_ansi()

    signal.signal(signal.SIGINT, shutdown)   # Ctrl+C
    if platform.system() != "Windows":
        signal.signal(signal.SIGTERM, shutdown)  # kill command on Linux

    init_log()
    print_header()

    print(f"\n{Color.CYAN}[MONITOR] Starting {len(config.HOSTS)} host threads "
          f"(interval: {config.PING_INTERVAL_SECONDS}s)...{Color.RESET}")
    print(f"{Color.GRAY}  Log file : {config.LOG_FILE}{Color.RESET}")
    print(f"{Color.GRAY}  Alerts   : {'ENABLED (email)' if config.EMAIL_ENABLED else 'DISABLED (set EMAIL_ENABLED=True in config.py)'}{Color.RESET}")
    print(f"{Color.GRAY}  Press Ctrl+C to stop and generate uptime report.{Color.RESET}\n")

    threads = []
    for label, ip in config.HOSTS.items():
        t = threading.Thread(
            target=monitor_host,
            args=(label, ip),
            daemon=True,
            name=f"monitor-{label}"
        )
        t.start()
        threads.append(t)
        time.sleep(0.3)   # Stagger starts to avoid console collision

    # Print header periodically while threads run
    cycle = 0
    while True:
        time.sleep(config.PING_INTERVAL_SECONDS * config.REFRESH_HEADER_EVERY)
        cycle += 1
        print_header()


if __name__ == "__main__":
    main()
