# Meraki Camera Notification

[![published](https://static.production.devnetcloud.com/codeexchange/assets/images/devnet-published.svg)](https://developer.cisco.com/codeexchange/github/repo/CiscoDevNet/Meraki-Camera-Notification)

This is an extension of the Meraki Camera Notification script found here: https://github.com/CiscoDevNet/Meraki-Camera-Notification

Leverage Meraki new camera API and MQTT capability to create a notification service. When the camera detects a person consistently appears in a particular zone the service will send a Webex team message to a Webex team room with a video link which will directly go to the video footage when that event occurred.

![](/docs/digram.png)

## Meraki and MQTT Configuration

1. Install an MQTT Broker

`apt-get install mosquitto mosquitto-client`

2. Go to **Cameras > [Camera Name] > Settings > Sense** page.
3. Click **Add or edit MQTT Brokers > New MQTT Broker** and add your broker information.
4. Make sure that your mosquitto server is accessible from the Internet and it's receiving events from Dashboard.

`mosquitto_sub -v -h server_ip -p 1883 -t '/merakimv/#'`


## Build locally
### Config
#### Open and complete all fields in `config.py`

### Build
1. Run `pip3 install -r requirements.txt`
2. Run `python3 app.py`

## Docker

Build : `docker build -t meraki-camera-notification .`

Run : `docker run -it meraki-camera-notification .`
