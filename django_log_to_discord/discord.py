from discord_webhook import DiscordWebhook, DiscordEmbed


class QueueBot:
    def __init__(self, webhook_url, title='', body=''):
        self.webhook_url = webhook_url
        self.title = title
        self.body = body

    def sendMessage(self, color='03b2f8', *args, **kwargs):
        
        if 'title' in kwargs:
            self.title = kwargs['title']
            del kwargs['title']
        if 'body' in kwargs:
            self.body = kwargs['body']
            del kwargs['body']
        
        webhook = DiscordWebhook(url=self.webhook_url)
        embed = DiscordEmbed(
            title=self.title,
            description=self.body,
            color=color
        )
        embed.set_timestamp()

        for key, value in kwargs.items():
            embed.add_embed_field(name=key, value=value)

        webhook.add_embed(embed)
        response = webhook.execute()
