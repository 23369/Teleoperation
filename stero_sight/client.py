# sub.py
import zmq, cv2, numpy as np
ctx = zmq.Context()
sock = ctx.socket(zmq.SUB)
sock.connect("tcp://localhost:5555")
sock.setsockopt_string(zmq.SUBSCRIBE, "")
while True:
    msg = sock.recv()
    img = cv2.imdecode(np.frombuffer(msg, np.uint8), cv2.IMREAD_COLOR)
    if img is not None:
        cv2.imshow("recv", img)
        if cv2.waitKey(1)==27: break
