from PluginBase import *

class Master(Plugin, PluginBase):
    @staticmethod
    def config_cls():
        config = {}
        config['ownersid'] = []
        config['channelLogId'] = 1
        config['apikey'] = ''
        config['copyCatId'] = []
        return config

    @Plugin.listen('Ready')
    def on_ready(self, event):
        self.client.api.channels_messages_create(self.config['channelLogId'], 'I am ready!\nDisco-py: {}'.format(disco.VERSION))

    @Plugin.listen('GuildCreate')
    def on_guild_create(self, event):
        if event.created:
            self.client.api.channels_messages_create(self.config['channelLogId'], 'Entrei no servidor: {}'.format(event.name))

    @Plugin.listen('GuildDelete')
    def on_guild_delete(self, event):
        if event.deleted:
            self.client.api.channels_messages_create(self.config['channelLogId'], 'Saindo do servidor: {}'.format(event.id))

    @Plugin.listen('MessageCreate')
    def on_message_create(self, event):
        if event.author.id in self.config['copyCatId']:
            e = None
            if len(event.attachments):
                for k in event.attachments.keys():
                    e = MessageEmbed(title = event.attachments[k].filename, url = event.attachments[k].url)
                    e.image = MessageEmbedImage(url = event.attachments[k].url, proxy_url = event.attachments[k].proxy_url, width = event.attachments[k].width, height = event.attachments[k].height) if event.attachments[k].width else None
                    break
            self.client.api.channels_messages_create(event.channel_id, event.content, event.nonce, event.tts, None, e)            

    @Plugin.listen('TypingStart')
    def on_typing_start(self, event):
        if event.user_id in self.config['copyCatId']:
            self.client.api.channels_typing(event.channel_id)
        
    @Plugin.command('updatePresence', '<status:str> [game:str...]')
    def on_updatepresence_command(self, event, status, game=None):
        if event.msg.author.id in self.config['ownersid']:
            if not Status[status]:
                status = 'ONLINE'
            self.client.update_presence(Game(name=game), Status[status])
            event.msg.reply('Atualizando status...')
        else:
            event.msg.reply('Você não pode usar esse comando.')
        
    @Plugin.command('setCopyCat', '[target:snowflake]')
    def on_setcopycat_command(self, event, target=None):
        if event.msg.author.id in self.config['ownersid']:
            if not target:
                r = '' if len(self.config['copyCatId']) else 'Não há alvos.'
                
                for t in self.config['copyCatId']:
                    r += '<@{}>\n'.format(t)
                    
                event.msg.reply(r)
                return
                
            if target == 1:
                target = event.msg.author.id
                
            if target in self.config['copyCatId']:
                self.config['copyCatId'].remove(target)
                event.msg.reply('<@{}> removido como alvo.'.format(target))
            else:
                self.config['copyCatId'].append(target)
                event.msg.reply('<@{}> adicionado como alvo.'.format(target))
        else:
            event.msg.reply('Você não pode usar esse comando.')
        
    @Plugin.command('quit')
    def on_quit_command(self, event):
        if event.msg.author.id in self.config['ownersid']:
            event.msg.reply('Bye!')
            self.log.info('Calling quit().')
            quit()
        else:
            event.msg.reply('Você não pode usar esse comando.')
        
    @Plugin.command('name','<name:str...>')
    def on_name_command(self, event, name):
        self.client.api.channels_typing(event.msg.channel_id)
        result = requests.get('https://br.api.pvp.net/api/lol/br/v1.4/summoner/by-name/{}'.format(name), params={'api_key':self.config['apikey']})
        event.msg.reply('```\n'+json.dumps(json.loads(result.text), indent=4, ensure_ascii=False)+'\n```')

    @Plugin.command('spam', '<count:int> <content:str...>')
    def on_spam_command(self, event, count, content):
        if event.msg.author.id in self.config['ownersid']:
            for i in range(count):
                self.client.api.channels_typing(event.msg.channel_id)
                event.msg.reply(content)
        else:
            event.msg.reply('Você não pode usar esse comando.')

    @Plugin.command('spamsf', '<count:int> <timesf:int> <content:str...>')
    def on_spamsf_command(self, event, count, timesf, content):
        if event.msg.author.id in self.config['ownersid']:
            msgs = []
            for i in range(count):
                self.client.api.channels_typing(event.msg.channel_id)
                msgs.append(event.msg.reply(content))
            time.sleep(timesf)
            for m in msgs:
                m.delete()
        else:
            event.msg.reply('Você não pode usar esse comando.')

    @Plugin.command('spamc', '<cid:snowflake> <count:int> <content:str...>')
    def on_spamc_command(self, event, cid, count, content):
        if event.msg.author.id in self.config['ownersid']:
            for i in range(count):
                self.client.api.channels_typing(cid)
                self.client.api.channels_messages_create(cid, content)
        else:
            event.msg.reply('Você não pode usar esse comando.')

    @Plugin.command('spamcsf', '<cid:snowflake> <count:int> <timesf:int> <content:str...>')
    def on_spamcsf_command(self, event, cid, count, timesf, content):
        if event.msg.author.id in self.config['ownersid']:
            msgs = []
            for i in range(count):
                self.client.api.channels_typing(cid)
                msgs.append(self.client.api.channels_messages_create(cid, content))
            time.sleep(timesf)
            for m in msgs:
                m.delete()
        else:
            event.msg.reply('Você não pode usar esse comando.')

    @Plugin.command('saychannel', '<cid:snowflake> <content:str...>')
    def on_saychannel_command(self, event, cid, content):
        self.client.api.channels_messages_create(cid, content)

    @Plugin.command('faketype', '<cid:snowflake>')
    def on_faketype_command(self, event, cid):
        self.client.api.channels_typing(cid)
    
    @Plugin.command('info', '<query:str...>')
    def on_info(self, event, query):
    
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
                parts.append('Nickname: {}'.format(member.nick))
                parts.append('Joined At: {}'.format(member.joined_at))
                
            event.msg.reply(('```\n{}\n```'.format(
                '\n'.join(parts))
            )+(user.avatar_url or ''))
