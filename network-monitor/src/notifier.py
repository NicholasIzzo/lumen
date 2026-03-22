import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))
from settings import DISCORD_WEBHOOK_URL

from discord_webhook import DiscordWebhook, DiscordEmbed


def send_alert(title: str, message: str, level: str = 'info'):
    colors = {'info': 0x3498db, 'warning': 0xf39c12, 'critical': 0xe74c3c, 'success': 0x2ecc71}
    emoji = {'info': '💡', 'warning': '⚠️', 'critical': '🚨', 'success': '✅'}
    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL, username='LUMEN Network')
    embed = DiscordEmbed(
        title=f"{emoji.get(level, '💡')} {title}",
        description=message,
        color=colors.get(level, 0x3498db)
    )
    embed.set_footer(text=f"LUMEN Network Monitor - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    webhook.add_embed(embed)
    webhook.execute()
    print(f'[NETWORK] Alert inviato: {title}')
