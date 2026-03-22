import os
import sys
import json
import requests
import schedule
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))
from settings import ANTHROPIC_API_KEY, PIHOLE_HOST, PIHOLE_PASSWORD, NETWORK_SUBNET, CHECK_INTERVAL_MINUTES

sys.path.insert(0, os.path.dirname(__file__))
from notifier import send_alert

import anthropic

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

KNOWN_DEVICES = {
    '192.168.0.x':  'Router',
    '192.168.x.33': 'Server (esempio)',
    '192.168.x.36': 'NAS (esempio)',
    '192.168.x.14': 'iPhone owner',
    '192.168.x.25': 'Smart TV',
    '192.168.x.37': 'Smart TV 2',
    '192.168.x.17': 'PC Owner',
    '192.168.0.x':  'Amazon Fire TV Stick',
    '192.168.0.x': 'Apple Watch',
    '192.168.0.x': 'Apple Watch 2',
    '192.168.0.x': 'Apple Watch 3',
    '192.168.x.13': 'Printer',
    '192.168.0.x':  'Tuya/Smart device',
    '192.168.0.x':  'Tuya/Smart device',
    '192.168.0.x':  'Tuya/Smart device',
    '192.168.0.x':  'Tuya/Smart device',
    '192.168.0.x':  'Tuya/Smart device',
    '192.168.0.x':  'Tuya/Smart device',
    '192.168.0.x': 'Tuya/Smart device',
    '192.168.0.x': 'Tuya/Smart device',
    '192.168.0.x': 'Tuya/Smart device',
    '192.168.0.x': 'Device 20:be',
    '192.168.0.x': 'Device 90:02',
    '192.168.0.x': 'Device f8:17',
    '192.168.0.x': 'Device 48:5f',
    '192.168.0.x': 'Device 68:db',
    '192.168.0.x': 'Device fc:67',
    '192.168.0.x': 'Device b0:45',
}

SYSTEM_PROMPT = '''Sei LUMEN Network Monitor, un agente AI che analizza la rete domestica.
Il tuo compito e': analizzare device connessi, statistiche Pi-hole e connettivita internet.
I device Tuya/Smart sono dispositivi domotica normali.
Segnala SOLO device con nome Sconosciuto non in lista.
Sii diretto e tecnico. Usa emoji per Discord. Rispondi in italiano.'''

TOOLS_DEFINITION = [
    {'name': 'get_network_devices', 'description': 'Ottieni la lista dei device connessi alla rete.', 'input_schema': {'type': 'object', 'properties': {}, 'required': []}},
    {'name': 'get_pihole_stats', 'description': 'Ottieni statistiche Pi-hole.', 'input_schema': {'type': 'object', 'properties': {}, 'required': []}},
    {'name': 'check_internet', 'description': 'Verifica connettivita internet.', 'input_schema': {'type': 'object', 'properties': {}, 'required': []}}
]


def get_network_devices() -> dict:
    try:
        devices = []
        with open('/proc/net/arp', 'r') as f:
            lines = f.readlines()[1:]
        for line in lines:
            parts = line.split()
            if len(parts) >= 4:
                ip = parts[0]
                mac = parts[3]
                if ip.startswith('192.168.0.'):
                    name = KNOWN_DEVICES.get(ip, 'Sconosciuto')
                    devices.append({'ip': ip, 'mac': mac, 'name': name, 'known': ip in KNOWN_DEVICES})
        return {'success': True, 'devices': devices, 'total': len(devices)}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_pihole_stats() -> dict:
    try:
        url = f'http://{PIHOLE_HOST}:9090/api/stats/summary'
        response = requests.get(url, timeout=5)
        data = response.json()
        queries = data.get('queries', {})
        gravity = data.get('gravity', {})
        clients = data.get('clients', {})
        return {'success': True, 'total_queries': queries.get('total', 0), 'blocked_queries': queries.get('blocked', 0), 'block_percent': round(queries.get('percent_blocked', 0), 1), 'domains_blocked': gravity.get('domains_being_blocked', 0), 'active_clients': clients.get('active', 0), 'status': 'online'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def check_internet() -> dict:
    try:
        targets = [('https://www.google.com', 'Google'), ('https://www.cloudflare.com', 'Cloudflare')]
        results = []
        for url, name in targets:
            try:
                r = requests.get(url, timeout=5)
                results.append({'target': name, 'reachable': True, 'status': r.status_code})
            except:
                results.append({'target': name, 'reachable': False})
        return {'success': True, 'internet_ok': all(r['reachable'] for r in results), 'results': results}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == 'get_network_devices':
        result = get_network_devices()
    elif tool_name == 'get_pihole_stats':
        result = get_pihole_stats()
    elif tool_name == 'check_internet':
        result = check_internet()
    else:
        result = {'success': False, 'error': f'Tool {tool_name} non trovato'}
    return json.dumps(result, ensure_ascii=False)


def run_agent(task: str) -> str:
    print(f'\n[NETWORK] {datetime.now().strftime("%H:%M:%S")} — {task[:50]}')
    messages = [{'role': 'user', 'content': task}]
    while True:
        response = client.messages.create(model='claude-haiku-4-5-20251001', max_tokens=2048, system=SYSTEM_PROMPT, tools=TOOLS_DEFINITION, messages=messages)
        messages.append({'role': 'assistant', 'content': response.content})
        if response.stop_reason == 'end_turn':
            for block in response.content:
                if hasattr(block, 'text'):
                    return block.text
            return ''
        if response.stop_reason == 'tool_use':
            tool_results = []
            for block in response.content:
                if block.type == 'tool_use':
                    print(f'[NETWORK] Tool: {block.name}')
                    result = execute_tool(block.name, block.input)
                    tool_results.append({'type': 'tool_result', 'tool_use_id': block.id, 'content': result})
            messages.append({'role': 'user', 'content': tool_results})


def check_network():
    print(f'\n[NETWORK] Check — {datetime.now().strftime("%d/%m/%Y %H:%M")}')
    report = run_agent('Esegui un check completo della rete domestica. Controlla: 1) device connessi, segnala SOLO quelli con nome Sconosciuto, 2) statistiche Pi-hole, 3) connettivita internet. Se tutto ok scrivi SOLO tutto ok con brevissimo sommario senza usare parole come anomalia, problema, errore.')
    if any(k in report.lower() for k in ['sconosciuto', 'anomalia', 'problema', 'critico', 'offline', 'errore']):
        send_alert('Anomalia di Rete Rilevata', report, 'critical')
    else:
        send_alert('Rete OK', report, 'success')


def daily_report():
    print(f'\n[NETWORK] Report giornaliero...')
    report = run_agent('Genera un report giornaliero della rete domestica. Includi: device connessi, statistiche Pi-hole, stato internet. Formatta per Discord con emoji.')
    send_alert('Report Giornaliero Rete', report, 'info')


if __name__ == '__main__':
    print('LUMEN — Network Monitor')
    print('=' * 40)
    send_alert('LUMEN Network Online', 'Monitoraggio rete avviato.', 'success')
    check_network()
    schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(check_network)
    schedule.every().day.at('08:30').do(daily_report)
    print(f'\n[NETWORK] Scheduler attivo — check ogni {CHECK_INTERVAL_MINUTES} minuti')
    while True:
        schedule.run_pending()
        time.sleep(30)


