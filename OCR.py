# coding=UTF-8

from disco.bot import Bot, Plugin
from PIL import Image
from pytesseract import image_to_string as img2str
import requests, io, re, time

class OCR(Plugin):
    @staticmethod
    def config_cls():
        config = {}
        config['enabled'] = False
        config['minLevel'] = 10
        return config

    @Plugin.listen('MessageCreate')
    def on_message_create(self, event):
        if self.config['enabled'] and 'ocr' in event.content:
            if self.config['minLevel'] > self.bot.get_level(event.author if not event.guild else event.guild.get_member(event.author)):
                self.client.api.channels_messages_create(event.channel_id, '{} não possui permissão para usar essa funcionalidade.'.format(event.author.mention))
                return
            try:
                urls = set()
                msg = self.client.api.channels_messages_create(event.channel_id, 'Procurando imagens na mensagem.')
                for a in event.attachments.values():
                    if a.width:
                        urls.add(a.url)
                for e in event.embeds:
                    if e.type == 'image':
                        urls.add(e.image.url)
                        urls.add(e.thumbnail.url)
                reurls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', event.content)
                for u in reurls:
                    urls.add(u)
                urls = set(u for u in urls if isinstance(u, (unicode, str)))
                for url in urls:
                    if '<' in url:
                        idx = url.index('<')
                        url = url[:idx]+url[idx+1:]
                    if '>' in url:
                        idx = url.index('>')
                        url = url[:idx]+url[idx+1:]
                    cache = self.storage.plugin.ensure('ocr_cache')
                    m = None
                    if url in cache:
                        msg.edit('Encontrado processamento anterior em cache.')
                        m = cache[url]
                    else:
                        msg.edit('Processando imagem.')
                        r = requests.get(url)
                        if r.status_code == 200:
                            if 'image' in r.headers['Content-Type']:
                                with Image.open(io.BytesIO(r.content)) as img:
                                    img.load()
                                    m = img2str(img)
                                    cache[url] = m
                            else:
                                cache[url] = m
                    if m:
                        m = '`{}`\n'.format(url)+m
                        if len(m) > 2000:
                            msg.edit('Resultado acima do limite de caracteres para uma mensagem.')
                            while len(m) > 2000:
                                if '\n' in m[2000::-1]:
                                    i = m[2000::-1].index('\n')                                
                                    self.client.api.channels_messages_create(event.channel_id, m[:2000-i])
                                    m = m[2000-i+1:]
                                else:
                                    self.client.api.channels_messages_create(event.channel_id, m[:2000])
                                    m = m[2000:]
                            self.client.api.channels_messages_create(event.channel_id, m)
                        else:
                            self.client.api.channels_messages_create(event.channel_id, m)
                    else:
                        msg.edit('Falha ao processar imagem.')
                else:
                    msg.edit('Nenhuma imagem encontrada mensagem.')
                time.sleep(2)
                msg.delete()
            except Exception as e:
                self.client.api.channels_messages_create(event.channel_id, 'Error: {}'.format(e))
                
    @Plugin.command('toggle', level=100, group='OCR', description='Ativa/desativa OCR.')
    def on_ocrtoggle_command(self, event):
        self.config['enabled'] = not self.config['enabled']
        event.msg.reply('OCR foi {}.'.format('ativado' if self.config['enabled'] else 'desativado'))
                
    @Plugin.command('status', level=10, group='OCR', description='Status atual do OCR.')
    def on_ocrstatus_command(self, event):
        event.msg.reply('OCR está {} no momento.'.format('ativado' if self.config['enabled'] else 'desativado'))
                
    @Plugin.command('level', '[lvl:int]', level=100, group='OCR', description='Altera o nível de permissão mínimo para usar o OCR.')
    def on_ocrlevel_command(self, event, lvl=None):
        if lvl:
            self.config['minLevel'] = lvl
            event.msg.reply('Nível mínimo alterado para {}.'.format(lvl))
        else:
            event.msg.reply('Nível mínimo atual: {}.'.format(self.config['minLevel']))            
