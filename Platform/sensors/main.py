
import time
import sys
import threading
import requests
import json

class SendDataThread(threading.Thread):
    def __init__(self,threadID,sensor):
        threading.Thread.__init__(self)
        self.sensor=sensor
        
    def run(self): 
        while True:
            err_flag=False
            output=self.sensor.retrieveData()
            while err_flag is not True:
                try:
                    self.sensor.publishData(output)
                    err_flag=True
                    time.sleep(self.sensor.time_sleep)
                except:
                    err_flag=False
                    time.sleep(1)
        self.sensor.stop()

class pingThread(threading.Thread):
    def __init__(self,threadID,platform_ID,room_ID,data,catalog_url):
        threading.Thread.__init__(self)
        self.threadID=threadID
        self.platform_ID=platform_ID
        self.room_ID=room_ID
        self.data=data
        self.connection_flag=False
        self.serviceCatalogAddress=catalog_url
        
    def run(self):
        while True:
            print("Pinging the Catalog...")
            while self.pingCatalog() is False:
                print("Failed. New attempt...")
                time.sleep(10)
            print("Device has been registered/updated on Catalog")
            self.connection_flag=True
            time.sleep(60)
    
    
    def pingCatalog(self):
        try:
            catalog=requests.get(self.serviceCatalogAddress+'/resource_catalog').json()['url']
            r=requests.put("{}/insertDevice/{}/{}".format(catalog,self.platform_ID,self.room_ID),data=json.dumps(self.data))
            if r.status_code==200:
                return True
            else:
                return False
        except Exception as e:
            #print(e)
            return False


if __name__ == '__main__':
    #settingFile=sys.argv[1]
    platform_ID=sys.argv[1]
    room_ID=sys.argv[2]
    device_ID=sys.argv[3]
    pin=sys.argv[4]
    
    settingFile="conf/{}_settings.json".format(device_ID)
    serviceCatalogAddress=json.load(open(settingFile,"r"))['service_catalog']
    class_imported=__import__(device_ID+'_class')
    sensor_class=getattr(class_imported,device_ID)
    mqtt_flag=False
    
    while not mqtt_flag:
        try:
            broker=requests.get(serviceCatalogAddress+'/broker').json()
            broker_IP=broker.get('IP_address')
            broker_port=broker.get('port')
            data_topic=broker['topic'].get('data')
            sensor=sensor_class(settingFile,broker_IP,broker_port,data_topic,platform_ID,room_ID,device_ID,pin)
            sensor.start()
            mqtt_flag=True
        except Exception as e:
            print(e)
            print("Can't connect to mqtt broker. New attempt...")
            time.sleep(10)
    time.sleep(1)
    sensor.create_info()
    thread1=pingThread(1,sensor.platform_ID,sensor.room_ID,sensor._data,serviceCatalogAddress)
    time.sleep(1)
    thread1.start()
    thread2=SendDataThread(2,sensor)
    thread2.start()
    

    
    
