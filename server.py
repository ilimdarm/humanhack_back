from flask import Flask, Response, request
from flask_cors import CORS
from bson.objectid import ObjectId
from datetime import datetime
from bson import json_util
from uuid import UUID
from uuid import uuid4
from db import connect_db
from main import gen
import time

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

db = connect_db()
db_users = db.users
db_cameras = db.cameras
db_services = db.services
db_departments = db.departments


@app.route('/auth', methods=['POST'])
def login():
    body = request.get_json()
    res = db_users.find_one({'login': body['login']})
    data = {}
    if not res:
        data['state'] = 0
        data['msg'] = 'Incorrect login or password'
        return json_util.dumps(data)
    token = uuid4()
    db_users.update_one({'login': body['login']}, {"$set": {'token': token}})
    data['state'] = 1
    data['token'] = token
    return json_util.dumps(data)

@app.route('/check_auth', methods=['POST'])
def check_auth():
    body = request.get_json()
    res = db_users.find_one({'token': UUID(body['token'])})
    data = {}
    if not res:
        data['state'] = 0
        return json_util.dumps(data)
    data['state'] = 1
    return json_util.dumps(data)


@app.route('/video/<id>&<with_objects>')
def video(id, with_objects):
    if (with_objects == 'true'):
        with_objects = True
    else: 
        with_objects = False
    camera = db_cameras.find_one({'_id': ObjectId(id), 'is_active': True})
    if not camera:
        data = {}
        data['state'] = 0
        data['msg'] = 'Camera not found'
        return json_util.dumps(data)
    url = camera['url']
    if (url == '0'):
        url = 0
    return Response(gen(url, with_objects), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_cameras', methods=['GET'])
def get_cameras():
    cursor = db_cameras.find({})
    if not cursor:
        data = {}
        data['state'] = 0
        data['msg'] = 'Cameras not found'
        return json_util.dumps(data)
    res = []
    for camera in cursor:
        camera['_id'] = str(camera['_id'])
        res.append(camera)
    return json_util.dumps(res)

@app.route('/get_services', methods=['GET'])
def get_services():
    cursor = db_services.find({})
    if not cursor:
        data = {}
        data['state'] = 0
        data['msg'] = 'Services not found'
        return json_util.dumps(data)
    res = []
    for service in cursor:
        service['_id'] = str(service['_id'])
        service['last_update'] = datetime.utcfromtimestamp(service['last_update']).strftime('%d-%m-%Y')
        res.append(service)
    return json_util.dumps(res)

@app.route('/update_service', methods=['POST']) 
def update_service():
    body = request.get_json()
    res = db_services.update_one({'_id': ObjectId(body['id'])}, {"$set":  {'status': body['status'], 'last_update': int(time.time())}})
    data = {}
    if not res:
        data['state'] = 0
        data['msg'] = 'Error updating service'
        return json_util.dumps(data)
    
    data['state'] = 1
    return json_util.dumps(data)


@app.route('/get_departments') 
def get_departments():
    cursor = db_departments.find({})
    if not cursor:
        data = {}
        data['state'] = 0
        data['msg'] = 'Departments not found'
        return json_util.dumps(data)
    res = []
    for dep in cursor:
        dep['_id'] = str(dep['_id'])
        res.append(dep)
    return json_util.dumps(res)


@app.route('/get_users') 
def get_users():
    cursor = db_users.find({})
    if not cursor:
        data = {}
        data['state'] = 0
        data['msg'] = 'Departments not found'
        return json_util.dumps(data)
    res = []
    for user in cursor:
        user['_id'] = str(user['_id'])
        user['date'] = datetime.utcfromtimestamp(user['date']).strftime('%d-%m-%Y')
        user['last_date'] = datetime.utcfromtimestamp(user['last_date']).strftime('%d-%m-%Y')
        res.append(user)
    return json_util.dumps(res)


if __name__ == '__main__':
    app.run(port=5000)