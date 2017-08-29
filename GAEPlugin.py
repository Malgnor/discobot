import os
from disco.bot import Plugin
from flask import redirect


class GAEPlugin(Plugin):
    @Plugin.command('version', description='Mostra a versão atual do bot.')
    def on_version_command(self, event):
        event.msg.reply(os.getenv('GAE_VERSION', '????????'))

    @Plugin.route('/_ah/health')
    def on_health_check_route(self):
        return 'Ok!'

    @Plugin.route('/join/')
    def on_join_route(self):
        return redirect('https://discordapp.com/oauth2/authorize?client_id=263849390949662720&scope=bot&permissions=2146958463')
