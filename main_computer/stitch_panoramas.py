import cv2
import numpy as np
from zeroconf import ServiceBrowser, Zeroconf
import time
import socket
import requests

class MyListener:
    def __init__(self):
        self.camera_feeds = []

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            address = socket.inet_ntoa(info.addresses[0])
            port = info.port
            url = f'http://{address}:{port}/camera/0'
            self.camera_feeds.append(url)
            print(f"Discovered camera feed: {url}")

    def update_service(self, zeroconf, type, name):
        # Handle service updates if needed
        pass

def fetch_frame(url):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        bytes_data = bytes()
        for chunk in response.iter_content(chunk_size=1024):
            bytes_data += chunk
            a = bytes_data.find(b'\xff\xd8')
            b = bytes_data.find(b'\xff\xd9')
            if a != -1 and b != -1:
                jpg = bytes_data[a:b+2]
                bytes_data = bytes_data[b+2:]
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                return frame
    except Exception as e:
        print(f"Error fetching frame from {url}: {e}")
    return None

def stitch_frames(frames):
    stitcher = cv2.Stitcher_create()
    status, pano = stitcher.stitch(frames)
    if status == cv2.Stitcher_OK:
        return pano
    else:
        print("Error during stitching")
        return None

def save_video(frames, filename='output.avi'):
    if not frames:
        print("No frames to save")
        return
    height, width, layers = frames[0].shape
    size = (width, height)
    out = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*'DIVX'), 10, size)
    for frame in frames:
        out.write(frame)
    out.release()
    print(f"Video saved as {filename}")

zeroconf = Zeroconf()
listener = MyListener()
browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)

recording = False
video_frames = []

try:
    while True:
        if not listener.camera_feeds:
            print("Waiting for camera feeds to be discovered...")
            time.sleep(2)
            continue

        frames = [fetch_frame(feed) for feed in listener.camera_feeds]
        if all(frame is not None for frame in frames):
            panorama = stitch_frames(frames)
            if panorama is not None:
                if recording:
                    video_frames.append(panorama)
                cv2.imshow('Panorama', panorama)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
except KeyboardInterrupt:
    print("Stopping...")
finally:
    cv2.destroyAllWindows()
    if recording:
        save_video(video_frames)
    zeroconf.close()
