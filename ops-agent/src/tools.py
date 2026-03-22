import subprocess
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))
from settings import NAS_HOST

BLACKLIST_RESTART = [
    "jellyfin-app-1",
    "qbittorrent-vpn",
    "gluetun",
    "mariadb",
    "nextcloud"
]

WHITELIST_UPDATES = [
    "homeassistant",
    "prowlarr",
    "radarr",
    "sonarr",
    "pihole",
    "grafana",
    "prometheus",
    "node-exporter",
    "cadvisor",
    "vaultwarden_server-1",
    "jc21_nginx-proxy-manager-1",
    "tailscale",
    "flaresolverr_flaresolverr-1"
]


def get_docker_containers() -> dict:
    try:
        result = subprocess.run(
            ["sudo", "docker", "ps", "-a", "--format", "{{.Names}}|{{.Status}}|{{.Image}}"],
            capture_output=True, text=True, timeout=10
        )
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) == 3:
                    name, status, image = parts
                    containers.append({
                        "name": name,
                        "status": status,
                        "image": image,
                        "running": status.startswith("Up"),
                        "protected": name in BLACKLIST_RESTART
                    })
        return {"success": True, "containers": containers}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_disk_usage() -> dict:
    try:
        result = subprocess.run(
            ["df", "-h", "/volume1"],
            capture_output=True, text=True, timeout=10
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            parts = lines[1].split()
            return {
                "success": True,
                "filesystem": parts[0],
                "size": parts[1],
                "used": parts[2],
                "available": parts[3],
                "percent": parts[4]
            }
        return {"success": False, "error": "Impossibile leggere il disco"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_system_stats() -> dict:
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
        mem_total = int([l for l in meminfo.split('\n') if 'MemTotal' in l][0].split()[1])
        mem_available = int([l for l in meminfo.split('\n') if 'MemAvailable' in l][0].split()[1])
        mem_used_percent = round((1 - mem_available / mem_total) * 100, 1)

        result = subprocess.run(["top", "-bn1"], capture_output=True, text=True, timeout=10)
        cpu_line = [l for l in result.stdout.split('\n') if 'Cpu' in l or 'cpu' in l]
        cpu_idle = 0
        if cpu_line:
            parts = cpu_line[0].split(',')
            idle_part = [p for p in parts if 'id' in p]
            if idle_part:
                cpu_idle = float(idle_part[0].strip().split()[0])
        cpu_used = round(100 - cpu_idle, 1)

        return {
            "success": True,
            "ram_used_percent": mem_used_percent,
            "ram_total_mb": round(mem_total / 1024),
            "ram_available_mb": round(mem_available / 1024),
            "cpu_used_percent": cpu_used
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def restart_container(container_name: str) -> dict:
    if container_name in BLACKLIST_RESTART:
        return {"success": False, "error": f"Container {container_name} e' protetto — LUMEN non puo' toccarlo."}
    try:
        result = subprocess.run(
            ["sudo", "docker", "restart", container_name],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return {"success": True, "message": f"Container {container_name} riavviato con successo"}
        return {"success": False, "error": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_container_logs(container_name: str, lines: int = 50) -> dict:
    try:
        result = subprocess.run(
            ["sudo", "docker", "logs", "--tail", str(lines), container_name],
            capture_output=True, text=True, timeout=10
        )
        return {"success": True, "logs": result.stdout + result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_containers() -> dict:
    results = []
    for container in WHITELIST_UPDATES:
        try:
            inspect = subprocess.run(
                ["sudo", "docker", "inspect", "--format", "{{.Config.Image}}", container],
                capture_output=True, text=True, timeout=10
            )
            image = inspect.stdout.strip()
            if not image:
                results.append({"container": container, "status": "non trovato"})
                continue
            pull = subprocess.run(
                ["sudo", "docker", "pull", image],
                capture_output=True, text=True, timeout=120
            )
            if "Status: Image is up to date" in pull.stdout:
                results.append({"container": container, "status": "gia' aggiornato"})
            elif "Status: Downloaded newer image" in pull.stdout:
                subprocess.run(["sudo", "docker", "restart", container], capture_output=True, text=True, timeout=30)
                results.append({"container": container, "status": "aggiornato e riavviato"})
            else:
                results.append({"container": container, "status": "errore", "detail": pull.stderr[:200]})
        except Exception as e:
            results.append({"container": container, "status": "errore", "detail": str(e)})
    return {"success": True, "results": results}


TOOLS_DEFINITION = [
    {
        "name": "get_docker_containers",
        "description": "Ottieni lo stato di tutti i container Docker. I container protetti non possono essere riavviati.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_disk_usage",
        "description": "Controlla lo spazio disco disponibile su /volume1.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_system_stats",
        "description": "Ottieni CPU e RAM attuali del NAS.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "restart_container",
        "description": "Riavvia un container Docker crashato. Non funziona su container protetti.",
        "input_schema": {
            "type": "object",
            "properties": {
                "container_name": {"type": "string", "description": "Il nome esatto del container da riavviare"}
            },
            "required": ["container_name"]
        }
    },
    {
        "name": "get_container_logs",
        "description": "Leggi gli ultimi log di un container.",
        "input_schema": {
            "type": "object",
            "properties": {
                "container_name": {"type": "string", "description": "Il nome del container"},
                "lines": {"type": "integer", "description": "Numero di righe di log (default 50)"}
            },
            "required": ["container_name"]
        }
    },
    {
        "name": "update_containers",
        "description": "Aggiorna le immagini Docker dei container in whitelist. Non tocca mai qbittorrent-vpn, gluetun e jellyfin.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    }
]


def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "get_docker_containers":
        result = get_docker_containers()
    elif tool_name == "get_disk_usage":
        result = get_disk_usage()
    elif tool_name == "get_system_stats":
        result = get_system_stats()
    elif tool_name == "restart_container":
        result = restart_container(tool_input.get("container_name", ""))
    elif tool_name == "get_container_logs":
        result = get_container_logs(tool_input.get("container_name", ""), tool_input.get("lines", 50))
    elif tool_name == "update_containers":
        result = update_containers()
    else:
        result = {"success": False, "error": f"Tool {tool_name} non trovato"}
    return json.dumps(result, ensure_ascii=False)
