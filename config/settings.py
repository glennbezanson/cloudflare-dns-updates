"""Application settings and configuration."""
import os
from pathlib import Path

# Application info
APP_NAME = "Cloudflare DNS Manager"
APP_VERSION = "1.0.0"

# Paths
APP_DIR = Path(__file__).parent.parent
DATA_DIR = APP_DIR / "data"
BACKUPS_DIR = DATA_DIR / "backups"
CONFIG_FILE = DATA_DIR / "config.enc"
AUDIT_LOG = DATA_DIR / "audit.log"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
BACKUPS_DIR.mkdir(exist_ok=True)

# DNS Record Types
DNS_RECORD_TYPES = [
    "A",
    "AAAA",
    "CNAME",
    "MX",
    "TXT",
    "NS",
    "SRV",
    "CAA",
    "PTR",
]

# Default TTL options
TTL_OPTIONS = {
    "Auto": 1,
    "1 minute": 60,
    "5 minutes": 300,
    "10 minutes": 600,
    "30 minutes": 1800,
    "1 hour": 3600,
    "2 hours": 7200,
    "12 hours": 43200,
    "1 day": 86400,
}

# Claude model for reviews
CLAUDE_MODEL = "claude-sonnet-4-20250514"
