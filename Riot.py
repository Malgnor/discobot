from PluginBase import *

class Riot(Plugin, PluginBase):
    @staticmethod
    def config_cls():
        config = {}
        config['apikey'] = ''
        config['default_region'] = 'br'
        return config
        
    @Plugin.command('name', '<name:str...>', level=10, description='Retorna algumas informações básicas sobre um ou mais invocadores.')
    def on_name_command(self, event, name):
        self.client.api.channels_typing(event.msg.channel_id)
        result = requests.get('https://{}.api.pvp.net/api/lol/{}/v1.4/summoner/by-name/{}'.format(self.config['default_region'], self.config['default_region'], name), params={'api_key':self.config['apikey']})
        event.msg.reply('```\n'+json.dumps(json.loads(result.text), indent=4, ensure_ascii=False)+'\n```')