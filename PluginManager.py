# coding=UTF-8

from disco.bot import Bot, Plugin
from disco.bot.command import CommandLevels
from Utils import savePluginConfig, loadPluginConfig
import json
    
class PluginManager(Plugin):        
    @Plugin.command('list', level=10, group='plugin' , description='Mostra a lista de plugins.')
    def on_pluginlist_command(self, event):
        event.msg.reply('\n'.join(self.bot.plugins))   
        
    @Plugin.command('groups', level=10, group='plugin' , description='Mostra a lista de grupos de comandos e sua menor abreviação usável.')
    def on_plugingroups_command(self, event):
        m = '```css\n'
        m += 'Grupo:Abreviação\n\n'
        for group, abbrev in self.bot.group_abbrev.items():
            m += '{}:{}\n'.format(group, abbrev)
        m += '```'
        event.msg.reply(m)
        
    @Plugin.command('reload', '<plugin:str>', group='plugin', level=100, description='Recarrega um plugin.', oob=True)
    def on_pluginreload_command(self, event, plugin):
        self.client.api.channels_typing(event.msg.channel_id)
        
        if plugin in self.bot.plugins:
            self.bot.plugins[plugin].reload()
            event.msg.reply('Plugin {} recarregado.'.format(plugin))
        else:
            event.msg.reply('Plugin {} não encontrado.'.format(plugin))
            return
        
    @Plugin.command('add', '<plugin:str>', group='plugin', level=100, description='Recarrega um plugin.', oob=True)
    def on_pluginadd_command(self, event, plugin):
        self.client.api.channels_typing(event.msg.channel_id)
        try:
            self.bot.add_plugin_module(plugin)
        except e:
            event.msg.reply('Erro ao tentar adicionar plugin {}: {}.'.format(plugin, e))
            return
        
        event.msg.reply('Plugin {} carregado.'.format(plugin))
        
    @Plugin.command('remove', '<plugin:str>', group='plugin', level=100, description='Recarrega um plugin.', oob=True)
    def on_pluginremove_command(self, event, plugin):
        self.client.api.channels_typing(event.msg.channel_id)
        
        if plugin in self.bot.plugins:
            self.bot.rmv_plugin(self.bot.plugins[plugin].__class__)
            event.msg.reply('Plugin {} removido.'.format(plugin))
        else:
            event.msg.reply('Plugin {} não encontrado.'.format(plugin))
            return
        
    @Plugin.command('view', '[plugin:str]', group='config', level=100, description='Mostra as configurações de um plugin.')
    def on_config_command(self, event, plugin=None):
        self.client.api.channels_typing(event.msg.channel_id)
        
        if plugin:
            if plugin in self.bot.plugins:
                plugin = self.bot.plugins[plugin]
                if plugin.config:
                    event.msg.reply('{}:```json\n{}```'.format(plugin.name, json.dumps(plugin.config, indent=4)))
                else:
                    event.msg.reply('Plugin {} não possui configurações.'.format(plugin.name))
            else:
                event.msg.reply('Plugin {} não encontrado.'.format(plugin))
        else:
            configs = []
            for plugin in self.bot.plugins.values():
                if plugin.config:
                    configs.append('{}:```json\n{}```'.format(plugin.name, json.dumps(plugin.config, indent=4)))
            toSend = ''
            for config in configs:
                if len(toSend+config) > 2000:
                    event.msg.reply(toSend)
                    toSend = ''
                toSend += config
            event.msg.reply(toSend)
        
    @Plugin.command('save', '[plugin:str] [format:str]', group='config', level=500, description='Salva as configurações de um plugin.')
    def on_configSave_command(self, event, plugin=None, format=None):
        self.client.api.channels_typing(event.msg.channel_id)
        
        if plugin:
            if plugin in self.bot.plugins:
                plugin = self.bot.plugins[plugin]
                if plugin.config:
                    savePluginConfig(self.bot, plugin, format)
                    event.msg.reply('Configurações do plugin {} foram salvas.'.format(plugin.name))
                else:
                    event.msg.reply('Plugin {} não possui configurações.'.format(plugin.name))
            else:
                event.msg.reply('Plugin {} não encontrado.'.format(plugin))
        else:
            saved = []
            for plugin in self.bot.plugins.values():
                if plugin.config:
                    savePluginConfig(self.bot, plugin, format)
                    saved.append(plugin.name)
            event.msg.reply('Configurações dos plugins {} foram salvas.'.format(', '.join(saved)))
        
    @Plugin.command('reload', '[plugin:str] [format:str]', group='config', level=500, description='Recarrega as configurações de um plugin.')
    def on_configReload_command(self, event, plugin=None, format=None):
        self.client.api.channels_typing(event.msg.channel_id)
        
        if plugin:
            if plugin in self.bot.plugins:
                plugin = self.bot.plugins[plugin]
                if plugin.config:
                    plugin.config = loadPluginConfig(self.bot, plugin, format)
                    event.msg.reply('Configurações do plugin {} foram recarregadas.'.format(plugin.name))
                else:
                    event.msg.reply('Plugin {} não possui configurações.'.format(plugin.name))
            else:
                event.msg.reply('Plugin {} não encontrado.'.format(plugin))
        else:
            loaded = []
            for plugin in self.bot.plugins.values():
                if plugin.config:
                    plugin.config = loadPluginConfig(self.bot, plugin, format)
                    loaded.append(plugin.name)
            event.msg.reply('Configurações dos plugins {} foram recarregadas.'.format(', '.join(loaded)))
        
    @Plugin.command('help', '[plugin:str]', aliases=['ajuda', 'command', 'commands'], description='Mostra a lista de comandos disponíveis para você.')
    def on_help_command(self, event, plugin=None):
        self.client.api.channels_typing(event.msg.channel_id)
        
        if plugin:
            if plugin in self.bot.plugins:
                plugin = self.bot.plugins[plugin]
                r = '{}```css\n'.format(plugin.name)
                count = 0
                level = plugin.bot.get_level(event.msg.author if not event.msg.guild else event.msg.guild.get_member(event.msg.author))
                for c in plugin.commands:
                    if ((c.level and level >= c.level) or not c.level) and not ('hide' in c.metadata and c.metadata['hide']):
                        count += 1
                        r += '\n'
                        ci = []
                        if c.group:
                            ci.append('{}'.format(c.group))
                        ci.append('{}'.format('|'.join(c.triggers)))
                        if c.args.length:
                            aa = []
                            for a in c.args.args:
                                aa.append('{}{}:{}{}'.format('' if a.required else '[', a.name, '|'.join(a.types), '' if a.required else ']'))
                            ci.append('{}'.format(' '.join(aa)))
                        ci.append('\n\tLevel: {}'.format(CommandLevels[c.level]))
                        if 'description' in c.metadata:
                            ci.append('\tDescription: {}'.format(c.metadata['description']))
                            
                        r += ' '.join(ci)
                r += '```'
                if count:
                    event.msg.reply(r)
                else:
                    event.msg.reply('Plugin {} não possui comandos disponíveis para você.'.format(plugin.name))
            else:
                event.msg.reply('Plugin {} não encontrado.'.format(plugin))
        else:
            commands = []
            for plugin in self.bot.plugins.values():
                r = '{}```css\n'.format(plugin.name)
                count = 0
                level = plugin.bot.get_level(event.msg.author if not event.msg.guild else event.msg.guild.get_member(event.msg.author))
                for c in plugin.commands:
                    if ((c.level and level >= c.level) or not c.level) and not ('hide' in c.metadata and c.metadata['hide']):
                        count += 1
                        r += '\n'
                        ci = []
                        if c.group:
                            ci.append('{}'.format(c.group))
                        ci.append('{}'.format('|'.join(c.triggers)))
                        if c.args.length:
                            aa = []
                            for a in c.args.args:
                                aa.append('{}{}:{}{}'.format('' if a.required else '[', a.name, '|'.join(a.types), '' if a.required else ']'))
                            ci.append('{}'.format(' '.join(aa)))
                        ci.append('\n\tLevel: {}'.format(CommandLevels[c.level]))
                        if 'description' in c.metadata:
                            ci.append('\tDescription: {}'.format(c.metadata['description']))
                            
                        r += ' '.join(ci)
                r += '```'
                if count:
                    commands.append(r)
            toSend = ''
            for command in commands:
                if len(toSend+command) > 2000:
                    event.msg.reply(toSend)
                    toSend = ''
                toSend += command
            event.msg.reply(toSend)