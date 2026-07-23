# =============================================================
#  config.py — Network Monitor Configuration
#  Author: Rodrigo Alexis Guerra Wendell
#  Edit this file to customize your hosts and alert settings.
# =============================================================

# ── Hosts to monitor ─────────────────────────────────────────
# Format: { "label": "ip_or_hostname" }
HOSTS = {
    "Gateway":       "192.168.1.1",
    "Google DNS":    "8.8.8.8",
    "Cloudflare":    "1.1.1.1",
    "HTTP Server":   "172.16.60.10",    # Your lab VLAN 61
    "NTP Server":    "172.16.60.74",    # Your lab VLAN 62
    "Syslog Server": "172.16.60.138",   # Your lab VLAN 63
    "FTP Server":    "172.16.60.202",   # Your lab VLAN 64
}

# ── Monitoring settings ───────────────────────────────────────
PING_INTERVAL_SECONDS = 30      # How often to ping each host
PING_TIMEOUT_SECONDS  = 2       # Max wait per ping
PING_COUNT            = 1       # Packets per ping cycle
DOWN_THRESHOLD        = 2       # Consecutive failures before alert

# ── Log settings ──────────────────────────────────────────────
LOG_DIR  = "logs"
LOG_FILE = "logs/network_log.csv"

# ── Email alerts ──────────────────────────────────────────────
EMAIL_ENABLED  = False          # Set True to activate email alerts
EMAIL_SENDER   = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"   # Use Gmail App Password, not your real password
EMAIL_RECEIVER = "your_email@gmail.com"
SMTP_HOST      = "smtp.gmail.com"
SMTP_PORT      = 587

# ── Console display ───────────────────────────────────────────
REFRESH_HEADER_EVERY = 20       # Re-print header every N cycles
