import os
from disco.types.message import MessageEmbed
from disco.util.serializer import Serializer
from disco.bot import BotConfig
from disco.client import ClientConfig


def attachment_to_embed(attachments):
    embed = None
    if len(attachments):
        for attachment in attachments.values():
            embed = MessageEmbed(title=attachment.filename, url=attachment.url)
            if attachment.width:
                embed.set_image(url=attachment.url, proxy_url=attachment.proxy_url,
                                width=attachment.width, height=attachment.height)
            break
    return embed


def embed_image_from_url(iurl):
    if not iurl:
        return None
    embed = MessageEmbed(url=iurl)
    embed.set_image(url=iurl)
    return embed


def save_plugin_config(bot, plugin, fmt=None):
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


def load_plugin_config(bot, plugin, fmt=None):
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


def save_bot_config(bot, path):
    clientKeys = [k for k in ClientConfig.__dict__ if not(
        k.startswith('__') and k.endswith('__'))]
    botKeys = [k for k in BotConfig.__dict__ if not(
        k.startswith('__') and k.endswith('__'))]
    botKeys.append('plugins')

    toSave = {}
    toSave['bot'] = {}
    cc = bot.client.config.to_dict()
    bc = bot.config.to_dict()

    for k in clientKeys:
        toSave[k] = cc[k]
    for k in botKeys:
        toSave['bot'][k] = bc[k]
    for k, v in toSave['bot']['levels'].items():
        toSave['bot']['levels'][k] = str(v)

    _, ext = os.path.splitext(path)
    Serializer.check_format(ext[1:])

    data = Serializer.dumps(ext[1:], toSave)

    with open(path, 'w') as file:
        file.write(data)


def load_bot_config(bot, path):
    if os.path.exists(path):
        bot.client.config = ClientConfig.from_file(path)
    else:
        return False

    bot.config = BotConfig(bot.client.config.bot) if hasattr(
        bot.client.config, 'bot') else BotConfig()
    return True
