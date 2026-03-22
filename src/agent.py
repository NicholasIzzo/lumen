import json
import os
import sys
import time
import schedule
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))
from settings import ANTHROPIC_API_KEY, CHECK_INTERVAL_MINUTES

import anthropic

sys.path.insert(0, os.path.dirname(__file__))
from tools import TOOLS_DEFINITION, execute_tool
from notifier import send_discord_alert, send_daily_report, send_critical_alert

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Sei LUMEN, un agente AI che monitora e gestisce autonomamente un homelab domestico.

Il homelab e' composto da:
- Un NAS con Docker: Sonarr, Radarr, Prowlarr, qBittorrent+Mullvad VPN, Pi-hole, Home Assistant, Grafana, Prometheus, Nextcloud, Vaultwarden, Nginx Proxy Manager
- Un server separato con Jellyfin (NON gestito da te)

REGOLE FONDAMENTALI:
- NON toccare MAI: jellyfin-app-1, qbittorrent-vpn, gluetun, mariadb, nextcloud
- qbittorrent-vpn dipende da gluetun per la VPN Mullvad
- mariadb e nextcloud sono spenti di proposito
- Puoi aggiornare automaticamente tutti gli altri container con update_containers

Il tuo compito e':
1. Monitorare lo stato dei container Docker
2. Controllare disco, CPU e RAM
3. Rilevare anomalie e problemi
4. Intervenire autonomamente quando possibile
5. Aggiornare i container in whitelist quando richiesto
6. Produrre report chiari e concisi in italiano

Sii diretto e tecnico. Usa emoji per rendere i report leggibili su Discord."""


def run_agent(task: str) -> str:
    print(f"\n[LUMEN] {datetime.now().strftime('%H:%M:%S')} — Task: {task}")
    messages = [{"role": "user", "content": task}]

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS_DEFINITION,
            messages=messages
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text = block.text
            print(f"[LUMEN] Completato.")
            return final_text

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"[LUMEN] Tool: {block.name}({block.input})")
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            messages.append({"role": "user", "content": tool_results})


def check_homelab():
    print(f"\n[LUMEN] Check periodico — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    report = run_agent(
        "Esegui un check completo del homelab. "
        "Controlla: 1) stato di tutti i container Docker, "
        "2) spazio disco, 3) CPU e RAM. "
        "IMPORTANTE: mariadb e nextcloud sono SPENTI DI PROPOSITO, ignorali. "
        "Se trovi altri container crashati (che non siano nella blacklist) riavviali. "
        "Se tutto e' ok scrivi SOLO 'tutto ok' con un brevissimo sommario senza usare "
        "parole come problema, errore, anomalia, critico, warning. "
        "Se ci sono problemi reali descrivili e dimmi cosa hai fatto."
    )
    if any(keyword in report.lower() for keyword in ["problema", "errore", "crash", "critico", "riavviato", "warning", "anomalia"]):
        send_critical_alert("Anomalia rilevata durante check periodico", report)
    else:
        print(f"[LUMEN] Tutto ok, nessun alert inviato.")


def daily_report():
    print(f"\n[LUMEN] Generazione report giornaliero...")
    report = run_agent(
        "Genera un report giornaliero completo del homelab. "
        "Includi: stato di tutti i container, spazio disco, "
        "risorse sistema, eventuali anomalie. "
        "Formatta il report in modo leggibile per Discord con emoji."
    )
    send_daily_report(report)


def weekly_update():
    print(f"\n[LUMEN] Aggiornamento settimanale container...")
    report = run_agent(
        "Esegui l'aggiornamento dei container in whitelist con update_containers. "
        "Poi verifica che tutti i container aggiornati siano tornati online. "
        "Riporta quali sono stati aggiornati e quali erano gia' all'ultima versione."
    )
    send_discord_alert("Aggiornamento Settimanale Completato", report, "info")


if __name__ == "__main__":
    print("LUMEN — Homelab AI Agent")
    print("=" * 40)

    send_discord_alert("LUMEN Online", "Agente avviato. Inizio monitoraggio homelab.", "success")
    check_homelab()

    schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(check_homelab)
    schedule.every().day.at("08:00").do(daily_report)
    schedule.every().sunday.at("03:00").do(weekly_update)

    print(f"\n[LUMEN] Scheduler attivo — check ogni {CHECK_INTERVAL_MINUTES} minuti")
    print(f"[LUMEN] Report giornaliero alle 08:00")
    print(f"[LUMEN] Aggiornamenti automatici ogni domenica alle 03:00")

    while True:
        schedule.run_pending()
        time.sleep(30)
