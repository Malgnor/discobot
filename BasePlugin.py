from disco.bot import Bot, Plugin

class BasePlugin():
    @Plugin.command('plugin')
    def on_plugin_command(self, event):
        event.msg.reply(self.name)