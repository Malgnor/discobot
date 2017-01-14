from disco.types.message import MessageEmbed
from disco.util.serializer import Serializer
import os

def AttachmentToEmbed(attachments):
    embed = None
    if len(attachments):
        for attachment in attachments.values():
            embed = MessageEmbed(title = attachment.filename, url = attachment.url)
            embed.set_image(url = attachment.url, proxy_url = attachment.proxy_url, width = attachment.width, height = attachment.height) if attachment.width else None
            break
    return embed
    
def EmbedImageFromUrl(iurl):
    if not iurl:
        return None
    embed = MessageEmbed(url = iurl)
    embed.set_image(url = iurl)
    return embed

def savePluginConfig(bot, plugin, fmt=None):    
    fmt = fmt or bot.config.plugin_config_format
    name = plugin.name
    if name.endswith('plugin'):
        name = name[:-6]

    path = os.path.join(
        bot.config.plugin_config_dir, name) + '.' + fmt

    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    
    with open(path, 'w') as file:
        file.write(Serializer.dumps(fmt, plugin.config))
    
def loadPluginConfig(bot, plugin, fmt=None):
    fmt = fmt or bot.config.plugin_config_format
    name = plugin.name.lower()
    if name.endswith('plugin'):
        name = name[:-6]

    path = os.path.join(
        bot.config.plugin_config_dir, name) + '.' + fmt

    if not os.path.exists(path):
        if hasattr(plugin, 'config_plugin'):
            return plugin.config_plugin()
        return None

    with open(path, 'r') as file:
        data = Serializer.loads(fmt, file.read())

    if hasattr(plugin, 'config_plugin'):
        inst = plugin.config_plugin()
        inst.update(data)
        return inst

    return data
    