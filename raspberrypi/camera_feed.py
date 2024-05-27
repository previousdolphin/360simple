import cv2
from flask import Flask, Response, request
import numpy as np
import os

app = Flask(__name__)

def generate_frames(camera_index, filter_name=None):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"Error: Could not open camera {camera_index}")
        return
    while True:
        success, frame = cap.read()
        if not success:
            print(f"Error: Failed to capture image from camera {camera_index}")
            break
        if filter_name:
            frame = apply_filter(frame, filter_name)
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            print(f"Error: Failed to encode image from camera {camera_index}")
            break
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def apply_filter(frame, filter_name):
    if filter_name == 'grayscale':
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    elif filter_name == 'sepia':
        kernel = np.array([[0.272, 0.534, 0.131],
                           [0.349, 0.686, 0.168],
                           [0.393, 0.769, 0.189]])
        return cv2.transform(frame, kernel)
    return frame

@app.route('/camera/<int:camera_index>')
def video_feed(camera_index):
    filter_name = request.args.get('filter')
    return Response(generate_frames(camera_index, filter_name),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # Use os.system to register the service with Avahi
    os.system("avahi-publish -s 'PiCamera' _http._tcp 5000 &")
    app.run(host='0.0.0.0', port=5000)
