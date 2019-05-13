import json, requests
import time, datetime
import paho.mqtt.client as mqtt
import config, merakiapi

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
_MONITORING_PAUSE_ACTIVE = False

_LAST_NOTIFY = int(time.time())


def collect_zone_information(topic, payload):
    # Get serial and zone from MQTT
    parameters = topic.split("/")
    serial_number = parameters[2]
    zone_id = parameters[3]
    index = len([i for i, x in enumerate(COLLECT_ZONE_IDS) if x == zone_id])

    # Filter out lux messages
    if COLLECT_ZONE_IDS[0] != "*":
        if index == 0 or zone_id == "0":
            return

    global _MONITORING_TRIGGERED, _MONITORING_MESSAGE_COUNT, _MONITORING_PEOPLE_TOTAL_COUNT

    # If MOTION_ALERT_PEOPLE_COUNT_THRESHOLD triggered, start monitoring

    if _MONITORING_TRIGGERED:
        if payload['counts']['person'] >= MOTION_ALERT_PEOPLE_COUNT_THRESHOLD:
            _MONITORING_MESSAGE_COUNT += 1

            # Add current people count to total
            _MONITORING_PEOPLE_TOTAL_COUNT += payload['counts']['person']
            if _MONITORING_MESSAGE_COUNT > MOTION_ALERT_ITERATE_COUNT:
                if _MONITORING_PEOPLE_TOTAL_COUNT >= MOTION_ALERT_TRIGGER_PEOPLE_COUNT:
                    # Send notification
                    zones = merakiapi.getmvzones(MERAKI_API_KEY, serial_number)
                    for zone in zones:
                        if zone['zoneId'] == zone_id:
                            zone_name = zone['label']
                    notify(serial_number,zone_name)
                    # Wait before sending subsequent alert
                    #time.sleep(MOTION_ALERT_PAUSE_TIME)
                
                # Reset
                print("Resetting values")
                _MONITORING_MESSAGE_COUNT = 0
                _MONITORING_PEOPLE_TOTAL_COUNT = 0
                _MONITORING_TRIGGERED = False
                
        else:
            #Reset
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


def notify(serial_number,zone_name):
    global _LAST_NOTIFY
    print("Time since last notification: ")
    print(int(time.time()) - _LAST_NOTIFY)
    if ((int(time.time()) - _LAST_NOTIFY) >= MOTION_ALERT_PAUSE_TIME):

        ts = str(time.time()).split(".")[0] + "000"
        #snaptime = (datetime.datetime.now() - datetime.timedelta(seconds=5)).isoformat().split(".")[0] + "-06:00"
        #print(snaptime)
        
        posturl = 'https://dashboard.meraki.com/api/v0/networks/{0}/cameras/{1}/snapshot'.format(NETWORK_ID, serial_number)
        headers = {
            'x-cisco-meraki-api-key': format(str(MERAKI_API_KEY)),
            'Content-Type': 'application/json'
        }
        postdata = {
            #'timestamp': format(str(snaptime))	
        }

        dashboard = requests.post(posturl, data=json.dumps(postdata), headers=headers)
        djson = json.loads(dashboard.text)
        file = format(str(djson['url']))
                
        videolink = merakiapi.getmvvideolink(MERAKI_API_KEY, NETWORK_ID, serial_number, ts)
        camera = merakiapi.getdevicedetail(MERAKI_API_KEY, NETWORK_ID, serial_number)
    
        msg = "**New People Detection!** <br> **Camera:** {} ({}) <br> **Zone:** {} <br> **Total detections:** {}  <br> **Video Link:** {}".format(camera['name'], serial_number, zone_name, MOTION_ALERT_PEOPLE_COUNT_THRESHOLD, videolink['url'])
        time.sleep(3)
        result = sent_notification(msg,files=file)
        
        _LAST_NOTIFY = int(time.time())
    else:
        print("Skipping Notification, too soon")
    



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
