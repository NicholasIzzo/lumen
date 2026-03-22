# LUMEN Network Monitor

Agente AI che monitora la rete domestica e rileva anomalie in autonomia.

## Cosa fa
- Scansiona tutti i device connessi alla rete ogni 4 ore
- Identifica device sconosciuti e manda alert immediati
- Controlla le statistiche Pi-hole (query bloccate, domini in blocklist)
- Verifica la connettivita' internet
- Genera un report giornaliero alle 8:30
- Tutto viene notificato su Discord

## Come funziona
Legge la tabella ARP del kernel Linux per rilevare i device, interroga le API di Pi-hole v6 per le statistiche DNS, e usa Claude API per analizzare i dati e decidere se mandare alert.

## Setup
1. Copia config/.env.example in config/.env e inserisci le tue credenziali
2. Aggiorna KNOWN_DEVICES in src/monitor.py con i device della tua rete
3. Installa le dipendenze: pip install -r requirements.txt
4. Avvia: python3 src/monitor.py
