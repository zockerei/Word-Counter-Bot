import logging
import discord


class Embed:
    def __init__(
            self,
            thumbnail_url,
            color=discord.Color.dark_embed(),
            title=None
    ):
        Embed._embed_logger.debug('Creating default embed')
        self._embed = discord.Embed(
            color=color,
            title=title,
        )
        if thumbnail_url is not None:
            self._embed.set_thumbnail(url=thumbnail_url)

    # logging setup
    _embed_logger = logging.getLogger('bot.embed')
    _embed_logger.debug('Embed logger set up')

    def add_description(self, description):
        """Add description to embed."""
        Embed._embed_logger.debug('Adding description to embed')
        self._embed.description = f'{description}\n'
        return self

    def add_footer(self, footer):
        """Add footer to embed."""
        Embed._embed_logger.debug('Adding footer to embed')
        self._embed.set_footer(text=f'{footer}')
        return self

    def to_dict(self):
        Embed._embed_logger.debug('Convert embed to dictionary')
        return self._embed.to_dict()
