# coding=UTF-8

from disco.bot import Bot, Plugin
from disco.bot.command import CommandLevels
from disco.types.user import Status, Game
from PluginManager import AttachmentToEmbed, EmbedImageFromUrl
import disco, warnings, ruamel.yaml, json

warnings.simplefilter('ignore', ruamel.yaml.error.UnsafeLoaderWarning)

class Master(Plugin):
    @staticmethod
    def config_cls():
        config = {}
        config['channelLogId'] = None
        config['channelDMId'] = None
        config['copyCatId'] = []
        config['client_config_name'] = 'config.yaml'
        return config

    @Plugin.listen('Ready')
    def on_ready(self, event):
        if self.config['channelLogId']:
            self.client.api.channels_messages_create(self.config['channelLogId'], 'I am ready!\nDisco-py: {}'.format(disco.VERSION))

    @Plugin.listen('GuildCreate')
    def on_guild_create(self, event):
        if self.config['channelLogId']:
            if event.created:
                self.client.api.channels_messages_create(self.config['channelLogId'], 'Entrei no servidor: {}'.format(event.name))

    @Plugin.listen('GuildDelete')
    def on_guild_delete(self, event):
        if self.config['channelLogId']:
            if event.deleted:
                self.client.api.channels_messages_create(self.config['channelLogId'], 'Saindo do servidor: {}'.format(event.id))

    @Plugin.listen('MessageCreate')
    def on_message_create(self, event):
        if event.author == self.state.me:
            return
        if event.channel.type == 1 and self.config['channelDMId']:
            self.client.api.channels_messages_create(self.config['channelDMId'], '[DM]{}: {}'.format(event.author.mention, event.content), event.nonce, event.tts, None, AttachmentToEmbed(event.attachments))
        if event.author.id in self.config['copyCatId']:
            self.client.api.channels_messages_create(event.channel_id, event.content, event.nonce, event.tts, None, AttachmentToEmbed(event.attachments))            

    @Plugin.listen('TypingStart')
    def on_typing_start(self, event):
        if event.user_id in self.config['copyCatId']:
            self.client.api.channels_typing(event.channel_id)
        
    @Plugin.command('updatePresence', '<status:str> [game:str...]', level=100, description='Atualiza o status e o jogo atual do bot.')
    def on_updatepresence_command(self, event, status, game=None):
        if not Status[status]:
            status = 'ONLINE'
        self.client.update_presence(Game(name=game), Status[status])
        event.msg.reply('Atualizando status...')
        
    @Plugin.command('setCopyCat', '[target:snowflake]', level=100, description='Faz o bot imitar usuários.')
    def on_setcopycat_command(self, event, target=None):
        if not target:
            r = 'Alvos:\n' if len(self.config['copyCatId']) else 'Não há alvos.'
            
            for t in self.config['copyCatId']:
                r += '<@{}>\n'.format(t)
                
            event.msg.reply(r)
            return
        
        if target == self.state.me.id:
            event.msg.reply('<@{}> não pode ser alvo.'.format(target))
            return
        
        if target == 1:
            target = event.msg.author.id
            
        if target in self.config['copyCatId']:
            self.config['copyCatId'].remove(target)
            event.msg.reply('<@{}> removido como alvo.'.format(target))
        else:
            self.config['copyCatId'].append(target)
            event.msg.reply('<@{}> adicionado como alvo.'.format(target))
        
    @Plugin.command('quit', level=500, description='Encerra o bot.')
    def on_quit_command(self, event):
        event.msg.reply('Bye!')
        self.log.info('Calling quit().')
        quit()

    @Plugin.command('saychannel', '<cid:snowflake> <content:str...>', level=50, description='Manda uma mensagem para um canal.')
    def on_saychannel_command(self, event, cid, content):
        self.client.api.channels_messages_create(cid, content)

    @Plugin.command('faketype', '<cid:snowflake>', level=50, description='Manda evento de \'digitando\' para um canal.')
    def on_faketype_command(self, event, cid):
        self.client.api.channels_typing(cid)

    @Plugin.command('check', '[user:str...]', group='level', level=10, description='Checa o nível de acesso de um usuário.')
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
    
    @Plugin.command('set', '<userid:snowflake> <targetLevel:str>', group='level', level=500, description='Altera o nível de acesso de um usuário.')
    def on_levelset_command(self, event, userid, targetLevel):
        if not CommandLevels[targetLevel]:
            event.msg.reply('{} é invalido.'.format(targetLevel))
            return
            
        self.bot.config.levels[userid] = targetLevel
        
        with open(self.config['client_config_name'], 'r') as file:
            c = ruamel.yaml.load(file.read())
        
        c['bot']['levels'][userid] = targetLevel
        
        with open(self.config['client_config_name'], 'w') as file:
            file.write(ruamel.yaml.dump(c))
            
        event.msg.reply('{} agora é {}.'.format(userid, targetLevel))
            
    @Plugin.command('group', level=100, description='Checa as abreviações de grupos de comandos.')
    def on_group_command(self, event):
        event.msg.reply(json.dumps(self.bot.group_abbrev))
        
        # groups = set(command.group for command in self.bot.commands if command.group)
        
        # event.msg.reply(json.dumps(groups))
        
        # abbrev = {}
        
        # for group in groups:
            # for i in range(1, len(group)):
                # if not group[:i] in abbrev.values():
                    # abbrev[group] = group[:i]
                    # break
                # conflict = {k: k[:i+1] for k, v in abbrev.items() if v == group[:i]}
                # abbrev.update(conflict)
                
        # self.bot.group_abbrev.update(abbrev)
        # self.bot.compute_command_matches_re()
        # event.msg.reply(json.dumps(self.bot.group_abbrev))
            
    # @Plugin.command('test', group='test', level=100)
    # def on_test1_command(self, event):
        # pass
        
    # @Plugin.command('tag', group='tag', level=100)
    # def on_test2_command(self, event):
        # pass
            
    # @Plugin.command('boots', group='boots', level=100)
    # def on_test3_command(self, event):
        # pass
        
    # @Plugin.command('boat', group='boat', level=100)
    # def on_test4_command(self, event):
        # pass
            
    # @Plugin.command('work', group='work', level=100)
    # def on_test5_command(self, event):
        # pass
        
    # @Plugin.command('word', group='word', level=100)
    # def on_test6_command(self, event):
        # pass
        
    @Plugin.command('listRoles', level=100, description='Mostra uma lista com os cargos de um servidor.')
    def on_listroles_command(self, event):
        if not event.channel.guild:
            event.msg.reply('Este canal não faz parte de um servidor.')
            return
            
        m = '```css\n'
        for role in event.channel.guild.roles.values():
            m += '{}:{}\n'.format(role.name, role.id)
        m += '```'
        event.msg.reply(m)
        
    @Plugin.command('info', '<query:str...>', level=10, description='Mostra informações sobre um usuário.')
    def on_info_command(self, event, query):
    
        try:
            uid = int(query)
        except ValueError:
            uid = query
            
        users = list(self.state.users.select({'username': query}, {'id': uid}))

        if not users:
            event.msg.reply("Couldn't find user for your query: `{}`".format(query))
        elif len(users) > 1:
            event.msg.reply('I found too many users ({}) for your query: `{}`'.format(len(users), query))
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
                if member.nick:
                    parts.append('Nickname: {}'.format(member.nick))
                parts.append('Joined At: {}'.format(member.joined_at))
                
            event.msg.reply(('```\n{}\n```'.format(
                '\n'.join(parts))
            ), embed=EmbedImageFromUrl(user.avatar_url))
