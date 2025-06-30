# File: image_server.py
#!/usr/bin/env python3
import cv2
import zmq
import time
import struct
from collections import deque
import numpy as np
import json
import pyrealsense2 as rs

class RealSenseCamera:
    def __init__(self, img_shape, fps, serial_number=None, enable_depth=False):
        self.img_shape = img_shape  # [h, w]
        self.fps = fps
        self.serial_number = serial_number
        self.enable_depth = enable_depth
        self.align = rs.align(rs.stream.color)
        self._init_realsense()

    def _init_realsense(self):
        self.pipeline = rs.pipeline()
        cfg = rs.config()
        if self.serial_number:
            cfg.enable_device(self.serial_number)
        h, w = self.img_shape
        cfg.enable_stream(rs.stream.color, w, h, rs.format.bgr8, self.fps)
        if self.enable_depth:
            cfg.enable_stream(rs.stream.depth, w, h, rs.format.z16, self.fps)
        profile = self.pipeline.start(cfg)
        if self.enable_depth:
            ds = profile.get_device().first_depth_sensor()
            self.depth_scale = ds.get_depth_scale()

    def get_frame(self):
        frames = self.align.process(self.pipeline.wait_for_frames())
        c = frames.get_color_frame()
        if not c:
            return None, None
        img = np.asanyarray(c.get_data())
        d = None
        if self.enable_depth:
            df = frames.get_depth_frame()
            d = np.asanyarray(df.get_data()) if df else None
        return img, d

    def release(self):
        self.pipeline.stop()

class OpenCVCamera:
    def __init__(self, device_id, img_shape, fps):
        h, w = img_shape
        self.cap = cv2.VideoCapture(device_id, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FOURCC,
                     cv2.VideoWriter.fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        if not self.cap.isOpened():
            raise RuntimeError(f"/dev/video{device_id} open failed")

    def get_frame(self):
        ret, f = self.cap.read()
        return f if ret else None

    def release(self):
        self.cap.release()

class ImageServer:
    def __init__(self, cfg, port=5555, unit_test=False):
        self.fps = cfg.get("fps", 30)
        self.head_type = cfg.get("head_camera_type","opencv")
        self.head_shape = cfg.get("head_camera_image_shape",[480,640])
        self.head_ids = cfg.get("head_camera_id_numbers",[0])
        self.unit_test = unit_test

        # cameras
        self.cams = self._create(self.head_type,
                                 self.head_ids,
                                 self.head_shape)
        # detect side-by-side
        self.stereo = (self.head_type=="opencv"
                       and len(self.cams)==1
                       and self.head_shape[1]%2==0)

        ctx=zmq.Context()
        self.sock=ctx.socket(zmq.PUB)
        self.sock.bind(f"tcp://*:{port}")
        if unit_test:
            self._init_perf()

    def _create(self,ctype,ids,shape):
        out=[]
        if ctype=="opencv":
            for i in ids:
                out.append(OpenCVCamera(i,shape,self.fps))
        elif ctype=="realsense":
            for s in ids:
                out.append(RealSenseCamera(shape,self.fps,s))
        else:
            raise ValueError("bad type")
        return out

    def _init_perf(self):
        self.frame_cnt=0
        self.times=deque()

    def _perf(self):
        t=time.time()
        self.times.append(t)
        while self.times and self.times[0]<t-1.0:
            self.times.popleft()
        self.frame_cnt+=1
        if self.frame_cnt%30==0:
            print(f"FPS {len(self.times):.1f}")

    def send_loop(self):
        try:
            while True:
                imgs=[]
                for cam in self.cams:
                    f=cam.get_frame()
                    if f is None: continue
                    if self.stereo:
                        w=f.shape[1]//2
                        imgs.extend([f[:,:w],f[:,w:]])
                    else:
                        imgs.append(f)
                if not imgs: continue
                big=cv2.hconcat(imgs)
                ok,buf=cv2.imencode(".jpg",big)
                if not ok: continue
                data=buf.tobytes()
                if self.unit_test:
                    meta=json.dumps({
                        "ts":time.time(),
                        "frame":self.frame_cnt
                    }).encode()
                    self.sock.send_multipart([meta,data])
                    self._perf()
                else:
                    self.sock.send(data)
        finally:
            for c in self.cams: c.release()
            self.sock.close()

if __name__=="__main__":
    cfg={
      "fps":30,
      "head_camera_type":"opencv",
      "head_camera_image_shape":[480,1280],
      "head_camera_id_numbers":[2]
    }
    s=ImageServer(cfg,unit_test=True)
    s.send_loop()
