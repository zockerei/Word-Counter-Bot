import logging

import discord


class EmbedBuilder:
    def __init__(
            self,
            thumbnail_url,
            color=discord.Color.dark_embed(),
            title=None

    ):
        EmbedBuilder._embed_logger.debug('Creating default embed')
        self._embed = discord.Embed(
            color=color,
            title=title
        )
        self._embed.set_footer(text='placeholder for highest count')
        self._embed.set_thumbnail(url=thumbnail_url)
    # logging setup
    _embed_logger = logging.getLogger('bot.embed')

    _embed_logger.debug('Embed logger set up')

    def add_description(self, description):
        """add description to embed"""
        EmbedBuilder._embed_logger.debug('Adding description to embed')
        self._embed.description = f'{description}\n'

    def to_dict(self):
        EmbedBuilder._embed_logger.debug('Convert embed to dictionary')
        return self._embed.to_dict()
