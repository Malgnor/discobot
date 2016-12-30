from disco.bot import Bot, Plugin
from configparser import RawConfigParser
import sys
import requests
import ujson
import os
import random

global riotApiKey, ownerid, pastasNum, commandsText, ownerCommandsText

def getConfig():
    global riotApiKey, ownerid
    config = RawConfigParser()
    try:
        config.read('config.cfg')
        ownerid = config.get('plugin', 'ownerid').split(',')
        riotApiKey = config.get('riotapi', 'apikey')
    except(RawConfigParser.NoSectionError, RawConfigParser.NoOptionError):
        quit('The "config.cfg" file is missing or corrupt!')
        
def createConfigFile():
    with open('config.cfg', 'w') as cfg:
        cfg.write('[plugin]\nownerid = 000000000000000,1111111111\n\n[riotapi]\napikey = **************')

def addPasta(pasta):
    global pastasNum
    if not os.path.exists('memes'):
        os.makedirs('memes')
    with open('memes'+os.path.sep+str(pastasNum)+'.txt', 'w') as meme:
        meme.write(pasta)
    pastasNum += 1
    
def loadPasta(num):
    if not os.path.isfile('memes'+os.path.sep+str(num)+'.txt'):
        return 'Copypasta não encontrado.'
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

def getCommandsText():
    if not os.path.isfile('commands.txt'):
        return 'commands.txt não encontrado;'
    with open('commands.txt', 'r') as file:
        commands = file.read()
    return commands

def getOwnerCommandsText():
    if not os.path.isfile('ownercommands.txt'):
        return 'ownercommands.txt não encontrado;'
    with open('ownercommands.txt', 'r') as file:
        commands = file.read()
    return commands
    
class MyPlugin(Plugin):    
    def __init__(self, bot, config):
        global pastasNum, commandsText, ownerCommandsText
        super(MyPlugin, self).__init__(bot, config)
        reload(sys)
        sys.setdefaultencoding('utf8')
        
        if not os.path.isfile('config.cfg'):
            createConfigFile()
        
        getConfig()
        pastasNum = countPastas()
        commandsText = getCommandsText()
        ownerCommandsText = getOwnerCommandsText()
        
    @Plugin.command('comandos')
    def on_commandshelp_command(self, event):
        event.msg.reply(commandsText)
        if str(event.msg.author.id) in ownerid:
            event.msg.reply(ownerCommandsText)
        event.msg.reply('Código fonte: https://github.com/aamlima/discobot')
        
    @Plugin.command('reload')
    def on_reload_command(self, event):
        if str(event.msg.author.id) in ownerid:
            event.msg.reply('Reloading...')
            quit("Command triggered quit.")
        else:
            event.msg.reply('Você não pode usar esse comando.')
        
    @Plugin.command('reloadconfig')
    def on_reloadconfig_command(self, event):
        if str(event.msg.author.id) in ownerid:
            msg = event.msg.reply('Reloading config...')
            getConfig()
            msg.edit('Config reloaded!')
        else:
            event.msg.reply('Você não pode usar esse comando.')
        
    @Plugin.command('reloadcommandstext')
    def on_reloadcommandstext_command(self, event):
        if str(event.msg.author.id) in ownerid:
            global commandsText, ownerCommandsText
            msg = event.msg.reply('Reloading commands text...')
            commandsText = getCommandsText()
            ownerCommandsText = getOwnerCommandsText()
            msg.edit('Config reloaded!')
        else:
            event.msg.reply('Você não pode usar esse comando.')
        
    @Plugin.command('addpasta','<pasta:str...>')
    def on_addpasta_command(self, event, pasta):
        if pasta == loadPasta(pastasNum-1):
            print("Duplicate pasta")
            return
        msg = event.msg.reply('Adicionando copypasta...')
        addPasta(pasta)
        msg.edit('Copypasta adicionado!')
        for key in event.msg.embeds:
            print(key.title, key.type, key.url)
        for key in event.msg.attachments.keys():
            print(event.msg.attachments[key].filename, event.msg.attachments[key].url)
        
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
        result = requests.get('https://br.api.pvp.net/api/lol/br/v1.4/summoner/by-name/' + name + '?api_key=' + riotApiKey)
        msg.edit('```\n'+ujson.dumps(ujson.loads(result.text), indent=4)+'\n```')

    @Plugin.command('spam', '<count:int> <content:str...>')
    def on_spam_command(self, event, count, content):
        if str(event.msg.author.id) in ownerid:
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
            if user.verified:
                parts.append('Verified: {}'.format(user.verified))
            if user.bot:
                parts.append('Bot: {}'.format(user.bot))

            if event.channel.guild:
                member = event.channel.guild.get_member(user)
                parts.append('Nickname: {}'.format(member.nick))
                parts.append('Joined At: {}'.format(member.joined_at))
                
            avatar_url = ''
            if user.avatar:
                avatar_url = '\nhttps://discordapp.com/api/users/{}/avatars/{}.jpg'.format(user.id, user.avatar)
            
            event.msg.reply(('```\n{}\n```'.format(
                '\n'.join(parts))
            )+avatar_url)
