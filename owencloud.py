from influxdb import InfluxDBClient
import redis
import requests
from pytz import timezone
from datetime import timedelta
import time
from datetime import datetime

import json

client = InfluxDBClient(host='influxdb', port=8086)
redis_cacher = redis.StrictRedis(host='redis', port=6379, db=1)
#client = InfluxDBClient(host='localhost', port=8086)
#redis_cacher = redis.StrictRedis(host='localhost', port=6379, db=1)
dbs=[]
for db in client.get_list_database():
    dbs.append(db['name'])
if 'sibay' in dbs:
    print ("db exist connecting ..")
    client.switch_database('sibay')
else:
    print ("db not found , creating db..")
    client.create_database('sibay')
    client.switch_database('sibay')


sess=requests.Session()
auth_owen=sess.post('https://api.owencloud.ru/v1/auth/open',json={"login":'login',"password":'111111'}).json()


def device_list():
    r=sess.post('https://api.owencloud.ru/v1/device/index',headers={'Content-Type':'application/x-www-form-urlencoded', 'Authorization': 'Bearer {}'.format(auth_owen['token'])})
    devs={}
    for devices in r.json():
        devs[devices['id']]=devices['name']
    json_objects = json.dumps(devs)
    redis_cacher.set('devlist', json_objects)
    redis_cacher.expire('devlist',43200)
    print(devs)
    return devs

def get_params(device):
    url='https://api.owencloud.ru/v1/device/'+str(device)
    data = sess.post(url, headers={'Content-Type':'application/x-www-form-urlencoded', 'Authorization': 'Bearer {}'.format(auth_owen['token'])})
    try:
        json_objects = json.dumps(data.json()['parameters'])
        redis_cacher.set(device, json_objects)
        redis_cacher.expire('devlist', 43200)
        return data.json()['parameters']
    except:
        return 0
        redis_cacher.set(device, 0)
        redis_cacher.expire('devlist', 43200)




def get_param_data(params_ids):
    payload = {"ids": params_ids}
    data=sess.post('https://api.owencloud.ru/v1/parameters/last-data',headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(auth_owen['token'])},json=payload)
    return data.json()




def sensors_task_SO2():
    response_list = []
    response_list_clear = []
    response_json={}
    if redis_cacher.exists('devlist'):
        devlist = json.loads(redis_cacher.get('devlist').decode('utf8'))
    else:
        devlist=device_list()
    for dev in devlist.keys():
        response_json = {}
        if redis_cacher.exists(dev):
            getparams = json.loads(redis_cacher.get(dev).decode('utf8'))
        else:
            getparams = get_params(dev)
        #print(getparams)
        if getparams !=0:
            for p in getparams:
                ids = []
                tags={}
                fields={}
                if p['name'] == "Значение float 1":
                    ids.append(p['id'])
                    param_data=get_param_data(ids)
                    if param_data[0]['values']:
                        if not "Ошибка" in param_data[0]['values'][0]['f']:
                            response_json['measurement']="SO2"
                            tags["id_device"]=dev
                            tags['street'] = devlist[dev]
                            response_json['tags']=tags
                            fields['value'] = float(param_data[0]['values'][0]['f'])
                            response_json['fields']=fields
                            utc = datetime.utcfromtimestamp(int(param_data[0]['values'][0]['d']))
                            response_json['time'] = utc.replace(tzinfo=timezone('UTC')).isoformat()
            response_list.append(response_json)
    for resp in response_list:
        if not resp:
            pass
        else:
            response_list_clear.append(resp)
    json_objects = json.dumps(response_list_clear)
    return response_list_clear



def sensors_task_CH2O():
    response_list = []
    response_list_clear = []
    response_json={}
    if redis_cacher.exists('devlist'):
        devlist = json.loads(redis_cacher.get('devlist').decode('utf8'))
    else:
        devlist=device_list()
    for dev in devlist.keys():
        response_json = {}
        if redis_cacher.exists(dev):
            getparams = json.loads(redis_cacher.get(dev).decode('utf8'))
        else:
            getparams = get_params(dev)
        #print(getparams)
        if getparams !=0:
            for p in getparams:
                ids = []
                tags={}
                fields={}
                if p['name'] == "Значение float 2":
                    ids.append(p['id'])
                    param_data=get_param_data(ids)
                    if param_data[0]['values']:
                        if not "Ошибка" in param_data[0]['values'][0]['f']:
                            response_json['measurement']="CH2O"
                            tags["id_device"]=dev
                            tags['street'] = devlist[dev]
                            response_json['tags']=tags
                            fields['value'] = float(param_data[0]['values'][0]['f'])
                            response_json['fields']=fields
                            utc = datetime.utcfromtimestamp(int(param_data[0]['values'][0]['d']))
                            response_json['time'] = utc.replace(tzinfo=timezone('UTC')).isoformat()
            response_list.append(response_json)
    for resp in response_list:
        if not resp:
            pass
        else:
            response_list_clear.append(resp)
    json_objects = json.dumps(response_list_clear)
    return response_list_clear


try:
    json_body=sensors_task_SO2()
    client.write_points(json_body)
except:
    print("SO2 error")
try:
    json_body=sensors_task_CH2O()
    client.write_points(json_body)
except:
    print("CH2O error")
#print(json_body)
#results=client.query('SELECT "value" FROM "sibay"."autogen"."SO2" WHERE time > now() - 4d GROUP BY "id_device"')
#print(results.raw)
#points=results.get_points(tags={'id_device':'84122'})
#for point in points:
#   print("Time: %s, value: %f" % (point['time'], point['value']))

