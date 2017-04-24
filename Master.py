# coding=UTF-8

from disco.bot import Bot, Plugin
from disco.bot.command import CommandLevels
from disco.types.user import Status, Game
from Utils import AttachmentToEmbed, EmbedImageFromUrl
import disco, json, re, ntpath, requests

class Master(Plugin):
    @staticmethod
    def config_cls():
        config = {}
        config['channelLogId'] = 0
        config['channelDMId'] = 0
        config['copyCatId'] = []
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
        if 'debug' in event.content:
            self.client.api.channels_messages_create(event.channel_id, '```json\n{}```'.format(json.dumps({
            'ID': event.id,
            'Channel_ID': event.channel_id,
            'Author': event.author.mention,
            'Mentions': [v.mention for v in event.mentions.values()],
            'Nonce': event.nonce,
            'TTS': event.tts,
            'Embeds': [v.to_dict() for v in event.embeds],
            'Attachments': [v.to_dict() for v in event.attachments.values()]}
            , indent=4)))
        if 'getfb' in event.content:
            try:
                urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', event.content)
                bases = [ntpath.basename(v) for v in urls]
                b = [v[v.index('_')+1:] for v in bases if '_' in v]
                b2 = [v[:v.index('_')] for v in b if '_' in v]
                if not len(b2):
                    return
                furl = ['https://www.facebook.com/photo.php?fbid={}'.format(v) for v in b2]
                r = [requests.get(v) for v in furl]
                rr = [v for v in r if v.status_code == 200 and 'actor_id' in v.text]
                f = [v.url for v in r if not v in rr]
                id = [v.text[v.text.index('actor_id')+11:v.text.index('story_id')-3] for v in rr]
                r2 = [requests.get('https://www.facebook.com/{}'.format(v)) for v in id]
                rurl = [v.url for v in r2 if v.status_code == 200]
                if len(rurl):
                    self.client.api.channels_messages_create(event.channel_id, '\n'.join(rurl))
                elif len(id):
                    self.client.api.channels_messages_create(event.channel_id, '\n'.join(['https://www.facebook.com/{}'.format(v) for v in id]))
                if len(f):
                    self.client.api.channels_messages_create(event.channel_id, 'Foto(s) privada(s): {}'.format('\n'.join(f)))
                # self.client.api.channels_messages_create(event.channel_id, '```json\n{}```'.format(json.dumps({
                # 'Urls': urls,
                # 'Bases': bases,
                # 'B': b,
                # 'B2': b2,
                # 'Furl': furl,
                # 'Id': id,
                # 'Rurl': rurl
                # }, indent=4)))
            except Exception as e:
                self.client.api.channels_messages_create(event.channel_id, 'Error: {}'.format(e))            
            

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

    @Plugin.command('editmsg', '<cid:snowflake> <mid:snowflake> <content:str...>', level=50, description='Edita uma mensagem.')
    def on_editmsg_command(self, event, cid, mid, content):
        self.client.api.channels_messages_modify(cid, mid, content)

    @Plugin.command('faketype', '<cid:snowflake>', level=50, description='Manda evento de \'digitando\' para um canal.')
    def on_faketype_command(self, event, cid):
        self.client.api.channels_typing(cid)
        
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

    @Plugin.command('c', '<content:str...>', level=10)
    def on_echo_command(self, event, content):
        event.msg.reply('```\n'+content+'```')
        
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
            