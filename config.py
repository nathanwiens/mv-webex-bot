#Meraki MV Parameters
# 
MQTT_SERVER = "10.1.1.221"
MERAKI_API_KEY = "XXXXXXXXXXX"
NETWORK_ID = "YYYYYYYYYYYYY"

# Array of MV serial numbers
COLLECT_CAMERAS_SERIAL_NUMBERS = ["*"]
# Array of zone id, all is *. eg ["*"]
COLLECT_ZONE_IDS = ["*"]

# Motion trigger settings
# Number of concurrent people in frame to start trigger
MOTION_ALERT_PEOPLE_COUNT_THRESHOLD = 1
# Number of MQTT
MOTION_ALERT_ITERATE_COUNT = 4
# Total people detections needed over MOTION_ALERT_ITERATE_COUNT to trigger notification
MOTION_ALERT_TRIGGER_PEOPLE_COUNT = 0
# Time between triggers, in seconds
MOTION_ALERT_PAUSE_TIME = 15

#WebEx Parameters
#
#WEBEXTEAMKEY is either you Personal Access Token or Bot API KEY, and starts with "Bearer "
#https://developer.webex.com/docs/api/v1/people/list-people
#Currently uses WebEx Bot: mvnotify@webex.bot
WEBEXTEAMKEY = "Bearer ZmIyZTdkZTYtYzQzYi00NjQzLTk3MmUtZjA5ODZlYjc1NGFhNmQwNGVhZjMtMjBi_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f"

#ROOM_ID is the room the script should post to. Must be writable by the API Key above
#https://developer.webex.com/docs/api/v1/rooms/list-rooms
#Add the bot to a room, then get the Room ID and paste below
ROOM_ID = "ZZZZZZZZZZZZZZZZ"
