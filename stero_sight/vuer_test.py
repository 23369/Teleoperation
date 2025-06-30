#!/usr/bin/env python3
import asyncio
from vuer import Vuer
from vuer.schemas import ImageBackground

# 1) 创建 Vuer 应用（不需要证书也行）
app = Vuer(host='0.0.0.0', port=8012, queries={'grid': False})

# 2) 注册一个简单的渲染任务，start=True 表示 app.run() 时立刻执行
@app.spawn(start=True)
async def render_once(session):
    # Data URL：1×1 红色像素
    red_pixel = (
      'data:image/png;base64,'
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC'
      'AAAAC0lEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=='
    )
    # 一张占满屏幕的红色背景
    await session.upsert([
        ImageBackground(
            image=red_pixel,
            key='red-bg',
            width=2,   # 世界坐标宽度
            height=2,  # 世界坐标高度
            position=(0, 0, -2),
        )
    ], to='children')

    # 停一下，渲染完成后不再更新
    await asyncio.sleep(1e6)

# 3) 启动服务
if __name__ == '__main__':
    app.run()
