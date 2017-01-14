# coding=UTF-8

from disco.bot import Bot, Plugin
from disco.types.message import MessageEmbed
from disco.bot.command import CommandLevels
import json, os, warnings, ruamel.yaml

warnings.simplefilter('ignore', ruamel.yaml.error.UnsafeLoaderWarning)

def AttachmentToEmbed(attachments):
    embed = None
    if len(attachments):
        for attachment in attachments.values():
            embed = MessageEmbed(title = attachment.filename, url = attachment.url)
            embed.set_image(url = attachment.url, proxy_url = attachment.proxy_url, width = attachment.width, height = attachment.height) if attachment.width else None
            break
    return embed
    
def EmbedImageFromUrl(iurl):
    if not iurl:
        return None
    embed = MessageEmbed(url = iurl)
    embed.set_image(url = iurl)
    return embed

def saveConfig(plugin):
    if not plugin.config:
        plugin.log.info('There is no configuration to save.')
        return
    
    name = plugin.name
    if name.endswith('plugin'):
        name = name[:-6]

    path = os.path.join(
        plugin.bot.config.plugin_config_dir, name) + '.' + plugin.bot.config.plugin_config_format

    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    
    with open(path, 'w') as file:
        file.write(ruamel.yaml.dump(plugin.config))
    plugin.log.info('{} saved.'.format(path))
    
def loadConfig(plugin):
    plugin.log.info('Reloading config for plugin: {}'.format(plugin.name))
    
    name = plugin.name
    if name.endswith('plugin'):
        name = name[:-6]

    path = os.path.join(
        plugin.bot.config.plugin_config_dir, name) + '.' + plugin.bot.config.plugin_config_format
    
    if not os.path.exists(path):
        if hasattr(plugin, 'config_cls'):
            return plugin.config_cls()
        return
    
    with open(path, 'r') as file:
        data = ruamel.yaml.load(file.read())

    if hasattr(plugin, 'config_cls'):
        inst = plugin.config_cls()
        inst.update(data)
        return inst

    return data
    
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
        
    @Plugin.command('save', '[plugin:str]', group='config', level=500, description='Salva as configurações de um plugin.')
    def on_configSave_command(self, event, plugin=None):
        self.client.api.channels_typing(event.msg.channel_id)
        
        if plugin:
            if plugin in self.bot.plugins:
                plugin = self.bot.plugins[plugin]
                if plugin.config:
                    saveConfig(plugin)
                    event.msg.reply('Configurações do plugin {} foram salvas.'.format(plugin.name))
                else:
                    event.msg.reply('Plugin {} não possui configurações.'.format(plugin.name))
            else:
                event.msg.reply('Plugin {} não encontrado.'.format(plugin))
        else:
            saved = []
            for plugin in self.bot.plugins.values():
                if plugin.config:
                    saveConfig(plugin)
                    saved.append(plugin.name)
            event.msg.reply('Configurações dos plugins {} foram salvas.'.format(', '.join(saved)))
        
    @Plugin.command('reload', '[plugin:str]', group='config', level=500, description='Recarrega as configurações de um plugin.')
    def on_configReload_command(self, event, plugin=None):
        self.client.api.channels_typing(event.msg.channel_id)
        
        if plugin:
            if plugin in self.bot.plugins:
                plugin = self.bot.plugins[plugin]
                if plugin.config:
                    plugin.config = loadConfig(plugin)
                    event.msg.reply('Configurações do plugin {} foram recarregadas.'.format(plugin.name))
                else:
                    event.msg.reply('Plugin {} não possui configurações.'.format(plugin.name))
            else:
                event.msg.reply('Plugin {} não encontrado.'.format(plugin))
        else:
            loaded = []
            for plugin in self.bot.plugins.values():
                if plugin.config:
                    plugin.config = loadConfig(plugin)
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