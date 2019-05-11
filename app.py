import json, requests
import time
import paho.mqtt.client as mqtt
import config

from webexteam import sent_notification

# MQTT setting
MQTT_SERVER = config.MQTT_SERVER
MQTT_PORT = 1883
MQTT_TOPIC = "/merakimv/#"

# Meraki API key
MERAKI_API_KEY = config.MERAKI_API_KEY

# Camera Network ID for Video Link
NETWORK_ID = config.NETWORK_ID

# Array of MV serial numbers
COLLECT_CAMERAS_SERIAL_NUMBERS = config.COLLECT_CAMERAS_SERIAL_NUMBERS
# Array of zone id, all is *. eg ["*"]
COLLECT_ZONE_IDS = config.COLLECT_ZONE_IDS

# Motion trigger settings
# Number of concurrent people in frame to start trigger
MOTION_ALERT_PEOPLE_COUNT_THRESHOLD = config.MOTION_ALERT_PEOPLE_COUNT_THRESHOLD
# Number of MQTT
MOTION_ALERT_ITERATE_COUNT = config.MOTION_ALERT_ITERATE_COUNT
# Total people detections needed over MOTION_ALERT_ITERATE_COUNT to trigger notification
MOTION_ALERT_TRIGGER_PEOPLE_COUNT = config.MOTION_ALERT_TRIGGER_PEOPLE_COUNT
# Time between triggers, in seconds
MOTION_ALERT_PAUSE_TIME = config.MOTION_ALERT_PAUSE_TIME

# Do not modify
_MONITORING_TRIGGERED = False
_MONITORING_MESSAGE_COUNT = 0
_MONITORING_PEOPLE_TOTAL_COUNT = 0


def collect_zone_information(topic, payload):
    # Get serial and zone from MQTT
    parameters = topic.split("/")
    serial_number = parameters[2]
    zone_id = parameters[3]
    index = len([i for i, x in enumerate(COLLECT_ZONE_IDS) if x == zone_id])

    # If not a zone, quit
    if COLLECT_ZONE_IDS[0] != "*":
        if index == 0 or zone_id == "0":
            return

    global _MONITORING_TRIGGERED, _MONITORING_MESSAGE_COUNT, _MONITORING_PEOPLE_TOTAL_COUNT

    # If MOTION_ALERT_PEOPLE_COUNT_THRESHOLD triggered, start monitoring

    if _MONITORING_TRIGGERED:
        _MONITORING_MESSAGE_COUNT += 1

        # Add current people count to total
        _MONITORING_PEOPLE_TOTAL_COUNT += payload['counts']['person']
        if _MONITORING_MESSAGE_COUNT > MOTION_ALERT_ITERATE_COUNT:
            if _MONITORING_PEOPLE_TOTAL_COUNT >= MOTION_ALERT_TRIGGER_PEOPLE_COUNT:
                # Send notification
                notify(serial_number)
                # Wait before sending subsequent alert
                time.sleep(MOTION_ALERT_PAUSE_TIME)

            # reset
            _MONITORING_MESSAGE_COUNT = 0
            _MONITORING_PEOPLE_TOTAL_COUNT = 0
            _MONITORING_TRIGGERED = False

    # If MOTION_ALERT_PEOPLE_COUNT_THRESHOLD triggered, start monitoring
    if payload['counts']['person'] >= MOTION_ALERT_PEOPLE_COUNT_THRESHOLD:
        _MONITORING_TRIGGERED = True

    print("payload : " + str(payload) +
          ", _MONITORING_TRIGGERED : " + str(_MONITORING_TRIGGERED) +
          ", _MONITORING_MESSAGE_COUNT : " + str(_MONITORING_MESSAGE_COUNT) +
          ", _MONITORING_PEOPLE_TOTAL_COUNT : " + str(_MONITORING_PEOPLE_TOTAL_COUNT))


def notify(serial_number):
    # Get video link
    ts = str(time.time()).split(".")[0] + "000"
    url = "https://dashboard.meraki.com/api/v0/networks/{1}/cameras/{0}/videoLink?timestamp={2}".format(serial_number, NETWORK_ID, ts)

    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        "Content-Type": "application/json"
    }
    resp = requests.get(url, headers=headers)
    respjson = json.loads(resp.text)

    if int(resp.status_code / 100) == 2:
        msg = "Camera {} detected at least ({}) person(s).  \n Video : {}".format(serial_number, MOTION_ALERT_PEOPLE_COUNT_THRESHOLD, respjson['url'])
        result = sent_notification(msg)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(MQTT_TOPIC)


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode("utf-8"))
    parameters = msg.topic.split("/")
    serial_number = parameters[2]
    # filter camera
    if COLLECT_CAMERAS_SERIAL_NUMBERS[0] != "*" or len(
            [i for i, x in enumerate(COLLECT_CAMERAS_SERIAL_NUMBERS) if x == serial_number]):
        return
    if msg.topic[-14:] != 'raw_detections':
        collect_zone_information(msg.topic, payload)


if __name__ == "__main__":

    # MQTT
    try:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect(MQTT_SERVER, MQTT_PORT, 60)
        client.loop_forever() #Script runs until manually stopped
    except Exception as ex:
        print("[MQTT]failed to connect or receive msg from mqtt, due to: \n {0}".format(ex))
