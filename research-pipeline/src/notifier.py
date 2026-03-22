import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))
from settings import DISCORD_WEBHOOK_URL

from discord_webhook import DiscordWebhook, DiscordEmbed


def send_report(topic: str, report: str, critic: str):
    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL, username='LUMEN Research')
    embed = DiscordEmbed(
        title=f'Research Report: {topic}',
        description=report[:3900],
        color=0x9b59b6
    )
    embed.add_embed_field(name='Critic Review', value=critic[:500], inline=False)
    embed.set_footer(text=f'LUMEN Research Pipeline - {datetime.now().strftime("%d/%m/%Y %H:%M")}')
    webhook.add_embed(embed)
    webhook.execute()
    print('[PIPELINE] Report inviato su Discord!')
