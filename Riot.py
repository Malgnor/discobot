# coding=UTF-8

from disco.bot import Bot, Plugin
from PluginManager import EmbedImageFromUrl
import requests, json

class Riot(Plugin):
    @staticmethod
    def config_cls():
        config = {}
        config['apikey'] = ''
        config['default_region'] = 'br'
        return config
        
    @Plugin.command('name', '<name:str...>', group='LoL', level=10, description='Retorna algumas informações básicas sobre um ou mais invocadores.')
    def on_name_command(self, event, name):
        self.client.api.channels_typing(event.msg.channel_id)
        result = requests.get('https://{}.api.pvp.net/api/lol/{}/v1.4/summoner/by-name/{}'.format(self.config['default_region'], self.config['default_region'], name), params={'api_key':self.config['apikey']})
        j = json.loads(result.text)
        profileiconid = None
        for k in j:
            if 'profileIconId' in j[k]:
                profileiconid = j[k]['profileIconId']
        event.msg.reply('```json\n'+json.dumps(j, indent=4, ensure_ascii=False)+'\n```',
            embed=EmbedImageFromUrl('http://ddragon.leagueoflegends.com/cdn/7.1.1/img/profileicon/{}.png'.format(profileiconid)) if profileiconid else None
        )