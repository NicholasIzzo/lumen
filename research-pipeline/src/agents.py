import anthropic
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))
from settings import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

AGENTS = {
    'planner': {
        'name': 'Planner',
        'emoji': '🗺️',
        'system': '''Sei il Planner di una pipeline di ricerca AI.
Analizza il topic e produci un piano di ricerca strutturato in italiano.
Output: domande chiave, sotto-topic, angolazioni interessanti. Max 200 parole.'''
    },
    'researcher': {
        'name': 'Researcher',
        'emoji': '🔍',
        'system': '''Sei il Researcher di una pipeline di ricerca AI.
Ricevi un piano e produci contenuto informativo dettagliato in italiano.
Rispondi alle domande chiave con fatti e spiegazioni. Max 400 parole.'''
    },
    'analyst': {
        'name': 'Analyst',
        'emoji': '📊',
        'system': '''Sei l Analyst di una pipeline di ricerca AI.
Analizza criticamente il contenuto del Researcher in italiano.
Identifica punti importanti, connessioni e implicazioni pratiche. Max 300 parole.'''
    },
    'writer': {
        'name': 'Writer',
        'emoji': '✍️',
        'system': '''Sei il Writer di una pipeline di ricerca AI.
Trasforma ricerca e analisi in un report finale professionale in italiano.
Usa titoli, bullet points ed emoji per Discord. Max 500 parole.'''
    },
    'critic': {
        'name': 'Critic',
        'emoji': '🔬',
        'system': '''Sei il Critic di una pipeline di ricerca AI.
Valuta il report finale con voto 1-10, lacune e suggerimenti in italiano. Max 150 parole.'''
    }
}


def run_agent(agent_key: str, prompt: str) -> str:
    agent = AGENTS[agent_key]
    print(f"[PIPELINE] {agent['emoji']} {agent['name']} sta lavorando...")
    response = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=1024,
        system=agent['system'],
        messages=[{'role': 'user', 'content': prompt}]
    )
    output = response.content[0].text
    print(f"[PIPELINE] {agent['name']} completato ({len(output)} chars)")
    return output
