import json

from disco.bot import Plugin
from disco.bot.command import CommandLevels
from Utils import save_plugin_config, load_plugin_config, save_bot_config, load_bot_config


class ManagerPlugin(Plugin):
    @Plugin.command('storage save', group='bot', description='Força o salvamento dos dados do bot.', hide=True)
    def on_botstoragesave_command(self, event):
        if self.storage:
            self.storage.save()
            event.msg.reply('Dados salvos.')
        else:
            event.msg.reply('Não há sistema de dados ativos.')

    @Plugin.command('config save', '[path:str...]', group='bot', description='Salva as configurações do bot/client.', hide=True)
    def on_botsave_command(self, event, path='config.json'):
        try:
            save_bot_config(self.bot, path)
            event.msg.reply(
                'Configurações do bot/client salvas em {}.'.format(path))
        except Exception as exception:
            event.msg.reply('Erro: {}.'.format(exception))

    @Plugin.command('config reload', '[path:str...]', group='bot', description='Recarrega as configurações do bot/client.', hide=True)
    def on_botreload_command(self, event, path='config.json'):
        try:
            if load_bot_config(self.bot, path):
                event.msg.reply('Configurações do bot/client recarregadas.')
            else:
                event.msg.reply('Arquivo {} inexistente.'.format(path))
        except Exception as exception:
            event.msg.reply('Erro: {}.'.format(exception))

    @Plugin.command('config edit', '<plugin:str> <key:str> <value:str...>', group='plugin', description='Altera uma configuração do plugin', hide=True)
    def on_configedit_command(self, event, plugin, key, value):
        if plugin in self.bot.plugins:
            plugin = self.bot.plugins[plugin]
            if plugin.config:
                if key in plugin.config:
                    if isinstance(plugin.config[key], (list, dict)):
                        event.msg.reply('Tipo de valor da chave {} não suportado pelo comando. Tipo: {}'.format(
                            key, type(plugin.config[key])))
                        return
                    try:
                        value = type(plugin.config[key])(value)
                    except ValueError:
                        event.msg.reply(
                            'Valor {} não pode ser convertido para o mesmo tipo da chave {}.'.format(value, key))
                        return
                    except TypeError:
                        event.msg.reply(
                            'Valor {} não pode ser convertido para o mesmo tipo da chave {}.'.format(value, key))
                        return
                    plugin.config[key] = value
                    event.msg.reply(
                        'Valor da chave {} alterada para {}.'.format(key, value))
                else:
                    event.msg.reply(
                        'Plugin {} não possui {} nas configurações.'.format(plugin.name, key))
            else:
                event.msg.reply(
                    'Plugin {} não possui configurações.'.format(plugin.name))
        else:
            event.msg.reply('Plugin {} não encontrado.'.format(plugin))

    @Plugin.command('list', group='plugin', description='Mostra a lista de plugins.')
    def on_pluginlist_command(self, event):
        event.msg.reply('\n'.join(self.bot.plugins))

    @Plugin.command('groups', group='plugin', description='Mostra a lista de grupos de comandos e sua menor abreviação usável.')
    def on_plugingroups_command(self, event):
        message = '```css\n'
        message += 'Grupo:Abreviação\n\n'
        for group, abbrev in self.bot.group_abbrev.items():
            message += '{}:{}\n'.format(group, abbrev)
        message += '```'
        event.msg.reply(message)

    @Plugin.command('reload', '<plugin:str>', group='plugin', description='Recarrega um plugin.', oob=True, hide=True)
    def on_pluginreload_command(self, event, plugin):
        self.client.api.channels_typing(event.msg.channel_id)

        if plugin in self.bot.plugins:
            self.bot.plugins[plugin].reload()
            event.msg.reply('Plugin {} recarregado.'.format(plugin))
        else:
            event.msg.reply('Plugin {} não encontrado.'.format(plugin))
            return

    @Plugin.command('add', '<plugin:str>', group='plugin', description='Recarrega um plugin.', oob=True, hide=True)
    def on_pluginadd_command(self, event, plugin):
        self.client.api.channels_typing(event.msg.channel_id)
        try:
            self.bot.add_plugin_module(plugin)
        except Exception as exception:
            event.msg.reply(
                'Erro ao tentar adicionar plugin {}: {}.'.format(plugin, exception))
            return

        event.msg.reply('Plugin {} carregado.'.format(plugin))

    @Plugin.command('remove', '<plugin:str>', group='plugin', description='Recarrega um plugin.', oob=True, hide=True)
    def on_pluginremove_command(self, event, plugin):
        self.client.api.channels_typing(event.msg.channel_id)

        if plugin in self.bot.plugins:
            self.bot.rmv_plugin(self.bot.plugins[plugin].__class__)
            event.msg.reply('Plugin {} removido.'.format(plugin))
        else:
            event.msg.reply('Plugin {} não encontrado.'.format(plugin))
            return

    @Plugin.command('config view', '[plugin:str]', group='plugin', description='Mostra as configurações de um plugin.', hide=True)
    def on_config_command(self, event, plugin=None):
        self.client.api.channels_typing(event.msg.channel_id)

        if plugin:
            if plugin in self.bot.plugins:
                plugin = self.bot.plugins[plugin]
                if plugin.config:
                    event.msg.reply('{}:```json\n{}```'.format(
                        plugin.name, json.dumps(plugin.config, indent=4)))
                else:
                    event.msg.reply(
                        'Plugin {} não possui configurações.'.format(plugin.name))
            else:
                event.msg.reply('Plugin {} não encontrado.'.format(plugin))
        else:
            configs = []
            for plugin_ in self.bot.plugins.values():
                if plugin_.config:
                    configs.append('{}:```json\n{}```'.format(
                        plugin_.name, json.dumps(plugin_.config, indent=4)))
            to_send = ''
            for config in configs:
                if len(to_send + config) > 2000:
                    event.msg.reply(to_send)
                    to_send = ''
                to_send += config
            event.msg.reply(to_send)

    @Plugin.command('config save', '[plugin:str] [fmt:str]', group='plugin', description='Salva as configurações de um plugin.', hide=True)
    def on_config_save_command(self, event, plugin=None, fmt=None):
        self.client.api.channels_typing(event.msg.channel_id)

        if plugin:
            if plugin in self.bot.plugins:
                plugin = self.bot.plugins[plugin]
                if plugin.config:
                    save_plugin_config(self.bot, plugin, fmt)
                    event.msg.reply(
                        'Configurações do plugin {} foram salvas.'.format(plugin.name))
                else:
                    event.msg.reply(
                        'Plugin {} não possui configurações.'.format(plugin.name))
            else:
                event.msg.reply('Plugin {} não encontrado.'.format(plugin))
        else:
            saved = []
            for plugin_ in self.bot.plugins.values():
                if plugin_.config:
                    save_plugin_config(self.bot, plugin_, fmt)
                    saved.append(plugin_.name)
            event.msg.reply(
                'Configurações dos plugins {} foram salvas.'.format(', '.join(saved)))

    @Plugin.command('config reload', '[plugin:str] [fmt:str]', group='plugin', description='Recarrega as configurações de um plugin.', hide=True)
    def on_config_reload_command(self, event, plugin=None, fmt=None):
        self.client.api.channels_typing(event.msg.channel_id)

        if plugin:
            if plugin in self.bot.plugins:
                plugin = self.bot.plugins[plugin]
                if plugin.config:
                    plugin.config = load_plugin_config(
                        self.bot, plugin, fmt)
                    event.msg.reply(
                        'Configurações do plugin {} foram recarregadas.'.format(plugin.name))
                else:
                    event.msg.reply(
                        'Plugin {} não possui configurações.'.format(plugin.name))
            else:
                event.msg.reply('Plugin {} não encontrado.'.format(plugin))
        else:
            loaded = []
            for plugin_ in self.bot.plugins.values():
                if plugin_.config:
                    plugin_.config = load_plugin_config(
                        self.bot, plugin_, fmt)
                    loaded.append(plugin_.name)
            event.msg.reply(
                'Configurações dos plugins {} foram recarregadas.'.format(', '.join(loaded)))

    @Plugin.command('help', '[plugin:str]', aliases=['ajuda', 'command', 'commands'], description='Mostra a lista de comandos disponíveis para você.')
    def on_help_command(self, event, plugin=None):

        if self.bot.config.http_enabled:
            with self.bot.http.app_context():
                from flask import url_for
                return event.msg.reply(url_for('on_plugins_route', plugin=plugin if plugin else None))

        self.client.api.channels_typing(event.msg.channel_id)

        plugins = self.bot.plugins.values()

        if plugin:
            if plugin in self.bot.plugins:
                plugins = [self.bot.plugins[plugin]]
            else:
                event.msg.reply('Plugin {} não encontrado.'.format(plugin))
                return

        commands = []
        for plugin_ in plugins:
            text = '{}```css\n'.format(plugin_.name)
            count = 0
            level = plugin_.bot.get_level(
                event.msg.author if not event.msg.guild else event.msg.guild.get_member(event.msg.author))
            for command in plugin_.commands:
                if ((command.level and level >= command.level) or not command.level) and not ('hide' in command.metadata and command.metadata['hide']):
                    count += 1
                    text += '\n'
                    info = []
                    if command.group:
                        info.append('{}'.format(command.group))
                    info.append('{}'.format('|'.join(command.triggers)))
                    if command.args:
                        args = []
                        for arg in command.args.args:
                            args.append('{}{}:{}{}'.format(
                                '' if arg.required else '[', arg.name, '|'.join(arg.types), '' if arg.required else ']'))
                        info.append('{}'.format(' '.join(args)))
                    info.append('\n')
                    if command.level:
                        info.append('\tLevel: {}'.format(
                            CommandLevels[command.level]))
                    if 'description' in command.metadata:
                        info.append('\tDescription: {}'.format(
                            command.metadata['description']))

                    text += ' '.join(info)
            text += '```'
            if count:
                commands.append(text)
        to_send = ''
        for command in commands:
            if len(to_send + command) > 2000:
                event.msg.reply(to_send)
                to_send = ''
            to_send += command
        event.msg.reply(to_send)

    @Plugin.route('/')
    def on_plugins_route(self):
        from flask import render_template, request

        arg_plugin = request.args.get('plugin', None)

        plugins = []
        for plugin in self.bot.plugins.values():
            if arg_plugin and not plugin.name == arg_plugin:
                continue

            value = {}
            value['name'] = plugin.name
            value['commands'] = []

            for cmd in plugin.commands:
                if 'hide' in cmd.metadata and cmd.metadata['hide']:
                    continue

                command = {}
                command['group'] = cmd.group+' ' if cmd.group else ''
                command['triggers'] = '|'.join(cmd.triggers)

                if cmd.args:
                    command['args'] = []
                    for arg in cmd.args.args:
                        command['args'].append(('{}{}:{}{}'.format('' if arg.required else '[', arg.name, '|'.join(arg.types), '' if arg.required else ']'), arg.required))

                if 'description' in cmd.metadata:
                    command['description'] = cmd.metadata['description']

                value['commands'].append(command)

            plugins.append(value)

        return render_template('plugins.html', plugins=plugins)
    