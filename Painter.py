# coding=UTF-8

from disco.bot import Bot, Plugin
from PIL import Image, ImageOps, ImageFilter, ImageSequence, ImageDraw, ImageFont
from PIL.ImageColor import getrgb
import io, os
  
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
        
    @Plugin.command('draw', level=10, group='Paint', description='Desenha uma imagem.')
    def on_painterdraw_command(self, event):
        self.client.api.channels_typing(event.msg.channel_id)
        ctx = self.userCtx.ensure(event.msg.author.id)
        try:
            img = Image.new('RGBA', (ctx.get('width', 100), ctx.get('height', 100)), getrgb(ctx.get('bgcolor', 'rgba(0,0,0,0)')))
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
            img = Image.new('RGBA', (ctx.get('width', 100), ctx.get('height', 100)), getrgb(ctx.get('bgcolor', 'rgba(0,0,0,0)')))
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
        ctx.update({'bgcolor': color})
        c = {}
        c.update(ctx)
        c.pop('texts', None)
        event.msg.reply('`{}`'.format(c))
        
    @Plugin.command('text add', '<x:int> <y:int> <color:str> <font:str> <size:int> <text:str...>', level=10, group='Paint', description='Adiciona texto na imagem.')
    def on_paintertextadd_command(self, event, x, y, color, font, size, text):
        try:
            font = [f[0]+f[1] for f in self.fonts if font.lower() in f[0].lower()]
            if len(font) == 0:
                event.msg.reply('Fonte desconhecida.')
                return
            font = 'Fonts'+os.path.sep+font[0]
            fnt = ImageFont.truetype(font, size)
            ctx = self.userCtx.ensure(event.msg.author.id)
            texts = ctx.get('texts', [])
            texts.append([x, y, color, font, size, text])
            ctx.update({'texts': texts})
            tsize = fnt.getsize(text)
            event.msg.reply('Tamanho do texto em pixels: `{}`\nTamanho recomendado para a imagem: `{}`'.format(tsize, (x+tsize[0], y+tsize[1])))
            del fnt
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
        
    @Plugin.command('sample', '[fontColor:str] [bgColor:str] [col:int]', level=10, group='Paint', description='Desenha uma amostra com todas as fontes disponíveis.')
    def on_paintersample_command(self, event, fontColor='black', bgColor='white', col=5):
        self.client.api.channels_typing(event.msg.channel_id)
        try:
            fontsPerCol = int(round(len(self.fonts)/float(col)))
            texts = []
            total = 0
            x = 5
            y = 5
            xMax = x
            yMax = y
            for font in self.fonts:
                total += 1 
                f = ImageFont.truetype(font[0]+font[1], 32)
                t = '{} - ABC123abc!@# - {}'.format(total, font[0])
                ts = f.getsize(t)
                texts.append([(x, y), t, f])
                y += ts[1]+10
                xMax = max(xMax, x+ts[0]+5)
                if total % fontsPerCol == 0:
                    yMax = max(yMax, y)
                    y = 5
                    x = xMax + 5
            img = Image.new('RGBA', (xMax, yMax), getrgb(bgColor))
            draw = ImageDraw.Draw(img)
            for text in texts:
                draw.text(text[0], text[1], fontColor, text[2])
                del text[2]
            del draw
            buffer = io.BytesIO()
            img.save(buffer, 'png')
            event.msg.reply('', attachment=('sample.png', buffer.getvalue()))
        except Exception as e:
            event.msg.reply('[ERRO]{}'.format(e))