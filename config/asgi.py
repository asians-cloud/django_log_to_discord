"""
ASGI config for Django Log To Discord project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/asgi/

"""
import os
import sys
from pathlib import Path

from asgiref.sync import ThreadSensitiveContext, sync_to_async

import django
from django.core import signals
from django.core.handlers.asgi import ASGIHandler
from django.core.exceptions import RequestAborted
from django.http import FileResponse
from django.urls import set_script_prefix


# Mitigation for HTTP ASGI with FIFO problem
class AsyncASGIHandler(ASGIHandler):
    async def __call__(self, scope, receive, send):
        """
        Async entrypoint - parses the request and hands off to get_response.
        """
        # Serve only HTTP connections.
        # FIXME: Allow to override this.
        if scope['type'] != 'http':
            raise ValueError(
                'Django can only handle ASGI/HTTP connections, not %s.'
                % scope['type']
            )

        async with ThreadSensitiveContext():
            await self.handle(scope, receive, send)

    async def handle(self, scope, receive, send):
        """
        Handles the ASGI request. Called via the __call__ method.
        """
        # Receive the HTTP request body as a stream object.
        try:
            body_file = await self.read_body(receive)
        except RequestAborted:
            return
        # Request is complete and can be served.
        set_script_prefix(self.get_script_prefix(scope))
        await sync_to_async(signals.request_started.send, thread_sensitive=True)(sender=self.__class__, scope=scope)
        # Get the request and check for basic issues.
        request, error_response = self.create_request(scope, body_file)
        if request is None:
            await self.send_response(error_response, send)
            return
        # Get the response, using the async mode of BaseHandler.
        response = await self.get_response_async(request)
        response._handler_class = self.__class__
        # Increase chunk size on file responses (ASGI servers handles low-level
        # chunking).
        if isinstance(response, FileResponse):
            response.block_size = self.chunk_size
        # Send the response.
        await self.send_response(response, send)

def get_asgi_application():
    """
    The public interface to Django's ASGI support. Return an ASGI 3 callable.

    Avoids making django.core.handlers.ASGIHandler a public API, in case the
    internal implementation changes or moves in the future.
    """
    django.setup(set_prefix=False)
    return AsyncASGIHandler()


# This allows easy placement of apps within the interior
# django_log_to_discord directory.
ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent
sys.path.append(str(ROOT_DIR / "django_log_to_discord"))

# If DJANGO_SETTINGS_MODULE is unset, default to the local settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

# This application object is used by any ASGI server configured to use this file.
django_application = get_asgi_application()
# Apply ASGI middleware here.
# from helloworld.asgi import HelloWorldApplication
# application = HelloWorldApplication(application)

# Import websocket application here, so apps from django_application are loaded first
from config.websocket import websocket_application  # noqa isort:skip


async def application(scope, receive, send):
    if scope["type"] == "http":
        await django_application(scope, receive, send)
    elif scope["type"] == "websocket":
        await websocket_application(scope, receive, send)
    else:
        raise NotImplementedError(f"Unknown scope type {scope['type']}")
