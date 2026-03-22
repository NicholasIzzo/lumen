# LUMEN Ops Agent

Agente AI che monitora e gestisce autonomamente l'infrastruttura Docker del homelab.

## Cosa fa
- Controlla lo stato di tutti i container Docker ogni 4 ore
- Riavvia automaticamente i container crashati
- Monitora spazio disco, CPU e RAM
- Manda alert su Discord solo quando c'è un problema reale
- Genera un report giornaliero alle 8:00
- Aggiorna automaticamente le immagini Docker ogni domenica alle 3:00

## Come funziona
Usa Claude API con tool use — l'agente chiama strumenti reali (Docker, filesystem, sistema) e decide autonomamente cosa fare in base ai risultati.

## Setup
1. Copia config/.env.example in config/.env e inserisci le tue credenziali
2. Installa le dipendenze: pip install -r requirements.txt
3. Avvia: python3 src/agent.py
