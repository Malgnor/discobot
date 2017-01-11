from disco.bot import Bot, Plugin
from disco.types.user import Status, Game
from disco.types.message import MessageEmbed, MessageEmbedImage
from disco.bot.command import CommandLevels
from configparser import RawConfigParser
import disco
import sys
import requests
import ujson as json
import os
import random
import time

global riotApiKey, ownerid, commandsText, ownerCommandsText, autosave, channelLogId, copyCatId

reload(sys)
sys.setdefaultencoding('utf8')

def getConfig():
    global riotApiKey, ownerid, autosave, channelLogId
    config = RawConfigParser()
    try:
        config.read('config.cfg')
        ownerid = config.get('plugin', 'ownerid').split(',')
        autosave = bool(int(config.get('plugin', 'autosave')))
        channelLogId = int(config.get('plugin', 'channelLogId'))
        riotApiKey = config.get('riotapi', 'apikey')
    except(RawConfigParser.NoSectionError, RawConfigParser.NoOptionError):
        quit('The "config.cfg" file is missing or corrupt!')
        
def createConfigFile():
    with open('config.cfg', 'w') as cfg:
        cfg.write('[plugin]\nownerid = 000000000000000,1111111111\nautosave = 1\nchannelLogId = 0000000000000000\n\n[riotapi]\napikey = **************')

def getCommandsText():
    if not os.path.isfile('commands.txt'):
        return 'commands.txt não encontrado.'
    with open('commands.txt', 'r') as file:
        commands = file.read()
    return commands

def getOwnerCommandsText():
    if not os.path.isfile('ownercommands.txt'):
        return 'ownercommands.txt não encontrado.'
    with open('ownercommands.txt', 'r') as file:
        commands = file.read()
    return commands
        
if not os.path.isfile('config.cfg'):
    createConfigFile()

getConfig()
commandsText = getCommandsText()
ownerCommandsText = getOwnerCommandsText()
copyCatId = None

class PluginBase():        
    @Plugin.command('plugin')
    def on_plugin_command(self, event):
        event.msg.reply(self.name)
        
    @Plugin.command('reload', '<plugin:str>')
    def on_reload_command(self, event, plugin):
        if plugin == self.name:
            self.log.info('Reloading plugin: {}'.format(self.name))
            self.reload()