#Meraki MV Parameters
# 
MQTT_SERVER = "X.X.X.X"
MERAKI_API_KEY = "AAAAAAA"
NETWORK_ID = "N_BBBBBBB"
microsoftapikey = "CCCCCC"
computervision_endpoint = "https://DDDDDDD.azure.com"
microsoftfaceapikey = "EEEEEEE"
face_endpoint = "https://FFFFFFF.azure.com/face/v1.0"

#Enable/Disable Person Detection
people_detect = True

#Enable/Disable Microsoft Cognitive Services Image Analysis
image_detect = True

#Enable/Disable Microsoft Cognitive Services Face API
face_detect = True

# Array of MV serial numbers, all is *. eg ["*"] or ["Q2XX-1234-ABCD","Q2XX-2345-BACD"]
COLLECT_CAMERAS_SERIAL_NUMBERS = ["*"]

# Array of zone id, all is *. eg ["*"] or ["1234567890","012345678"]
COLLECT_ZONE_IDS = ["*"]

# Motion trigger settings
# Number of concurrent people in frame to start trigger
MOTION_ALERT_PEOPLE_COUNT_THRESHOLD = 1
# Number of MQTT
MOTION_ALERT_ITERATE_COUNT = 4
# Total people detections needed over MOTION_ALERT_ITERATE_COUNT to trigger notification
MOTION_ALERT_TRIGGER_PEOPLE_COUNT = 0
# Time between triggers, in seconds
MOTION_ALERT_PAUSE_TIME = 5

#WebEx Parameters
#
#WEBEXTEAMKEY is either you Personal Access Token or Bot API KEY, and starts with "Bearer "
#https://developer.webex.com/docs/api/v1/people/list-people
WEBEXTEAMKEY = "Bearer ZmIyZTdkZTYtYzQzYi00NjQzLTk3MmUtZjA5ODZlYjc1NGFhNmQwNGVhZjMtMjBi_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f"
#ROOM_ID is the room the script should post to. Must be writable by the API Key above
#https://developer.webex.com/docs/api/v1/rooms/list-rooms
ROOM_ID = "HHHHHHH"