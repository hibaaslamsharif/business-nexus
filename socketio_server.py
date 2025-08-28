import os
import asyncio
from aiohttp import web
import socketio

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mywork.settings')

# Initialize Django first
import django
django.setup()

# Import the sio variable from socketio_config
from chat import socketio_config

# Create the Socket.IO server with CORS and async settings
sio = socketio.AsyncServer(
    async_mode='aiohttp',
    cors_allowed_origins='*',
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1e8,  # 100MB
    async_handlers=True,
    logger=True,
    engineio_logger=True
)

# Set the sio instance in the config module
socketio_config.sio = sio

# Import event handlers after sio is set
from chat.socketio_config import *

# Create aiohttp application
app = web.Application()
app.router.add_static('/static', 'static')

# Attach the Socket.IO server to the aiohttp app
sio.attach(app)

# Add Socket.IO routes
app.router.add_route('*', '/socket.io/', sio.handle_request)

async def init_app():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8003)  # Reverted to port 8003
    return runner, site

if __name__ == '__main__':
    print('Starting Socket.IO server on port 8003...')
    loop = asyncio.get_event_loop()
    runner, site = loop.run_until_complete(init_app())
    loop.run_until_complete(site.start())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(runner.cleanup())
