
## Setup Instructions

### Raspberry Pi

1. Clone the repository to your Raspberry Pi.
2. Navigate to the `raspberry_pi` directory.
3. Install the required packages:
    ```sh
    sudo apt update
    sudo apt install python3-pip
    pip3 install -r requirements.txt
    sudo apt install avahi-daemon avahi-utils
    ```
4. Ensure the Avahi service is running:
    ```sh
    sudo systemctl enable avahi-daemon
    sudo systemctl start avahi-daemon
    ```
5. Create a systemd service file to run the script on boot:
    ```sh
    sudo nano /etc/systemd/system/camera_feed.service
    ```
6. Add the following content, replacing `/path/to/` with the actual path of your `camera_feed.py` script:
    ```ini
    [Unit]
    Description=Camera Feed Service
    After=network.target

    [Service]
    ExecStart=/usr/bin/python3 /path/to/camera_feed.py
    WorkingDirectory=/path/to/
    StandardOutput=inherit
    StandardError=inherit
    Restart=always
    User=pi

    [Install]
    WantedBy=multi-user.target
    ```
7. Enable and start the service:
    ```sh
    sudo systemctl daemon-reload
    sudo systemctl enable camera_feed.service
    sudo systemctl start camera_feed.service
    ```

### Main Computer

1. Clone the repository to your main computer.
2. Navigate to the `main_computer` directory.
3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```
4. Run the `stitch_panoramas.py` script to start stitching the camera feeds:
    ```sh
    python stitch_panoramas.py
    ```
5. Navigate to the `qt_app` directory and run the PyQt5 application:
    ```sh
    python main.py
    ```

## Usage

1. Ensure the Raspberry Pis are running and connected to the same network.
2. Start the `stitch_panoramas.py` script on the main computer to discover and stitch the camera feeds.
3. Run the PyQt5 application to view the panorama and interact with the controls.

## Troubleshooting

- Ensure all devices are on the same network.
- Verify the Avahi service is running on the Raspberry Pis.
- Check the camera connections and indices if there are issues with capturing video.
