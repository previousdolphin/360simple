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
            address = socket.inet_ntoa(info.address)
            port = info.port
            url = f'http://{address}:{port}/camera/0'
            self.camera_feeds.append(url)
            print(f"Discovered camera feed: {url}")

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

        response = requests.get(self.listener.camera_feeds[0], stream=True)
        if response.status_code == 200:
            frame = response.raw.read()
            image = cv2.imdecode(np.frombuffer(frame, np.uint8), cv2.IMREAD_COLOR)
            self.display_image(image)

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
