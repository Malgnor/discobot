from disco.bot import Bot, Plugin
from disco.types.user import Status, Game
from disco.types.message import MessageEmbed, MessageEmbedImage
import disco
import sys
import requests
import ujson as json
import os
import random
import time

import ruamel.yaml
import warnings
warnings.simplefilter('ignore', ruamel.yaml.error.UnsafeLoaderWarning)

reload(sys)
sys.setdefaultencoding('utf8')

class PluginBase():
    def saveConfig(self):
        if not self.config:
            self.log.info('There is no configuration to save.')
            return
        
        name = self.name
        if name.endswith('plugin'):
            name = name[:-6]

        path = os.path.join(
            self.bot.config.plugin_config_dir, name) + '.' + self.bot.config.plugin_config_format

        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        
        with open(path, 'w') as file:
            file.write(ruamel.yaml.dump(self.config))
        self.log.info('{} saved.'.format(path))
        
    def loadConfig(self):
        self.log.info('Reloading config for plugin: {}'.format(self.name))
        
        name = self.name
        if name.endswith('plugin'):
            name = name[:-6]

        path = os.path.join(
            self.bot.config.plugin_config_dir, name) + '.' + self.bot.config.plugin_config_format
        
        if not os.path.exists(path):
            if hasattr(self, 'config_cls'):
                return self.config_cls()
            return
        
        with open(path, 'r') as file:
            data = ruamel.yaml.load(file.read())

        if hasattr(self, 'config_cls'):
            inst = self.config_cls()
            inst.update(data)
            return inst

        return data
        
    @Plugin.command('plugins')
    def on_plugins_command(self, event):
        event.msg.reply(self.name)
        
    @Plugin.command('config', '[plugin:str]')
    def on_config_command(self, event, plugin=None):
        if (plugin and plugin == self.name) or not plugin:
            event.msg.reply('```{}```'.format(json.dumps(self.config, indent=4)))
        
    @Plugin.command('configSave', '[plugin:str]')
    def on_configSave_command(self, event, plugin=None):
        if (plugin and plugin == self.name) or not plugin:
            self.saveConfig()
        
    @Plugin.command('configReload', '[plugin:str]')
    def on_configReload_command(self, event, plugin=None):
        if (plugin and plugin == self.name) or not plugin:
            self.config = self.loadConfig()