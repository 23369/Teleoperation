#!/usr/bin/env python3
import cv2
import zmq
import time
import struct
from collections import deque
import numpy as np
import pyrealsense2 as rs


# ----------- 单摄封装 ----------- #
class RealSenseCamera:
    def __init__(self, img_shape, fps, serial_number=None, enable_depth=False):
        self.img_shape = img_shape          # [h, w]
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
        cfg.enable_stream(rs.stream.color,
                          self.img_shape[1], self.img_shape[0],
                          rs.format.bgr8, self.fps)
        if self.enable_depth:
            cfg.enable_stream(rs.stream.depth,
                              self.img_shape[1], self.img_shape[0],
                              rs.format.z16, self.fps)
        profile = self.pipeline.start(cfg)
        if self.enable_depth:
            depth_sensor = profile.get_device().first_depth_sensor()
            self.g_depth_scale = depth_sensor.get_depth_scale()

    def get_frame(self):
        frames = self.align.process(self.pipeline.wait_for_frames())
        color = frames.get_color_frame()
        if not color:
            return None, None
        color_img = np.asanyarray(color.get_data())
        depth_img = None
        if self.enable_depth:
            depth = frames.get_depth_frame()
            depth_img = np.asanyarray(depth.get_data()) if depth else None
        return color_img, depth_img

    def release(self):
        self.pipeline.stop()


class OpenCVCamera:
    def __init__(self, device_id, img_shape, fps):
        self.id = device_id
        self.img_shape = img_shape
        self.cap = cv2.VideoCapture(self.id, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  img_shape[1])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, img_shape[0])
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        if not self.cap.isOpened():
            raise RuntimeError(f"Camera /dev/video{device_id} open failed")

    def get_frame(self):
        ok, frame = self.cap.read()
        return frame if ok else None

    def release(self):
        self.cap.release()


# ----------- 服务器 ----------- #
class ImageServer:
    def __init__(self, cfg, port=5555, unit_test=False):
        self.fps  = cfg.get("fps", 30)
        self.head_type  = cfg.get("head_camera_type", "opencv")
        self.head_shape = cfg.get("head_camera_image_shape", [480, 640])
        self.head_ids   = cfg.get("head_camera_id_numbers", [0])

        self.wrist_type  = cfg.get("wrist_camera_type")
        self.wrist_shape = cfg.get("wrist_camera_image_shape", [480, 640])
        self.wrist_ids   = cfg.get("wrist_camera_id_numbers")

        self.unit_test = unit_test

        # 初始化摄像头
        self.head_cams = self._create_cams(self.head_type, self.head_ids,
                                           self.head_shape)
        self.wrist_cams = self._create_cams(self.wrist_type, self.wrist_ids,
                                            self.wrist_shape) if self.wrist_type else []

        # Side-by-Side 双目判定
        self.stereo_split = (self.head_type == "opencv"
                             and len(self.head_cams) == 1
                             and self.head_shape[1] % 2 == 0 #这里判断仅为强行锁定为双目
                             #and self.head_shape[1] == 2 * self.head_shape[0]
                             )

        # ZeroMQ
        ctx = zmq.Context()
        self.sock = ctx.socket(zmq.PUB)
        self.sock.bind(f"tcp://*:{port}")

        if self.unit_test:
            self._init_perf()

    def _create_cams(self, ctype, ids, shape):
        cams = []
        if not ids:
            return cams
        if ctype == "opencv":
            for i in ids:
                cams.append(OpenCVCamera(i, shape, self.fps))
        elif ctype == "realsense":
            for sn in ids:
                cams.append(RealSenseCamera(shape, self.fps, sn))
        else:
            raise ValueError("Unsupported camera type")
        return cams

    # 性能统计
    def _init_perf(self):
        self.frame_cnt = 0
        self.time_win = 1.0
        self.times = deque()
        self.t0 = time.time()

    def _perf_tick(self):
        t = time.time()
        self.times.append(t)
        while self.times and self.times[0] < t - self.time_win:
            self.times.popleft()
        self.frame_cnt += 1
        if self.frame_cnt % 30 == 0:
            fps = len(self.times) / self.time_win
            print(f"FPS {fps:.1f}")

    # 主循环
    def send_loop(self):
        try:
            while True:
                head_frames = []
                for cam in self.head_cams:
                    img = (cam.get_frame() if self.head_type == "opencv"
                           else cam.get_frame()[0])
                    if img is None:
                        continue
                    if self.stereo_split:
                        w = img.shape[1] // 2
                        head_frames.extend([img[:, :w], img[:, w:]])
                    else:
                        head_frames.append(img)

                if not head_frames:
                    continue

                head_cat = cv2.hconcat(head_frames)

                if self.wrist_cams:
                    wrist_frames = []
                    for cam in self.wrist_cams:
                        img = (cam.get_frame() if self.wrist_type == "opencv"
                               else cam.get_frame()[0])
                        if img is not None:
                            wrist_frames.append(img)
                    if wrist_frames:
                        head_cat = cv2.hconcat([head_cat,
                                                cv2.hconcat(wrist_frames)])

                ok, buf = cv2.imencode(".jpg", head_cat)
                if not ok:
                    continue
                payload = buf.tobytes()

                if self.unit_test:
                    header = struct.pack("dI", time.time(), self.frame_cnt)
                    self.sock.send(header + payload)
                    self._perf_tick()
                else:
                    self.sock.send(payload)
        except KeyboardInterrupt:
            pass
        finally:
            for c in self.head_cams + self.wrist_cams:
                c.release()
            self.sock.close()

# ----------- 入口 ----------- #
if __name__ == "__main__":
    cfg = {
        "fps": 30,
        "head_camera_type": "opencv",
        "head_camera_image_shape": [480, 1280],   # 整幅 1280×480
        "head_camera_id_numbers": [6],            # /dev/video6
        # wrist 不启用
    }
    ImageServer(cfg).send_loop()
