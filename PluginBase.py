from disco.bot import Bot, Plugin
from disco.types.user import Status, Game
from disco.types.message import MessageEmbed, MessageEmbedImage
from disco.bot.command import CommandLevels
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

def AttachmentToEmbed(attachments):
    embed = None
    if len(attachments):
        for k in attachments.keys():
            embed = MessageEmbed(title = attachments[k].filename, url = attachments[k].url)
            embed.image = MessageEmbedImage(url = attachments[k].url, proxy_url = attachments[k].proxy_url, width = attachments[k].width, height = attachments[k].height) if attachments[k].width else None
            break
    return embed

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
        
    @Plugin.command('plugins', level=10, aliases=['plugin', 'pluginList', 'listPlugins', 'listPlugin'], hide=True)
    def on_plugins_command(self, event):
        event.msg.reply(self.name)
        
    @Plugin.command('config', '[plugin:str]', level=100, hide=True)
    def on_config_command(self, event, plugin=None):
        if (plugin and plugin == self.name) or not plugin:
            event.msg.reply('{}:```{}```'.format(self.name, json.dumps(self.config, indent=4)))
        
    @Plugin.command('configSave', '[plugin:str]', level=500, hide=True)
    def on_configSave_command(self, event, plugin=None):
        if (plugin and plugin == self.name) or not plugin:
            self.saveConfig()
            event.msg.reply('Saved config for: {}'.format(self.name))
        
    @Plugin.command('configReload', '[plugin:str]', level=500, hide=True)
    def on_configReload_command(self, event, plugin=None):
        if (plugin and plugin == self.name) or not plugin:
            self.config = self.loadConfig()
            event.msg.reply('Reloaded config for: {}'.format(self.name))
        
    @Plugin.command('help', '[plugin:str]', description='Mostra a lista de comandos disponíveis para você.', hide=True)
    def on_help_command(self, event, plugin=None):
        if (plugin and plugin == self.name) or not plugin:
            r = '{}```'.format(self.name)
            count = 0
            level = self.bot.get_level(event.msg.author if not event.msg.guild else event.msg.guild.get_member(event.msg.author))
            for c in self.commands:
                if ((c.level and level >= c.level) or not c.level) and not ('hide' in c.metadata and c.metadata['hide']):
                    count += 1
                    r += '\n'
                    ci = []
                    ci.append('{}'.format(c.triggers[0]))
                    if c.args.length:
                        aa = []
                        for a in c.args.args:
                            aa.append('{}{}:{}{}'.format('' if a.required else '[', a.name, '|'.join(a.types), '' if a.required else ']'))
                        ci.append('{}'.format(' '.join(aa)))
                    if 'description' in c.metadata:
                        ci.append('\n\tDescription: {}'.format(c.metadata['description']))
                    ci.append('\n\tLevel: {}'.format(CommandLevels[c.level]))
                    if c.group:
                        ci.append('\tGroup: {}'.format(c.group))
                    if c.triggers[1:]:
                        ci.append('\tAliases: {}'.format(', '.join(c.triggers[1:])))
                        
                    r += ' '.join(ci)
            r += '```'
            if count:
                event.msg.reply(r)