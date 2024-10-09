import logging
import discord
from discord import Asset


class Embed:
    def __init__(
            self,
            thumbnail_url: Asset,
            color: discord.Color = discord.Color.dark_embed(),
            title: str = None
    ) -> None:
        """
        Initialize Embed object.

        Parameters:
            thumbnail_url (str): The URL for the thumbnail.
            color (discord.Color, optional): The color for the embed. Defaults to discord.Color.dark_embed().
            title (str, optional): The title for the embed. Defaults to None.
        """
        Embed._embed_logger.debug('Creating default embed')
        self._embed = discord.Embed(
            color=color,
            title=title,
        )
        if thumbnail_url is not None:
            self._embed.set_thumbnail(url=thumbnail_url)

    # logging setup
    _embed_logger = logging.getLogger('bot.embed')
    _embed_logger.info('Embed logger set up')

    def add_description(self, description: str) -> 'Embed':
        """
        Add description to embed.

        Parameters:
            description (str): The description to add to the embed.

        Returns:
            Embed: The Embed object with the description added.
        """
        Embed._embed_logger.debug('Adding description to embed')
        self._embed.description = f'{description}\n'
        return self

    def add_footer(self, footer: str) -> 'Embed':
        """
        Add footer to embed.

        Parameters:
            footer (str): The footer text to add to the embed.

        Returns:
            Embed: The Embed object with the footer added.
        """
        Embed._embed_logger.debug('Adding footer to embed')
        self._embed.set_footer(text=f'{footer}')
        return self

    def to_dict(self) -> dict:
        """
        Convert embed to dictionary.

        Returns:
            dict: The dictionary representation of the embed.
        """
        Embed._embed_logger.debug('Convert embed to dictionary')
        return self._embed.to_dict()
