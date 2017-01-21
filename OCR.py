# coding=UTF-8

from disco.bot import Bot, Plugin
from PIL import Image, ImageOps, ImageFilter, ImageSequence
from pytesseract import image_to_string as img2str
import requests, io, re, time

def isoData(data): #https://github.com/fiji/Auto_Threshold/blob/master/src/main/java/fiji/threshold/Auto_Threshold.java
    g = 0
    for i in range(1, len(data)):
        if data[i] > 0:
            g = i + 1
            break
        
    while True:
        l = 0
        totl = 0
        for i in range(g):
             totl = totl + data[i]
             l = l + (data[i] * i)
        
        h = 0
        toth = 0
        for i in range(g+1, len(data)):
            toth += data[i]
            h += (data[i]*i)
        
        if totl > 0 and toth > 0:
            l /= totl
            h /= toth
            if g == int(round((l + h) / 2.0)):
                break
        
        g += 1
        if g > len(data)-2:
            return -1

    return g
    
class OCR(Plugin):
    @staticmethod
    def config_cls():
        config = {}
        config['enabled'] = False
        config['uploadProcessedImage'] = False
        config['cache'] = True
        config['processImage'] = True
        config['binarize'] = True
        config['minLevel'] = 10
        config['unsharpMask'] = [2, 150, 5]
        return config

    @Plugin.listen('MessageCreate')
    def on_message_create(self, event):
        if event.author == self.state.me:
            return
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
                    cache = self.storage.plugin.ensure('ocr_cache') if self.config['cache'] else {}
                    m = None
                    enhancedImg = None
                    firstFrame = None
                    othersFrames = []
                    dur = None
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
                                    idx = 0
                                    q = len([i for i in ImageSequence.Iterator(img)])
                                    if not q == 1:
                                        m = ''
                                        dur = img.info['duration'] or 250
                                    for frame in ImageSequence.Iterator(img):
                                        if frame.mode == 'P':
                                            frame = frame.convert('RGBA')
                                        if self.config['processImage']:
                                            if self.config['unsharpMask'][0]:
                                                enhancedImg = frame.filter(ImageFilter.UnsharpMask(self.config['unsharpMask'][0], self.config['unsharpMask'][1], self.config['unsharpMask'][2]))
                                            if self.config['binarize']:
                                                grayScale = ImageOps.grayscale(enhancedImg or frame)
                                                threshold = isoData(grayScale.histogram())
                                                enhancedImg = grayScale.point(lambda pixel: pixel > threshold and 255)
                                        if q == 1:
                                            m = img2str(enhancedImg or frame)
                                        else:
                                            r = img2str(enhancedImg or frame)
                                            if r:
                                                m += '`Frame {}:` {}\n'.format(idx, r)
                                            if idx == 0:
                                                firstFrame = enhancedImg or frame
                                            else:
                                                othersFrames.append(enhancedImg or frame)
                                        idx += 1
                                    cache[url] = m
                            else:
                                cache[url] = m
                    if m:
                        m = '`{}`\n'.format(url)+m
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
                        msg.edit('Falha ao processar imagem.')
                    if self.config['uploadProcessedImage'] and enhancedImg:
                        buffer = io.BytesIO()
                        if firstFrame:
                            firstFrame.save(buffer, 'gif', duration=dur, save_all=True, append_images=othersFrames)
                        else:
                            enhancedImg.save(buffer, 'png')
                        self.client.api.channels_messages_create(event.channel_id, '', attachment=('result.{}'.format('gif' if firstFrame else 'png'), buffer.getvalue()))
                time.sleep(2)
                msg.delete()
            except Exception as e:
                self.client.api.channels_messages_create(event.channel_id, 'Error: {}'.format(e))
                
    @Plugin.command('toggle', level=100, group='OCR', description='Ativa/desativa OCR.')
    def on_ocrtoggle_command(self, event):
        self.config['enabled'] = not self.config['enabled']
        event.msg.reply('OCR foi {}.'.format('ativado' if self.config['enabled'] else 'desativado'))
                
    @Plugin.command('upload', level=100, group='OCR', description='Ativa/desativa o upload da imagem processada.')
    def on_ocrtoggleupload_command(self, event):
        self.config['uploadProcessedImage'] = not self.config['uploadProcessedImage']
        event.msg.reply('Upload da imagem processada foi {}.'.format('ativado' if self.config['uploadProcessedImage'] else 'desativado'))
                
    @Plugin.command('process', level=100, group='OCR', description='Ativa/desativa o processamento de imagens.')
    def on_ocrtoggleprocess_command(self, event):
        self.config['processImage'] = not self.config['processImage']
        event.msg.reply('Processamento de imagens foi {}.'.format('ativado' if self.config['processImage'] else 'desativado'))
                
    @Plugin.command('binarize', level=100, group='OCR', description='Ativa/desativa a binarização de imagens.')
    def on_ocrtogglebinarize_command(self, event):
        self.config['binarize'] = not self.config['binarize']
        event.msg.reply('Binarização de imagens foi {}.'.format('ativado' if self.config['binarize'] else 'desativado'))
                
    @Plugin.command('cache', level=100, group='OCR', description='Ativa/desativa o uso do cache.')
    def on_ocrtogglecache_command(self, event):
        self.config['cache'] = not self.config['cache']
        event.msg.reply('O uso do cache foi {}.'.format('ativado' if self.config['cache'] else 'desativado'))
                
    @Plugin.command('status', level=10, group='OCR', description='Status atual do OCR.')
    def on_ocrstatus_command(self, event):
        event.msg.reply('OCR está {} no momento.'.format('ativado' if self.config['enabled'] else 'desativado'))
                
    @Plugin.command('clearCache', level=100, group='OCR', description='Limpa o cache de resultados do OCR.')
    def on_ocrclearcache_command(self, event):
        cache = self.storage.plugin.ensure('ocr_cache')
        for key in cache.keys():
            del cache[key]
        event.msg.reply(':-1:' if len(cache) else ':+1:')
        
    @Plugin.command('level', '[lvl:int]', level=100, group='OCR', description='Altera o nível de permissão mínimo para usar o OCR.')
    def on_ocrlevel_command(self, event, lvl=None):
        if lvl:
            self.config['minLevel'] = lvl
            event.msg.reply('Nível mínimo alterado para {}.'.format(lvl))
        else:
            event.msg.reply('Nível mínimo atual: {}.'.format(self.config['minLevel']))
        
    @Plugin.command('unsharpMask', '<radius:int> <percent:int> <threshold:int>', level=100, group='OCR', description='Altera os parâmetros do UnsharpMask aplicado na imagem.')
    def on_ocrsharpness_command(self, event, radius, percent, threshold):
        self.config['unsharpMask'] = [radius, percent, threshold]
        event.msg.reply('Parâmetros do UnsharpMask alterados para ({}, {}, {}).'.format(radius, percent, threshold))
            