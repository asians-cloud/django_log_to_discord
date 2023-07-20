import io
import logging
import traceback

from .discord import QueueBot


class DiscordFormatter(logging.Formatter):
    """
    an extension of the usual logging.Formatter to simplify transmitted data
    """
    meta_attrs = [
        'REMOTE_ADDR',
        'HOSTNAME',
        'HTTP_REFERER'
    ]
    limit = -1  # default per logging.Formatter is None

    def format(self, record):
        """
        same as logging.Formatter.format, with added reporting of the meta_attrs when found in request.META, and the
        username that generated the Exception
        """
        s = super().format(record)

        if type(record.args) == dict and 'method' in record.args:
            s += "\nMETHOD: {value}".format(
                attr='USER',
                value=record.args['method']
            )

        if hasattr(record, 'request'):
            s += "\n{attr}: {value}".format(
                attr='USER',
                value=record.request.user
            )
            for attr in self.meta_attrs:
                if attr in record.request.META:
                    s += "\n{attr}: {value}".format(
                        attr=attr,
                        value=record.request.META[attr]
                    )
        return s

    def formatException(self, ei):
        """
        same as logging.Formatter.formatException except for the limit passed as a variable
        """
        sio = io.StringIO()
        tb = ei[2]

        traceback.print_exception(ei[0], ei[1], tb, self.limit, sio)
        s = sio.getvalue()
        sio.close()
        if s[-1:] == "\n":
            s = s[:-1]
        return s


class AdminDiscordHandler(logging.Handler):
    """An exception log handler that send a short log to a discord bot.

    """

    def __init__(self, *args, **kwargs):
        super().__init__()

        ''''''
        if 'webhook_url' in kwargs:
            self.webhook_url = kwargs['webhook_url']
        if 'title' in kwargs:
            self.title = kwargs['title']
        if 'body' in kwargs:
            self.body = kwargs['body']

        self.bot_data = None

        self.setFormatter(DiscordFormatter())

    def emit(self, record):
        self.send_message(self.format(record))

    def send_message(self, message):
        bot = QueueBot(
            webhook_url=self.webhook_url,
            title=self.title,
            body=message
        )
        bot.sendMessage()
