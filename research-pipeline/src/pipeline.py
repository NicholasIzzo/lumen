import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from agents import run_agent
from notifier import send_report


def run_pipeline(topic: str) -> dict:
    print(f'\n{"="*50}')
    print(f'LUMEN Research Pipeline')
    print(f'Topic: {topic}')
    print(f'{"="*50}')

    plan = run_agent('planner', f'Crea un piano di ricerca per: {topic}')
    research = run_agent('researcher', f'Topic: {topic}\n\nPiano:\n{plan}\n\nProduci contenuto dettagliato.')
    analysis = run_agent('analyst', f'Topic: {topic}\n\nContenuto:\n{research}')
    report = run_agent('writer', f'Topic: {topic}\n\nRicerca:\n{research}\n\nAnalisi:\n{analysis}\n\nScrivi il report finale.')
    critic = run_agent('critic', f'Valuta questo report:\n{report}')

    send_report(topic, report, critic)
    return {"topic": topic, "plan": plan, "research": research, "analysis": analysis, "report": report, "critic": critic}


if __name__ == '__main__':
    import sys
    topic = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else input('Topic di ricerca: ')
    run_pipeline(topic)
