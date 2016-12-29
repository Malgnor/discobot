from disco.bot import Bot, Plugin
from configparser import RawConfigParser
import sys
import requests
import ujson
import os

global riotApiKey, getSummonerNameUrl, ownerid
getSummonerNameUrl = 'https://br.api.pvp.net/api/lol/br/v1.4/summoner/by-name/'

def getConfig():
    global riotApiKey, ownerid
    config = RawConfigParser()
    try:
        config.read('config.cfg')
        ownerid = config.get('plugin', 'ownerid')
        riotApiKey = config.get('riotapi', 'apikey')
    except(RawConfigParser.NoSectionError, RawConfigParser.NoOptionError):
        quit('The "config.cfg" file is missing or corrupt!')
        
def createConfigFile():
    with open('config.cfg', 'w') as cfg:
        cfg.write('[plugin]\nownerid = 000000000000000\n\n[riotapi]\napikey = **************')

class MyPlugin(Plugin):    
    def __init__(self, bot, config):
        super(MyPlugin, self).__init__(bot, config)
        reload(sys)
        sys.setdefaultencoding('utf8')
        
        if not os.path.isfile('config.cfg'):
            createConfigFile()
        
        getConfig()
        
    @Plugin.command('reload')
    def on_reload_command(self, event):
        event.msg.reply('Reloading...')
        quit("Command triggered quit.")
        
    @Plugin.command('reloadconfig')
    def on_reload_command(self, event):
        msg = event.msg.reply('Reloading config...')
        getConfig()
        msg.edit('Config reloaded!')
        
    @Plugin.command('name','<name:str...>')
    def on_name_command(self, event, name):
        msg = event.msg.reply('Procurando...')
        result = requests.get(getSummonerNameUrl + name + '?api_key=' + riotApiKey)
        j = ujson.loads(result.text)
        msg.edit('```\n'+ujson.dumps(j, indent=4)+'\n```')

    @Plugin.listen('MessageCreate')
    def on_message_create(self, msg):
        self.log.info('Message created: {}: {}'.format(msg.author, msg.content))

    @Plugin.command('spam', '<count:int> <content:str...>')
    def on_spam_command(self, event, count, content):
        for i in range(count):
            event.msg.reply(content)

    @Plugin.command('info', '<query:str...>')
    def on_info(self, event, query):
        users = list(self.state.users.select({'username': query}, {'id': query}))

        if not users:
            event.msg.reply("Couldn't find user for your query: `{}`".format(query))
        elif len(users) > 1:
            event.msg.reply('I found too many userse ({}) for your query: `{}`'.format(len(users), query))
        else:
            user = users[0]
            parts = []
            parts.append('ID: {}'.format(user.id))
            parts.append('Username: {}'.format(user.username))
            parts.append('Discriminator: {}'.format(user.discriminator))

            if event.channel.guild:
                member = event.channel.guild.get_member(user)
                parts.append('Nickname: {}'.format(member.nick))
                parts.append('Joined At: {}'.format(member.joined_at))

            event.msg.reply('```\n{}\n```'.format(
                '\n'.join(parts)
            ))
