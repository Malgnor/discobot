from disco.bot import Bot, Plugin
from configparser import RawConfigParser
import sys
import requests
import ujson
import os
import random

global riotApiKey, getSummonerNameUrl, ownerid, pastasNum
getSummonerNameUrl = 'https://br.api.pvp.net/api/lol/br/v1.4/summoner/by-name/'

def getConfig():
    global riotApiKey, ownerid
    config = RawConfigParser()
    try:
        config.read('config.cfg')
        ownerid = int(config.get('plugin', 'ownerid'))
        riotApiKey = config.get('riotapi', 'apikey')
    except(RawConfigParser.NoSectionError, RawConfigParser.NoOptionError):
        quit('The "config.cfg" file is missing or corrupt!')
        
def createConfigFile():
    with open('config.cfg', 'w') as cfg:
        cfg.write('[plugin]\nownerid = 000000000000000\n\n[riotapi]\napikey = **************')

def addPasta(pasta):
    global pastasNum
    if not os.path.exists('memes'):
        os.makedirs('memes')
    with open('memes'+os.path.sep+str(pastasNum)+'.txt', 'w') as meme:
        meme.write(pasta)
    pastasNum += 1
    
def loadPasta(num):
    if not os.path.isfile('memes'+os.path.sep+str(num)+'.txt'):
        return 'Copypasta não encontrado'
    with open('memes'+os.path.sep+str(num)+'.txt', 'r') as meme:
        pasta = meme.read()
    return pasta
    
def countPastas():
    if os.path.exists('memes'):
        count = 0
        for files in os.listdir('memes'):
            count += 1
        return count
    else:
        return 0
    
class MyPlugin(Plugin):    
    def __init__(self, bot, config):
        global pastasNum
        super(MyPlugin, self).__init__(bot, config)
        reload(sys)
        sys.setdefaultencoding('utf8')
        
        if not os.path.isfile('config.cfg'):
            createConfigFile()
        
        getConfig()
        pastasNum = countPastas()
        
    @Plugin.command('reload')
    def on_reload_command(self, event):
        if event.msg.author.id == ownerid:
            event.msg.reply('Reloading...')
            quit("Command triggered quit.")
        else:
            event.msg.reply('Você não pode usar esse comando.')
        
    @Plugin.command('reloadconfig')
    def on_reloadconfig_command(self, event):
        if event.msg.author.id == ownerid:
            msg = event.msg.reply('Reloading config...')
            getConfig()
            msg.edit('Config reloaded!')
        else:
            event.msg.reply('Você não pode usar esse comando.')
        
    @Plugin.command('addpasta','<pasta:str...>')
    def on_addpasta_command(self, event, pasta):
        msg = event.msg.reply('Adicionando copypasta...')
        addPasta(pasta)
        msg.edit('Copypasta adicionado!')
        
    @Plugin.command('pasta','[pasta:int]')
    def on_pasta_command(self, event, pasta=None):
        if not pasta:
            pasta = random.randrange(pastasNum)
        msg = event.msg.reply('Procurando copypasta...')
        msg.edit(loadPasta(pasta))
        
    @Plugin.command('pastaspam','<pasta:int>')
    def on_pastaspam_command(self, event, pasta):
        for i in range(pasta):
            event.msg.reply(loadPasta(random.randrange(pastasNum)))
        
    @Plugin.command('pastaC')
    def on_pastaCount_command(self, event, ):
        event.msg.reply('Copypastas salvos: ' + str(pastasNum))
        
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
        if event.msg.author.id == ownerid:
            for i in range(count):
                event.msg.reply(content)
        else:
            event.msg.reply('Você não pode usar esse comando.')

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
