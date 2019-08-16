# Meraki Camera Notification

This is an extension/rewrite of the Meraki Camera Notification script found here: https://github.com/CiscoDevNet/Meraki-Camera-Notification

This script leverages Meraki's camera API and MQTT as part of MV Sense to create a notification service. When the camera detects a defined number of people in a particular zone the service will send a Webex Teams message with a snapshot and a link to the video footage.

![](https://i.imgur.com/kIb1ts8.png)
![](https://i.imgur.com/IcuRy1L.png)

## Meraki and MQTT Configuration

1. Install an MQTT Broker

`apt-get install mosquitto mosquitto-client`

2. In Dashboard, Go to **Cameras > [Camera Name] > Settings > Sense**.
3. Click **Add or edit MQTT Brokers > New MQTT Broker** and add your broker information.
4. Make sure that your mosquitto server is accessible from your camera and that it's receiving events.

`mosquitto_sub -v -h `_**server_ip**_` -p 1883 -t '/merakimv/#'`


## Build locally

### Build
```bash
git clone git://github.com/nathanwiens/mv-webex-bot
cd mv-webex-bot
pip3 install -r requirements.txt
```

### Config
Open and complete all fields in `config.py`

Add mvnotify@webex.bot to your WebEx Teams room

### Run
```bash
python3 app.py
```

## Docker

### Build
```bash
git clone git://github.com/nathanwiens/mv-webex-bot
cd mv-webex-bot
```
Open and complete all fields in `config.py`

Add mvnotify@webex.bot to your WebEx Teams room
```
docker build -t meraki-camera-notification .
```

### Run 
```
docker run -it meraki-camera-notification .
```

## Docker-compose

```
  mvbot:
    container_name: mvbot
    image: mvbot
    build: ./mv-webex-bot/
    restart: unless-stopped
    network_mode: host
    environment:
      - TZ=America/Denver
    volumes:
      - ./mv-webex-bot:/opt
```
