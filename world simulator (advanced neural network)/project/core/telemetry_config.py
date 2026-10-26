"""
project/core/telemetry_config.py

Master Configuration for Remote Telemetry, Active User Analytics, and GitHub Upgrades.
The project owner can configure their free Discord webhook or REST endpoint here,
allowing consented users to automatically transmit active-user pings and world state dumps.
"""

from __future__ import annotations

import os

# -----------------------------------------------------------------------------
# GitHub Repository & Upgrade Configuration
# -----------------------------------------------------------------------------
GITHUB_OWNER = "sretrowave3-dev"
GITHUB_REPO_NAME = "world-simulator-vibe-coded-v1"
GITHUB_REPO = f"{GITHUB_OWNER}/{GITHUB_REPO_NAME}"
GITHUB_BRANCH = "main"

# Remote API Endpoints
GITHUB_API_COMMITS_URL = f"https://api.github.com/repos/{GITHUB_REPO}/commits/{GITHUB_BRANCH}"
GITHUB_API_RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"
GITHUB_ZIPBALL_URL = f"https://api.github.com/repos/{GITHUB_REPO}/zipball/{GITHUB_BRANCH}"

# -----------------------------------------------------------------------------
# Owner Telemetry & Live Analytics Configuration
# -----------------------------------------------------------------------------
# The project owner can paste their free Discord webhook URL or any REST API endpoint below.
# When users consent in the setup wizard, active user heartbeats and world state data
# are automatically routed to this endpoint for free.
DEFAULT_OWNER_WEBHOOK = os.environ.get(
    "SIMULATOR_TELEMETRY_WEBHOOK",
    "https://discord.com/api/webhooks/1563857516943773776/V2znOb2BXgZ2iLiimU0H7glotYTYom2unvpMfrGJKVHQ3245IE1TYVxfZygBQt2LiBiw"
)

# Active User Tracking Frequency
HEARTBEAT_INTERVAL_SECONDS: float = 600.0  # 10 minutes

# World State Dispatch Frequency
WORLD_STATE_INTERVAL_TICKS: int = 1800     # ~30 seconds of active simulation

# Default World State Granularity:
# - "SUMMARY": High-level metrics (population, extinction count, age, climate, civ score)
# - "DEEP": Detailed ecosystem (biome health, genetics, top species, notable thoughts/speech)
# - "FULL": Complete serialized world dump ("literally everything" - entities, genomes, brains, terrain)
DEFAULT_WORLD_STATE_LEVEL: str = "FULL"

# Maximum payload size in bytes before gzip compression is applied (Discord webhook limit ~8MB)
MAX_UNCOMPRESSED_PAYLOAD_BYTES: int = 64 * 1024
