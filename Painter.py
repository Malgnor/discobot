# coding=UTF-8

from disco.bot import Bot, Plugin
from PIL import Image, ImageOps, ImageFilter, ImageSequence, ImageDraw, ImageFont
from PIL.ImageColor import getrgb
import io, os, re
  
class Painter(Plugin):
    def __init__(self, bot, config):
        super(Painter, self).__init__(bot, config)
        if not os.path.exists('Fonts'+os.path.sep):
            os.makedirs(os.path.dirname('Fonts'+os.path.sep))
        fonts = os.listdir('Fonts')
        self.fonts = [os.path.splitext(font) for font in fonts]
        self.init = True
        
    @property
    def userCtx(self):
        if self.init:
            return self.storage.plugin.ensure('user')
        return None
        
    @property
    def channelCtx(self):
        if self.init:
            return self.storage.plugin.ensure('channel')
        return None

    @Plugin.listen('MessageCreate')
    def on_message_create(self, event):
        if event.author == self.state.me:
            return
        ctxUser = self.userCtx.ensure(event.author.id)
        ctxChannel = self.channelCtx.ensure(event.channel_id)
        cfg = None
        if ctxUser.get('autotext', False):
            cfg = ctxUser.get('text', ['Fonts/arial.ttf', 64, 'white', 'rgba(0,0,0,0)'])
        elif ctxChannel.get('autotext', False):
            cfg = ctxChannel.get('text', ['Fonts/arial.ttf', 64, 'white', 'rgba(0,0,0,0)'])
        if cfg:
            try:
                if not event.channel.type == 1:
                    event.delete()
                txt = event.with_proper_mentions
                img = Image.new('RGBA', (1, 1), getrgb('white'))
                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype(cfg[0], cfg[1])
                tsize = draw.textsize(txt, font)
                img = Image.new('RGBA', (tsize[0]+10, tsize[1]+10), getrgb(cfg[3]))
                draw = ImageDraw.Draw(img)
                draw.text((5, 5), txt, cfg[2], font)
                del font
                del draw
                buffer = io.BytesIO()
                img.save(buffer, 'png')
                reurls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', event.content)
                self.client.api.channels_messages_create(event.channel_id, '[{}]:\n{}'.format(event.author, '\n'.join(reurls)), attachment=('text.png', buffer.getvalue()))
            except Exception as e:
                self.client.api.channels_messages_create(event.channel_id, '[ERRO]{}'.format(e))
                
    @Plugin.command('draw', level=10, group='Paint', description='Desenha uma imagem.')
    def on_painterdraw_command(self, event):
        self.client.api.channels_typing(event.msg.channel_id)
        ctx = self.userCtx.ensure(event.msg.author.id)
        try:
            img = Image.new('RGBA', (ctx.get('width', 100), ctx.get('height', 100)), getrgb(ctx.get('bgColor', 'rgba(0,0,0,0)')))
            draw = ImageDraw.Draw(img)
            for text in ctx.get('texts', []):
                font = ImageFont.truetype(text[3], text[4])
                draw.text((text[0], text[1]), text[5], font=font, fill=text[2])
                del font
            del draw
            buffer = io.BytesIO()
            img.save(buffer, 'png')
            event.msg.reply('', attachment=('draw.png', buffer.getvalue()))
        except Exception as e:
            event.msg.reply('[ERRO]{}'.format(e))
        
    @Plugin.command('sendDraw', '<channelID:snowflake>', level=10, group='Paint', description='Desenha uma imagem em um canal específico.')
    def on_paintersenddraw_command(self, event, channelID):
        self.client.api.channels_typing(channelID)
        ctx = self.userCtx.ensure(event.msg.author.id)
        try:
            img = Image.new('RGBA', (ctx.get('width', 100), ctx.get('height', 100)), getrgb(ctx.get('bgColor', 'rgba(0,0,0,0)')))
            draw = ImageDraw.Draw(img)
            for text in ctx.get('texts', []):
                font = ImageFont.truetype(text[3], text[4])
                draw.text((text[0], text[1]), text[5], font=font, fill=text[2])
                del font
            del draw
            buffer = io.BytesIO()
            img.save(buffer, 'png')
            self.client.api.channels_messages_create(channelID, '', attachment=('draw.png', buffer.getvalue()))
        except Exception as e:
            event.msg.reply('[ERRO]{}'.format(e))
        
    @Plugin.command('size', '<width:int> <height:int>', level=10, group='Paint', description='Altera o tamanha da imagem.')
    def on_paintersize_command(self, event, width, height):
        ctx = self.userCtx.ensure(event.msg.author.id)
        ctx.update({'width': width, 'height': height})
        c = {}
        c.update(ctx)
        c.pop('texts', None)
        event.msg.reply('`{}`'.format(c))
        
    @Plugin.command('background', '<color:str...>', level=10, group='Paint', description='Altera a cor do funda da imagem.')
    def on_painterbackground_command(self, event, color):
        ctx = self.userCtx.ensure(event.msg.author.id)
        ctx.update({'bgColor': color})
        c = {}
        c.update(ctx)
        c.pop('texts', None)
        event.msg.reply('`{}`'.format(c))
        
    @Plugin.command('text add', '<x:int> <y:int> <color:str> <font:str> <size:int> <text:str...>', level=10, group='Paint', description='Adiciona texto na imagem.')
    def on_paintertextadd_command(self, event, x, y, color, font, size, text):
        try:
            font = [f[0]+f[1] for f in self.fonts if font.lower() in ''.join(f[0].lower().split(' '))]
            if len(font) == 0:
                event.msg.reply('Fonte desconhecida.')
                return
            font = 'Fonts'+os.path.sep+font[0]
            fnt = ImageFont.truetype(font, size)
            ctx = self.userCtx.ensure(event.msg.author.id)
            texts = ctx.get('texts', [])
            texts.append([x, y, color, font, size, text])
            ctx.update({'texts': texts})
            draw = ImageDraw.Draw(Image.new('RGB', (1, 1), getrgb('white')))
            tsize = draw.textsize(text, fnt)
            event.msg.reply('Tamanho do texto em pixels: `{}`\nTamanho recomendado para a imagem: `{}`'.format(tsize, (x+tsize[0], y+tsize[1])))
            del fnt
            del draw
        except Exception as e:
            event.msg.reply('[ERRO]{}'.format(e))
        
    @Plugin.command('text clear', level=10, group='Paint', description='Remove todos os textos da imagem.')
    def on_paintertextclear_command(self, event):
        ctx = self.userCtx.ensure(event.msg.author.id)
        ctx.update({'texts': []})
        c = {}
        c.update(ctx)
        c.pop('texts', None)
        event.msg.reply('`{}`'.format(c))
        
    @Plugin.command('text config', '<bgColor:str> <fontColor:str> <font:str> <size:int>', level=10, group='Paint', description='Configuração do texto para uso em outros comandos.')
    def on_paintertextconfig_command(self, event, bgColor, fontColor, font, size):
        try:
            font = [f[0]+f[1] for f in self.fonts if font.lower() in ''.join(f[0].lower().split(' '))]
            if len(font) == 0:
                event.msg.reply('Fonte desconhecida.')
                return
            font = 'Fonts'+os.path.sep+font[0]
            cfg = [font, size, fontColor, bgColor]
            ctx = self.userCtx.ensure(event.msg.author.id)
            ctx.update({'text': cfg})
            event.msg.reply('Configuração do texto: `{}`'.format(cfg))
        except Exception as e:
            event.msg.reply('[ERRO]{}'.format(e))
        
    @Plugin.command('text toggle', level=10, group='Paint', description='Ativa/desativa a autosubstituição da mensagem por imagem.')
    def on_paintertexttoggle_command(self, event):
        ctx = self.userCtx.ensure(event.msg.author.id)
        ctx['autotext'] = not ctx.get('autotext', False)
        event.msg.reply('Autosubstituição foi {}.'.format('ativada' if ctx['autotext'] else 'desativada'))
        
    @Plugin.command('text configUser', '<bgColor:str> <fontColor:str> <font:str> <size:int> <userID:snowflake>', level=100, group='Paint', description='Configuração do texto para uso em outros comandos.')
    def on_paintertextconfiguser_command(self, event, bgColor, fontColor, font, size, userID):
        try:
            font = [f[0]+f[1] for f in self.fonts if font.lower() in ''.join(f[0].lower().split(' '))]
            if len(font) == 0:
                event.msg.reply('Fonte desconhecida.')
                return
            font = 'Fonts'+os.path.sep+font[0]
            cfg = [font, size, fontColor, bgColor]
            ctx = self.userCtx.ensure(userID)
            ctx.update({'text': cfg})
            event.msg.reply('Configuração do texto: `{}`'.format(cfg))
        except Exception as e:
            event.msg.reply('[ERRO]{}'.format(e))
        
    @Plugin.command('text toggleUser', '<userID:snowflake>', level=100, group='Paint', description='Ativa/desativa a autosubstituição da mensagem por imagem.')
    def on_paintertexttoggleuser_command(self, event, userID):
        ctx = self.userCtx.ensure(userID)
        ctx['autotext'] = not ctx.get('autotext', False)
        event.msg.reply('Autosubstituição foi {}.'.format('ativada' if ctx['autotext'] else 'desativada'))
        
    @Plugin.command('text configChannel', '<bgColor:str> <fontColor:str> <font:str> <size:int> <channelID:snowflake>', level=100, group='Paint', description='Configuração do texto para uso em outros comandos.')
    def on_paintertextconfigchannel_command(self, event, bgColor, fontColor, font, size, channelID):
        try:
            font = [f[0]+f[1] for f in self.fonts if font.lower() in ''.join(f[0].lower().split(' '))]
            if len(font) == 0:
                event.msg.reply('Fonte desconhecida.')
                return
            font = 'Fonts'+os.path.sep+font[0]
            cfg = [font, size, fontColor, bgColor]
            ctx = self.channelCtx.ensure(channelID)
            ctx.update({'text': cfg})
            event.msg.reply('Configuração do texto: `{}`'.format(cfg))
        except Exception as e:
            event.msg.reply('[ERRO]{}'.format(e))
        
    @Plugin.command('text toggleChannel', '<channelID:snowflake> [content:str...]', level=100, group='Paint', description='Ativa/desativa a autosubstituição da mensagem por imagem.')
    def on_paintertexttogglechannel_command(self, event, channelID, content=None):
        ctx = self.channelCtx.ensure(channelID)
        ctx['autotext'] = not ctx.get('autotext', False)
        event.msg.reply('Autosubstituição foi {}.'.format('ativada' if ctx['autotext'] else 'desativada'))
        if content:
            self.client.api.channels_messages_create(channelID, content)
        
    @Plugin.command('fonts', level=10, group='Paint', description='Lista as fontes de texto disponíveis.')
    def on_painterfonts_command(self, event):
        r = '```markdown\n'
        idx = 1
        for font in self.fonts:
            f = '{}. {}\n'.format(idx, font[0])
            if len(r+f)+3 > 2000:
                r += '```'
                event.msg.reply(r)
                r = '```markdown\n'
            r += f
            idx += 1
        r += '```'
        event.msg.reply(r)
        