import sys
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtCore import QTimer
import cv2
import configparser
import requests
from zeroconf import ServiceBrowser, Zeroconf
import socket

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

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('ui/main_window.ui', self)

        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

        self.zeroconf = Zeroconf()
        self.listener = MyListener()
        self.browser = ServiceBrowser(self.zeroconf, "_http._tcp.local.", self.listener)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1000 // 30)  # 30 FPS

        self.start_recording_btn.clicked.connect(self.start_recording)
        self.stop_recording_btn.clicked.connect(self.stop_recording)
        self.save_still_btn.clicked.connect(self.save_still)
        self.apply_filter_btn.clicked.connect(self.apply_filter)

        self.recording = False

        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: white;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #5a5a5a;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
            QComboBox {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #5a5a5a;
            }
        """)

    def update_frame(self):
        if not self.listener.camera_feeds:
            return

        try:
            response = requests.get(self.listener.camera_feeds[0], stream=True, timeout=10)
            bytes_data = bytes()
            for chunk in response.iter_content(chunk_size=1024):
                bytes_data += chunk
                a = bytes_data.find(b'\xff\xd8')
                b = bytes_data.find(b'\xff\xd9')
                if a != -1 and b != -1:
                    jpg = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:]
                    image = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    self.display_image(image)
                    break
        except requests.exceptions.RequestException as e:
            print(f"Error fetching frame: {e}")

    def display_image(self, img):
        qformat = QtGui.QImage.Format_RGB888
        outImage = QtGui.QImage(img, img.shape[1], img.shape[0], img.strides[0], qformat)
        outImage = outImage.rgbSwapped()
        self.image_label.setPixmap(QtGui.QPixmap.fromImage(outImage))

    def start_recording(self):
        self.recording = True

    def stop_recording(self):
        self.recording = False

    def save_still(self):
        response = requests.get(self.config['SETTINGS']['SaveStillURL'])
        if response.status_code == 200:
            with open('still.jpg', 'wb') as file:
                file.write(response.content)

    def apply_filter(self):
        filter_name = self.filter_combo.currentText()
        requests.post(self.config['SETTINGS']['ApplyFilterURL'], data={'filter': filter_name})

    def closeEvent(self, event):
        self.zeroconf.close()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
