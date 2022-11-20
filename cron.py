from db import connect_db
from main import object_detection
from age import predict_age
import cv2
import requests
from time import sleep
from datetime import datetime, date


db = connect_db()
db_cameras = db.cameras
db_services = db.services
enabled_services = []

services = db_services.find({'status': True})
for val in services:
    enabled_services.append(val['name'])

camera_data = {}
cam_objects = {}

while True:
    cursor = db_cameras.find({'is_active': True})

    for camera in cursor:
        camera_data[str(camera['_id'])] = {}

        if (camera['url'] == '0'):
            url = int(camera['url'])
        
        ages = []
        cam = cv2.VideoCapture(url)
        ret, frame = cam.read()
        finded, frame = object_detection(frame)
        camera_data[str(camera['_id'])]['finded'] = finded
        if ('Age Recognition' in enabled_services or 'Child Recognition' in enabled_services):
            for key in finded:
                if (key != 0):
                    continue
                coords = finded[key]
                age = predict_age(frame[coords[1]: coords[1] + coords[3], coords[0]: coords[0] + coords[2]])
                if (age == None):
                    continue
                
                ages.append(age)
        child_count = None
        if ('Child Recognition' in enabled_services):
            child_count = ages.count('(0, 2)') + ages.count('(4, 6)') + ages.count('(8, 12)') + ages.count('(15, 20)')
        
        week_day = None
        if ('Accounting for the day of the week' in enabled_services):
            week_day = datetime.weekday(datetime.now())
        
        is_holiday = None
        if ('Accounting for holidays' in enabled_services):
            today = date.today()
            holiday = requests.get('https://isdayoff.ru/api/getdata?year=' + str(today.year) + '&month=' + str(today.month) + '&day=' + str(today.day))
            is_holiday = holiday.text

