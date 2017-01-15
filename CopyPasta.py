# coding=UTF-8

from disco.bot import Bot, Plugin
from Utils import AttachmentToEmbed
import random

class CopyPasta(Plugin):
    def __init__(self, bot, config):
        super(CopyPasta, self).__init__(bot, config)
        self.init = True
        
    @property
    def copypastas(self):
        if self.init:
            return self.storage.plugin.ensure('copypastas')
        return None
        
    @Plugin.command('add', '<name:str> <copypasta:str...>', group='copypasta', level=10, description='Adiciona um copypasta.')
    def on_copypastaAdd_command(self, event, name, copypasta):
        if name in self.copypastas:
            event.msg.reply('"' + name + '" já existente.\nUse "copypastaMod" para modificar um copypasta existente.')
        else:
            self.copypastas[name] = [copypasta, AttachmentToEmbed(event.msg.attachments)]
            event.msg.reply('"' + name + '" adicionado.')
        
    @Plugin.command('mod', '<name:str> <copypasta:str...>', group='copypasta', level=10, description='Modifica um copypasta')
    def on_copypastaMod_command(self, event, name, copypasta):
        if not name in self.copypastas:
            event.msg.reply('"' + name + '" inexistente.\nUse "copypastaAdd" para adicionar um novo copypasta.')
        else:
            self.copypastas[name] = [copypasta, AttachmentToEmbed(event.msg.attachments)]
            event.msg.reply('"' + name + '" modificado.')
        
    @Plugin.command('del', '<name:str>', group='copypasta', level=10, description='Remove um copypasta.')
    def on_copypastaDel_command(self, event, name):
        if not name in self.copypastas:
            event.msg.reply('"' + name + '" inexistente.')
        else:
            del self.copypastas[name]
            event.msg.reply('"' + name + '" apagado.')
        
    @Plugin.command('rename', '<oldname:str> <newname:str>', group='copypasta', level=10, description='Renomeia um copypasta.')
    def on_copypastaRename_command(self, event, oldname, newname):
        if not oldname in self.copypastas:
            event.msg.reply('"' + oldname + '" inexistente.')
        else:
            self.copypastas[newname] = self.copypastas[oldname]
            del self.copypastas[oldname]
            event.msg.reply('"' + oldname + '" renomeado para "'+ newname + '".')

    @Plugin.command('view', '[copypasta:str]', group='copypasta', level=10, description='Mostra um copypasta.')
    def on_copypasta_command(self, event, copypasta=None):
        if copypasta:
            if copypasta in self.copypastas:
                event.msg.reply(self.copypastas[copypasta][0], embed=self.copypastas[copypasta][1])
            else:
                event.msg.reply('"' + copypasta + '" não encontrado.')
        else:
            if len(self.copypastas):
                k = list(self.copypastas.keys())[random.randrange(len(self.copypastas))]
                event.msg.reply(self.copypastas[k][0], embed=self.copypastas[k][1])
            else:
                event.msg.reply("Não há copypastas salvos.")

    @Plugin.command('spam', '<quantity:int>', group='copypasta', level=50, description='Spamma copypastas.')
    def on_copypastaSpam_command(self, event, quantity):
        if len(self.copypastas):
            for i in range(quantity):
                k = list(self.copypastas.keys())[random.randrange(len(self.copypastas))]
                event.msg.reply(self.copypastas[k][0], embed=self.copypastas[k][1])
        else:
            event.msg.reply("Não há copypastas salvos.")

    @Plugin.command('list', group='copypasta', level=10, description='Mostra uma lista com todos os copypastas.')
    def on_copypastaList_command(self, event):
        if len(self.copypastas):
            res = '```markdown\n'
            for k in self.copypastas.keys():
                res += '* '+k+'\n'
            res += '```'
            event.msg.reply(res)
        else:
            event.msg.reply("Não há copypastas salvos.")

    @Plugin.command('all', group='copypasta', level=50, description='Spamma todos os copypastas.')
    def on_copypastaAll_command(self, event):
        if len(self.copypastas):
            for k in self.copypastas.keys():
                event.msg.reply(self.copypastas[k][0], embed=self.copypastas[k][1])
        else:
            event.msg.reply("Não há copypastas salvos.")