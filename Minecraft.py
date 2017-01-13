from PluginBase import *
import socket

def isOnline(address, port):
    s = socket.socket()
    s.settimeout(2)
    try:
        s.connect((address, port))
        s.close()
        return True
    except socket.error, e:
        return False
    
class Minecraft(Plugin, PluginBase):
    @staticmethod
    def config_cls():
        config = {}
        config['window_title'] = '"Minecraft Server"'
        config['server_ip'] = '127.0.0.1'
        config['server_port'] = 25565
        config['server_path'] = ''
        config['server_file'] = 'spigot.jar'
        config['server_mem'] = 1024
        config['server_laststart'] = time.time()
        return config
        
    @Plugin.command('start', group='minecraft', level=50, description='Inicializa o servidor.')
    def on_start_command(self, event):
        self.client.api.channels_typing(event.msg.channel_id)
        
        if isOnline('localhost', self.config['server_port']):
            event.msg.reply('{}:{} já está online.'.format(self.config['server_ip'], self.config['server_port']))
            return
        
        if self.config['server_laststart']+60 > time.time():
            event.msg.reply('Espere um minuto e tente novamente.')
            return
            
        self.config['server_laststart'] = time.time()
        cmd = 'start {} /d {} /min "java" -Xmx{}M -jar {} -o true'.format(self.config['window_title'], self.config['server_path'], self.config['server_mem'], self.config['server_file'])
        os.system(cmd)
        event.msg.reply('Inicializando servidor! IP: {}:{}'.format(self.config['server_ip'], self.config['server_port']))

    @Plugin.command('check', '[ip:str] [port:int]', group='minecraft', level=10, description='Verifica se uma porta em um ip está acessível.')
    def on_check_command(self, event, ip='127.0.0.1', port=25565):
        self.client.api.channels_typing(event.msg.channel_id)
        host = ip
        if ip == self.config['server_ip']:
            host = 'localhost'
        if isOnline(host, port):
            event.msg.reply('{}:{} está online.'.format(ip, port))
        else:
            event.msg.reply('{}:{} não está online.'.format(ip, port))