# import discord
from django.db import models


# client = discord.Client()


class DiscordBotData(models.Model):

    api_url = 'https://discord.com/api/'

    bot_token = models.CharField(max_length=50)
    chat_id = models.CharField(max_length=16, blank=True, null=True)
