import re, json, requests
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
microsoftapikey = config.microsoftapikey
microsoftfaceapikey = config.microsoftfaceapikey

# Camera Network ID for Video Link
NETWORK_ID = config.NETWORK_ID

# Array of MV serial numbers
COLLECT_CAMERAS_SERIAL_NUMBERS = config.COLLECT_CAMERAS_SERIAL_NUMBERS
# Array of zone id, all is *. eg ["*"]
COLLECT_ZONE_IDS = config.COLLECT_ZONE_IDS

# Motion trigger settings
# Number of concurrent people in frame to start trigger
MOTION_ALERT_PEOPLE_COUNT_THRESHOLD = config.MOTION_ALERT_PEOPLE_COUNT_THRESHOLD
MOTION_ALERT_VEHICLE_COUNT_THRESHOLD = config.MOTION_ALERT_VEHICLE_COUNT_THRESHOLD
# Number of MQTT
MOTION_ALERT_ITERATE_COUNT = config.MOTION_ALERT_ITERATE_COUNT
# Total people detections needed over MOTION_ALERT_ITERATE_COUNT to trigger notification
MOTION_ALERT_TRIGGER_PEOPLE_COUNT = config.MOTION_ALERT_TRIGGER_PEOPLE_COUNT
MOTION_ALERT_TRIGGER_VEHICLE_COUNT = config.MOTION_ALERT_TRIGGER_VEHICLE_COUNT
# Time between triggers, in seconds
MOTION_ALERT_PAUSE_TIME = config.MOTION_ALERT_PAUSE_TIME

# Do not modify
_PEOPLE_MONITORING_TRIGGERED = False
_VEHICLE_MONITORING_TRIGGERED = False
_PEOPLE_MONITORING_MESSAGE_COUNT = 0
_VEHICLE_MONITORING_MESSAGE_COUNT = 0
_MONITORING_PEOPLE_TOTAL_COUNT = 0
_MONITORING_VEHICLE_TOTAL_COUNT = 0
_MONITORING_PAUSE_ACTIVE = False

_LAST_PEOPLE_NOTIFY = int(time.time())
_LAST_VEHICLE_NOTIFY = int(time.time())

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

    global _PEOPLE_MONITORING_TRIGGERED,_PEOPLE_MONITORING_MESSAGE_COUNT, _MONITORING_PEOPLE_TOTAL_COUNT

    # If MOTION_ALERT_PEOPLE_COUNT_THRESHOLD triggered, start monitoring

    if config.people_detect:
      print("PEOPLE TRIGGERED: " + str(_PEOPLE_MONITORING_TRIGGERED))
      if _PEOPLE_MONITORING_TRIGGERED:
        if config.people_detect:
          if payload['counts']['person'] >= MOTION_ALERT_PEOPLE_COUNT_THRESHOLD:
              _PEOPLE_MONITORING_MESSAGE_COUNT += 1
  
              # Add current people count to total
              _MONITORING_PEOPLE_TOTAL_COUNT += payload['counts']['person']
              if _PEOPLE_MONITORING_MESSAGE_COUNT > MOTION_ALERT_ITERATE_COUNT:
                  if _MONITORING_PEOPLE_TOTAL_COUNT >= MOTION_ALERT_TRIGGER_PEOPLE_COUNT:
                      # Send notification
                      zones = merakiapi.getmvzones(MERAKI_API_KEY, serial_number)
                      for zone in zones:
                          if zone['zoneId'] == zone_id:
                              zone_name = zone['label']
                      notify(serial_number,'people',zone_name,zone_id)
                      # Wait before sending subsequent alert
                      #time.sleep(MOTION_ALERT_PAUSE_TIME)
  
                  # Reset
                  print("Resetting people values 1")
                  _PEOPLE_MONITORING_MESSAGE_COUNT = 0
                  _MONITORING_PEOPLE_TOTAL_COUNT = 0
                  _MONITORING_TRIGGERED = False
  
          else:
              #Reset
              print("Resetting people values 1")
              _PEOPLE_MONITORING_MESSAGE_COUNT = 0
              _MONITORING_PEOPLE_TOTAL_COUNT = 0
              _PEOPLE_MONITORING_TRIGGERED = False
            
    # If MOTION_ALERT_PEOPLE_COUNT_THRESHOLD triggered, start monitoring
    if ('person' in payload['counts'].keys()) and config.people_detect:
      if payload['counts']['person'] >= MOTION_ALERT_PEOPLE_COUNT_THRESHOLD:
        print("PEOPLE MONITORING TRIGGERED")
        _PEOPLE_MONITORING_TRIGGERED = True

def notify(serial_number,detection_type,zone_name,zone_id):
    global _LAST_PEOPLE_NOTIFY

    if detection_type == 'people':
        print("Time since last people notification: ")
        print(int(time.time()) - _LAST_PEOPLE_NOTIFY)
    if ((detection_type == 'people') and (int(time.time()) - _LAST_PEOPLE_NOTIFY) >= MOTION_ALERT_PAUSE_TIME):

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
        print("URL: {}".format(file))

        # WAIT FOR SNAPSHOT IMAGE
        time.sleep(4)

        videolink = merakiapi.getmvvideolink(MERAKI_API_KEY, NETWORK_ID, serial_number, ts)
        camera = merakiapi.getdevicedetail(MERAKI_API_KEY, NETWORK_ID, serial_number)
        
        msg = ""
        
        if detection_type == 'people':
        
          msg += "**New People Detection!** <br>"
          
          if config.image_detect:
            #MICROSOFT IMAGE DETECTION
            posturl = "{}/vision/v1.0/analyze?visualFeatures=categories,tags,faces".format(config.computervision_endpoint)
            headers = {
              'Ocp-Apim-Subscription-Key': format(str(microsoftapikey)),
              'Content-Type': 'application/json'
            }
            postdata = {
              #'url': 'https://spn16.meraki.com/stream/jpeg/snapshot/a9a675d665f5ba49VHODA3OThkMDY1Y2I3YWJiYjUzNzQzYWYyYTA4MDEyYjJmNzQ2NmQwYzkxZDA0MzZkNmI4YjZhOWEzNDRhZDRjManEcZLzQhsSgIvXY1Rrp64ynNWUCq3vFDmwbpm0DB2LjAJUOrVIu0_kDw1IKX3O-83oX4W43if8heYm8groFojxrDempDPdBZPmRhoMwLM7Znqbfn0jlPcClaoRPSzTZy02j0YE0OmX70-RmPIraZh9tPssnnlsWHfGNDS7ZKkbf4qHI-fXp39TEd6lZ6QOtz_gFYofETwniPWNwu54TiE'
              'url': file
            }
            postdata = json.dumps(postdata)
            imageresult = requests.post(posturl, data=postdata, headers=headers)
    
            cog = json.loads(imageresult.text)
            print(cog)
            
            tagstring = "**Detected Tags:** <br>"
            for tag in cog['tags']:
              if tag['confidence'] >= 0.8:
                tagstring += "&nbsp;&nbsp;&nbsp;&nbsp;{} <br>".format(tag['name'].capitalize())
                print(tag['name'].capitalize())
            
            msg += tagstring
          
          if config.face_detect:
            #MICROSOFT FACE DETECTION
            
            faceurl = "{}/detect".format(config.face_endpoint)
            headers = {
              'Ocp-Apim-Subscription-Key': microsoftfaceapikey,
              'Content-Type': 'application/json'
            }
            params = {
                'returnFaceId': 'true',
                'returnFaceLandmarks': 'false',
                'returnFaceAttributes': 'age,gender,headPose,smile,facialHair,glasses,emotion,hair,makeup,occlusion,accessories,blur,exposure,noise',
            }
            
            #image_url = 'https://spn16.meraki.com/stream/jpeg/snapshot/a9a675d665f5ba49VHODA3OThkMDY1Y2I3YWJiYjUzNzQzYWYyYTA4MDEyYjJmNzQ2NmQwYzkxZDA0MzZkNmI4YjZhOWEzNDRhZDRjManEcZLzQhsSgIvXY1Rrp64ynNWUCq3vFDmwbpm0DB2LjAJUOrVIu0_kDw1IKX3O-83oX4W43if8heYm8groFojxrDempDPdBZPmRhoMwLM7Znqbfn0jlPcClaoRPSzTZy02j0YE0OmX70-RmPIraZh9tPssnnlsWHfGNDS7ZKkbf4qHI-fXp39TEd6lZ6QOtz_gFYofETwniPWNwu54TiE'
            image_url = file
            
            response = requests.post(faceurl, params=params,
                                     headers=headers, json={"url": image_url})
            rstr = json.dumps(response.json())
            faces = json.loads(rstr)
            print(faces)
            
            facecount = 0
            facestring = ""
            
            for face in faces:
              facecount += 1 
              facestring += "**Face {}:** <br>".format(facecount)
              for k,v in face['faceAttributes'].items():
                if k == 'age':
                  facestring += "&nbsp;&nbsp;&nbsp;&nbsp;Age: {} <br>".format(v)
                  print("Age: {}".format(v))
                if k == 'gender':
                  facestring += "&nbsp;&nbsp;&nbsp;&nbsp;Gender: {} <br>".format(v.capitalize())
                  print("Gender: {}".format(v.capitalize()))
                if k == 'emotion':
                  for key in v:
                    if v[key] >= 0.5:
                      facestring += "&nbsp;&nbsp;&nbsp;&nbsp;Emotion: {} <br>".format(key.capitalize())
                      print("Emotion: {}".format(key))
                if k == 'glasses':
                  facestring += "&nbsp;&nbsp;&nbsp;&nbsp;Glasses: {} <br>".format(v)
                  print("Glasses: {}".format(v))
    
            msg += "**Total Faces Detected:** {} <br> {} <br>".format(facecount, facestring)

        msg += "**Camera:** {} ({}) <br> **Zone:** {}  <br> **Video Link:** {}".format(camera['name'], serial_number, zone_name.capitalize(), videolink['url'])
        print("MESSAGE: %s" % msg)
        result = sent_notification(msg,files=file)
        
        if detection_type == 'people':
          _LAST_PEOPLE_NOTIFY = int(time.time())
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
