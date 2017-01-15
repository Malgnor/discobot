# coding=UTF-8

from disco.bot import Bot, Plugin
from disco.bot.command import CommandLevels
from Utils import savePluginConfig, loadPluginConfig, saveBotConfig, loadBotConfig
import json
    
class PluginManager(Plugin):
    def __init__(self, bot, config):
        super(PluginManager, self).__init__(bot, config)
        if self.bot.config and len(self.bot.config.levels):
            try:
                self.bot.config.levels = {int(k): v for k, v in self.bot.config.levels.items()}
            except Exception as e:
                self.log.info('`BotConfig.levels` keys should be `ints`')
            
    @Plugin.command('storage save', level=500, group='bot', description='Força o salvamento dos dados do bot.')
    def on_botstoragesave_command(self, event):
        if self.storage:
            self.storage.provider.save()
            event.msg.reply('Dados salvos.')
        else:
            event.msg.reply('Não há sistema de dados ativos.')
            
    @Plugin.command('config save', '[path:str...]', level=500, group='bot', description='Salva as configurações do bot/client.')
    def on_botsave_command(self, event, path='config.json'):
        try:
            saveBotConfig(self.bot, path)
            event.msg.reply('Configurações do bot/client salvas em {}.'.format(path))
        except Exception as e:
            event.msg.reply('Erro: {}.'.format(e))
            
    @Plugin.command('config reload', '[path:str...]', level=500, group='bot', description='Recarrega as configurações do bot/client.')
    def on_botreload_command(self, event, path='config.json'):
        try:
            if loadBotConfig(self.bot, path):
                event.msg.reply('Configurações do bot/client recarregadas.')
            else:
                event.msg.reply('Arquivo {} inexistente.'.format(path))
        except Exception as e:
            event.msg.reply('Erro: {}.'.format(e))

    @Plugin.command('level check', '[user:str...]', group='bot', level=10, description='Checa o nível de acesso de um usuário.')
    def on_levelcheck_command(self, event, user=None):
        user = user or event.msg.author.id
        try:
            uid = int(user)
        except ValueError:
            uid = user
        users = list(self.state.users.select({'username': user}, {'id': uid}))

        if not users:
            event.msg.reply("Couldn't find user for your query: `{}`".format(user))
        elif len(users) > 1:
            event.msg.reply('I found too many users ({}) for your query: `{}`'.format(len(users), user))
        else:
            event.msg.reply('{}: {}'.format(users[0].username, CommandLevels[self.bot.get_level(users[0] if not event.msg.guild else event.msg.guild.get_member(users[0]))]))
    
    @Plugin.command('level set', '<userid:snowflake> <targetLevel:str>', group='bot', level=500, description='Altera o nível de acesso de um usuário.')
    def on_levelset_command(self, event, userid, targetLevel):
        if not CommandLevels[targetLevel]:
            event.msg.reply('{} é invalido.'.format(targetLevel))
            return
            
        self.bot.config.levels[userid] = targetLevel
            
        event.msg.reply('{} agora é {}.'.format(userid, targetLevel))
        
    @Plugin.command('config edit', '<plugin:str> <key:str> <value:str...>', level=100, group='plugin', description='Altera uma configuração do plugin')
    def on_configedit_command(self, event, plugin, key, value):
        if plugin in self.bot.plugins:
            plugin = self.bot.plugins[plugin]
            if plugin.config:
                if key in plugin.config:
                    if type(plugin.config[key]) in [type(list()), type(dict())]:
                        event.msg.reply('Tipo de valor da chave {} não suportado pelo comando. Tipo: {}'.format(key, type(plugin.config[key])))
                        return
                    try:
                        value = type(plugin.config[key])(value)
                    except ValueError:
                        event.msg.reply('Valor {} não pode ser convertido para o mesmo tipo da chave {}.'.format(value, key))
                        return
                    except TypeError:
                        event.msg.reply('Valor {} não pode ser convertido para o mesmo tipo da chave {}.'.format(value, key))
                        return
                    plugin.config[key] = value
                    event.msg.reply('Valor da chave {} alterada para {}.'.format(key, value))
                else:
                    event.msg.reply('Plugin {} não possui {} nas configurações.'.format(plugin.name, key))
            else:
                event.msg.reply('Plugin {} não possui configurações.'.format(plugin.name))
        else:
            event.msg.reply('Plugin {} não encontrado.'.format(plugin))
        
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
        
    @Plugin.command('config view', '[plugin:str]', group='plugin', level=100, description='Mostra as configurações de um plugin.')
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
        
    @Plugin.command('config save', '[plugin:str] [format:str]', group='plugin', level=500, description='Salva as configurações de um plugin.')
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
        
    @Plugin.command('config reload', '[plugin:str] [format:str]', group='plugin', level=500, description='Recarrega as configurações de um plugin.')
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