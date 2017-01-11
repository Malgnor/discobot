from PluginBase import *

def getCopyPastas():
    if not os.path.isfile('copypastas.json'):
        print 'copypastas.json não encontrado.'
        return {}
    with open('copypastas.json', 'r') as file:
        copypastas = json.load(file)
    return copypastas
    
def saveCopyPastas(copypastas):
    with open('copypastas.json', 'w') as file:
        file.write(json.dumps(copypastas, indent=4, ensure_ascii=False))
        
copypastas = getCopyPastas()

class CopyPasta(Plugin, PluginBase):
    @staticmethod
    def config_cls():
        config = {}
        config['autosave'] = True
        return config
            
    @Plugin.command('copypastaAdd', '<name:str> <copypasta:str...>', level=10)
    def on_copypastaAdd_command(self, event, name, copypasta):
        if name in copypastas:
            event.msg.reply('"' + name + '" já existente.\nUse "copypastaMod" para modificar um copypasta existente.')
        else:
            copypastas[name] = [copypasta, AttachmentToEmbed(event.msg.attachments)]
            event.msg.reply('"' + name + '" adicionado.')
            if self.config['autosave']:
                saveCopyPastas(copypastas)
        
    @Plugin.command('copypastaMod', '<name:str> <copypasta:str...>', level=10)
    def on_copypastaMod_command(self, event, name, copypasta):
        if not name in copypastas:
            event.msg.reply('"' + name + '" inexistente.\nUse "copypastaAdd" para adicionar um novo copypasta.')
        else:
            copypastas[name] = [copypasta, AttachmentToEmbed(event.msg.attachments)]
            event.msg.reply('"' + name + '" modificado.')
            if self.config['autosave']:
                saveCopyPastas(copypastas)
        
    @Plugin.command('copypastaDel', '<name:str>', level=10)
    def on_copypastaDel_command(self, event, name):
        if not name in copypastas:
            event.msg.reply('"' + name + '" inexistente.')
        else:
            del copypastas[name]
            event.msg.reply('"' + name + '" apagado.')
            if self.config['autosave']:
                saveCopyPastas(copypastas)
        
    @Plugin.command('copypastaRename', '<oldname:str> <newname:str>', level=10)
    def on_copypastaRename_command(self, event, oldname, newname):
        if not oldname in copypastas:
            event.msg.reply('"' + oldname + '" inexistente.')
        else:
            copypastas[newname] = copypastas[oldname]
            del copypastas[oldname]
            event.msg.reply('"' + oldname + '" renomeado para "'+ newname + '".')
            if self.config['autosave']:
                saveCopyPastas(copypastas)

    @Plugin.command('copypasta', '[copypasta:str]', level=10)
    def on_copypasta_command(self, event, copypasta=None):
        if copypasta:
            if copypasta in copypastas:
                event.msg.reply(copypastas[copypasta][0], embed=copypastas[copypasta][1])
            else:
                event.msg.reply('"' + copypasta + '" não encontrado.')
        else:
            keys = copypastas.keys()
            if len(keys):
                k = keys[random.randrange(len(keys))]
                event.msg.reply(copypastas[k][0], embed=copypastas[k][1])
            else:
                event.msg.reply("Não há copypastas salvos.")

    @Plugin.command('copypastaSpam', '<quantity:int>', level=50)
    def on_copypastaSpam_command(self, event, quantity):
        keys = copypastas.keys()
        if len(keys):
            for i in range(quantity):
                k = keys[random.randrange(len(keys))]
                event.msg.reply(copypastas[k][0], embed=copypastas[k][1])
        else:
            event.msg.reply("Não há copypastas salvos.")

    @Plugin.command('copypastaList', level=10)
    def on_copypastaList_command(self, event):
        keys = copypastas.keys()
        if len(keys):
            res = '```\n'
            for k in keys:
                res += k+'\n'
            res += '```'
            event.msg.reply(res)
        else:
            event.msg.reply("Não há copypastas salvos.")

    @Plugin.command('copypastaAll', level=50)
    def on_copypastaAll_command(self, event):
        keys = copypastas.keys()
        if len(keys):
            for k in keys:
                event.msg.reply(copypastas[k][0], embed=copypastas[k][1])
        else:
            event.msg.reply("Não há copypastas salvos.")