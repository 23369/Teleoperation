#!/usr/bin/env python3
import threading, json, base64, asyncio
from vuer import Vuer
from vuer.schemas import ImageBackground
from aiohttp import WSMsgType

# 确保 video_server.py 在同目录，并定义了 VideoWebSocketServer
from video_server import VideoWebSocketServer

# —— 1) 后台启动 WebSocket 转发器 —— 
threading.Thread(
    target=lambda: VideoWebSocketServer().run(),
    daemon=True
).start()

# —— 2) 创建 Vuer 应用 —— 
app = Vuer(host='0.0.0.0', port=8012, queries={'grid': False})

# —— 立体显示参数 —— 
EYE_SEP = 0.06
PLANE_W = 1.2
PLANE_H = PLANE_W * (480 / 640)  # 假设上下比 480:640

# —— 3) 注册渲染循环 —— 
@app.spawn(start=True)
async def render_loop(session, fps=30):
    # 首次插入左右两块平面
    await session.upsert([
        ImageBackground(
            name='left_eye',
            key='bg-left',
            width=PLANE_W,
            height=PLANE_H,
            position=(-EYE_SEP / 2, 1.5, -2)
        ),
        ImageBackground(
            name='right_eye',
            key='bg-right',
            width=PLANE_W,
            height=PLANE_H,
            position=( EYE_SEP / 2, 1.5, -2)
        )
    ], to='bgChildren')

    # 建立 WebSocket 连接到 8080/ws/video
    ws = await session.ws_connect('ws://localhost:8080/ws/video')

    while True:
        msg = await ws.receive()
        if msg.type == WSMsgType.TEXT:
            # 收到 metadata，可打印查看
            meta = json.loads(msg.data)
            print(f"frame={meta['frame']} ts={meta['ts']:.3f}")
        elif msg.type == WSMsgType.BINARY:
            # 收到 JPEG bytes，转 DataURL
            url = 'data:image/jpeg;base64,' + base64.b64encode(msg.data).decode()
            # 更新左右贴图（UV 横向各取一半）
            await session.upsert([
                ImageBackground(
                    key='bg-left',
                    image=url,
                    uv_offset=(0.0, 0.0),
                    uv_scale=(0.5, 1.0)
                ),
                ImageBackground(
                    key='bg-right',
                    image=url,
                    uv_offset=(0.5, 0.0),
                    uv_scale=(0.5, 1.0)
                )
            ], to='bgChildren')
        # 控制渲染频率
        await asyncio.sleep(1.0 / fps)

# —— 入口 —— 
if __name__ == '__main__':
    app.run()
