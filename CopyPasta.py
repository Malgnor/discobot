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

class CopyPasta(Plugin):
    @staticmethod
    def config_cls():
        config = {}
        config['autosave'] = True
        return config
            
    @Plugin.command('add', '<name:str> <copypasta:str...>', group='copypasta', level=10, description='Adiciona um copypasta.')
    def on_copypastaAdd_command(self, event, name, copypasta):
        if name in copypastas:
            event.msg.reply('"' + name + '" já existente.\nUse "copypastaMod" para modificar um copypasta existente.')
        else:
            copypastas[name] = [copypasta, AttachmentToEmbed(event.msg.attachments)]
            event.msg.reply('"' + name + '" adicionado.')
            if self.config['autosave']:
                saveCopyPastas(copypastas)
        
    @Plugin.command('mod', '<name:str> <copypasta:str...>', group='copypasta', level=10, description='Modifica um copypasta')
    def on_copypastaMod_command(self, event, name, copypasta):
        if not name in copypastas:
            event.msg.reply('"' + name + '" inexistente.\nUse "copypastaAdd" para adicionar um novo copypasta.')
        else:
            copypastas[name] = [copypasta, AttachmentToEmbed(event.msg.attachments)]
            event.msg.reply('"' + name + '" modificado.')
            if self.config['autosave']:
                saveCopyPastas(copypastas)
        
    @Plugin.command('del', '<name:str>', group='copypasta', level=10, description='Remove um copypasta.')
    def on_copypastaDel_command(self, event, name):
        if not name in copypastas:
            event.msg.reply('"' + name + '" inexistente.')
        else:
            del copypastas[name]
            event.msg.reply('"' + name + '" apagado.')
            if self.config['autosave']:
                saveCopyPastas(copypastas)
        
    @Plugin.command('rename', '<oldname:str> <newname:str>', group='copypasta', level=10, description='Renomeia um copypasta.')
    def on_copypastaRename_command(self, event, oldname, newname):
        if not oldname in copypastas:
            event.msg.reply('"' + oldname + '" inexistente.')
        else:
            copypastas[newname] = copypastas[oldname]
            del copypastas[oldname]
            event.msg.reply('"' + oldname + '" renomeado para "'+ newname + '".')
            if self.config['autosave']:
                saveCopyPastas(copypastas)

    @Plugin.command('view', '[copypasta:str]', group='copypasta', level=10, description='Mostra um copypasta.')
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

    @Plugin.command('spam', '<quantity:int>', group='copypasta', level=50, description='Spamma copypastas.')
    def on_copypastaSpam_command(self, event, quantity):
        keys = copypastas.keys()
        if len(keys):
            for i in range(quantity):
                k = keys[random.randrange(len(keys))]
                event.msg.reply(copypastas[k][0], embed=copypastas[k][1])
        else:
            event.msg.reply("Não há copypastas salvos.")

    @Plugin.command('list', group='copypasta', level=10, description='Mostra uma lista com todos os copypastas.')
    def on_copypastaList_command(self, event):
        keys = copypastas.keys()
        if len(keys):
            res = '```markdown\n'
            for k in keys:
                res += '* {}\n'.format(k)
            res += '```'
            event.msg.reply(res)
        else:
            event.msg.reply("Não há copypastas salvos.")

    @Plugin.command('all', group='copypasta', level=50, description='Spamma todos os copypastas.')
    def on_copypastaAll_command(self, event):
        keys = copypastas.keys()
        if len(keys):
            for k in keys:
                event.msg.reply(copypastas[k][0], embed=copypastas[k][1])
        else:
            event.msg.reply("Não há copypastas salvos.")