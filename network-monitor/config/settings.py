import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
PIHOLE_HOST = os.getenv('PIHOLE_HOST', '192.168.x.x')
PIHOLE_PASSWORD = os.getenv('PIHOLE_PASSWORD', '')
NETWORK_SUBNET = os.getenv('NETWORK_SUBNET', '192.168.0.0/24')
CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', '240'))
