from PluginBase import *

class Spam(Plugin, PluginBase):
    @Plugin.command('spam', '<count:int> <content:str...>', level=100)
    def on_spam_command(self, event, count, content):
        for i in range(count):
            self.client.api.channels_typing(event.msg.channel_id)
            event.msg.reply(content)

    @Plugin.command('spamsf', '<count:int> <timesf:int> <content:str...>', level=100)
    def on_spamsf_command(self, event, count, timesf, content):
        msgs = []
        for i in range(count):
            self.client.api.channels_typing(event.msg.channel_id)
            msgs.append(event.msg.reply(content))
        time.sleep(timesf)
        for m in msgs:
            m.delete()

    @Plugin.command('spamc', '<cid:snowflake> <count:int> <content:str...>', level=100)
    def on_spamc_command(self, event, cid, count, content):
        for i in range(count):
            self.client.api.channels_typing(cid)
            self.client.api.channels_messages_create(cid, content)

    @Plugin.command('spamcsf', '<cid:snowflake> <count:int> <timesf:int> <content:str...>', level=100)
    def on_spamcsf_command(self, event, cid, count, timesf, content):
        msgs = []
        for i in range(count):
            self.client.api.channels_typing(cid)
            msgs.append(self.client.api.channels_messages_create(cid, content))
        time.sleep(timesf)
        for m in msgs:
            m.delete()