#!/usr/bin/env python3
import asyncio, zmq, zmq.asyncio, struct, json
from aiohttp import web

class VideoWebSocketServer:
    def __init__(self,
                 zmq_addr='tcp://localhost:5555',
                 ws_port=8080,
                 ws_path='/ws/video'):
        ctx = zmq.asyncio.Context()
        self.sock = ctx.socket(zmq.SUB)
        self.sock.connect(zmq_addr)
        self.sock.setsockopt_string(zmq.SUBSCRIBE, '')
        self.app = web.Application()
        self.app.add_routes([web.get(ws_path, self._handler)])
        self.ws_port = ws_port

    async def _handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        try:
            while True:
                data = await self.sock.recv()
                # detect header (not JPEG SOI)
                if not (data[0]==0xFF and data[1]==0xD8):
                    hdr = data[:12]
                    ts, frame = struct.unpack('dI', hdr)
                    await ws.send_str(json.dumps({'ts': ts, 'frame': frame}))
                    img = data[12:]
                else:
                    img = data
                await ws.send_bytes(img)
        except asyncio.CancelledError:
            pass
        finally:
            await ws.close()
        return ws

    def run(self):
        web.run_app(self.app, port=self.ws_port, handle_signals=False)

if __name__ == '__main__':
    VideoWebSocketServer().run()
