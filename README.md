# LUMEN — Homelab AI Ops Agent

> *"Lumen never sleeps."*

An AI-powered agent that autonomously monitors and manages a self-hosted homelab using Claude's tool use API.

## What it does

- Monitors all Docker containers every 4 hours
- Auto-restarts crashed containers (with a configurable blacklist)
- Checks disk usage, CPU and RAM
- Sends alerts to Discord when issues are detected
- Generates a daily report every morning at 8:00
- Auto-updates container images every Sunday at 3:00 AM
- Protects critical containers from accidental restarts (VPN stack, etc.)

## Demo

LUMEN detecting and fixing a crashed container autonomously:

\\\
[LUMEN] Tool: get_docker_containers({})
[LUMEN] Tool: get_container_logs({'container_name': 'sonarr'})
[LUMEN] Tool: restart_container({'container_name': 'sonarr'})
[LUMEN] Completato.
→ Alert sent to Discord
\\\

## Architecture

\\\
Claude API (claude-haiku — brain)
          |
          v
 LUMEN Orchestrator (agent loop)
          |
    ------+------+----------+
    v     v      v          v
Docker  Disk  System   Container
 API   Usage  Stats      Logs
          |
          v
   Discord Alerts
\\\

## Stack

- AI Brain: Claude API (Haiku) with tool use
- Infrastructure: Self-hosted NAS + Docker
- Alerting: Discord webhooks
- Language: Python 3.11
- Scheduler: schedule library

## Setup

1. Clone the repo
\\\ash
git clone https://github.com/NicholasIzzo/lumen.git
cd lumen
\\\

2. Install dependencies
\\\ash
pip install -r requirements.txt
\\\

3. Configure environment
\\\ash
cp config/.env.example config/.env
\\\

4. Run
\\\ash
python3 src/agent.py
\\\

## Environment variables

| Variable | Description |
|----------|-------------|
| ANTHROPIC_API_KEY | Your Claude API key |
| DISCORD_WEBHOOK_URL | Discord webhook for alerts |
| NAS_HOST | Your NAS IP address |
| NAS_USER | SSH username |
| CHECK_INTERVAL_MINUTES | How often to check (default: 240) |

## Cost

Running on claude-haiku with 4-hour intervals costs approximately **\.22/month**.

## Protected containers

These containers are never restarted by LUMEN:
- VPN stack (gluetun, qbittorrent-vpn)
- Manually stopped services (mariadb, nextcloud)
- External services (jellyfin)

## License

MIT

---

*Built with Claude API + Python — Running 24/7 on a self-hosted NAS*
