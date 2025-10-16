# modules/ra_videocom.py
class RaVideoCom:
    def __init__(self, context):
        self.context = context
    async def start_camera(self): pass
    async def stop_camera(self): pass
    async def handle_incoming_stream(self, stream): pass
