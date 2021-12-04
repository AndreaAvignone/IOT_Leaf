import cherrypy
import json
import requests
import time
import datetime
import sys
from serverClass import *
from generic_service import *
#from conf.simplePublisher import *

class ResourcesServerREST(object):
    exposed=True
    def __init__(self,conf_filename,db_filename):
        self.catalog=ResourceService(conf_filename,db_filename)
        self.service=self.catalog.registerRequest()

    def GET(self,*uri,**params):
        uriLen=len(uri)
        if uriLen!=0:
            info=uri[0]
            platform= self.catalog.retrievePlatform(info)
            if platform is not False:
                if uriLen>1:
                    roomInfo= self.catalog.retrieveRoomInfo(info,uri[1])
                    if roomInfo is not False:
                        if uriLen>2:
                            deviceInfo=self.catalog.retrieveDeviceInfo(info,uri[1],uri[2])
                            if deviceInfo is not False:
                                if uriLen>3:
                                    output=deviceInfo.get(uri[3])
                                elif len(params)!=0:
                                    parameter=str(params['parameter'])
                                    parameterInfo=self.catalog.retrieveParameterInfo(info,uri[1],uri[2],parameter)
                                    if parameterInfo is False:
                                        output=None
                                    else:
                                        output=parameterInfo
                                else:
                                    output=deviceInfo

                            else:
                                output=roomInfo.get(uri[2])

                        elif len(params)!=0:
                            parameter=str(params['parameter'])
                            parameterInfo=self.catalog.findParameter(info,uri[1],parameter)
                            if parameterInfo is False:
                                output=None
                            else:
                                output=parameterInfo

                        else:
                            output=roomInfo
                    else:
                        output=platform.get(uri[1])
                else:
                    output=platform
            else:
                output=self.catalog.db_content.get(info)
            if output==None:
                raise cherrypy.HTTPError(404,"Information Not found")

        else:
            output=self.catalog.db_content['description']

        return json.dumps(output) 

    def PUT(self,*uri):
        body=cherrypy.request.body.read()
        json_body=json.loads(body.decode('utf-8'))
        command=str(uri[0])
        saveFlag=False
        """
        if command=='insertPlatform':
            requestClients=requests.get(self.catalog.serviceCatalogAddress+"/clients_catalog").json()
            platform_ID=json_body['platform_ID']
            if(requests.get(requestClients['url']+'/checkAssociation/'+platform_ID).json()):
                rooms=[]
                newPlatform=self.catalog.insertPlatform(platform_ID,rooms)
                if newPlatform==True:
                    output="Platform '{}' has been added to Resource Catalog\n".format(platform_ID)
                    res={"result":True}
                    saveFlag=True
                        
                else:
                    output="'{}' already exists!".format(platform_ID)
                    res={"result":True}
                    #platform=self.catalog.retrievePlatform(platform_ID)
                    #platform['local_IP']=json_body['local_IP']
            else:
                output="'{}' cannot be connected".format(platform_ID)
                res={"result":False}
        """    
        if command=='insertRoom':
            platform_ID=uri[1]
            room_ID=json_body['room_ID']
            room_name=json_body['room_name']
            platformFlag=self.catalog.retrievePlatform(platform_ID)
            if platformFlag is False:
                requestClients=requests.get(self.catalog.serviceCatalogAddress+"/clients_catalog").json()
                if(requests.get(requestClients['url']+'/checkAssociation/'+platform_ID).json()["result"]):
                    rooms=[]
                    newPlatform=self.catalog.insertPlatform(platform_ID,rooms)
                else:
                    res={"result":False}
                    raise cherrypy.HTTPError(400,"Platform Not valid")
                    
            room=self.catalog.insertRoom(platform_ID,room_ID,json_body)
            if room is False:
                output="Platform '{}' - Room '{}' already exists. Resetted...".format(platform_ID,room_ID)
            else:
                output="Platform '{}' - Room '{}' has been added to Server".format(platform_ID, room_ID)
            res={"result":True}
            saveFlag=True
                    
        elif command=='insertDevice':
            platform_ID=uri[1]
            room_ID=uri[2]
            device_ID=json_body['device_ID']
            platformFlag, roomFlag, newDevice=self.catalog.insertDevice(platform_ID,room_ID,device_ID,json_body)
            if platformFlag is False:
                raise cherrypy.HTTPError(404,"Platform Not found")
            if roomFlag is False:
                raise cherrypy.HTTPError(404,"Room Not found")
            else:
                if newDevice==True:
                    output="Platform '{}' - Room '{}' - Device '{}' has been added to Server".format(platform_ID, room_ID,device_ID)
                    self.catalog.dateUpdate(self.catalog.retrieveRoomInfo(platform_ID,room_ID))
                    saveFlag=True
                else:
                    output="Platform '{}' - Room '{}' - Device '{}' already exists. Updating...".format(platform_ID,room_ID,device_ID)
        elif command=='insertValue':
            platform_ID=uri[1]
            room_ID=uri[2]
            device_ID=uri[3]
            try:
                newValue=self.catalog.insertDeviceValue(platform_ID, room_ID, device_ID,json_body)
                output="Platform '{}' - Room '{}' - Device '{}': parameters updated".format(platform_ID, room_ID, device_ID)
                request=requests.get(server.serviceCatalogAddress+"/broker").json()
                IP=request.get('IP_address')
                port=request.get('port')
                publisher=MyPublisher("server_v",platform_ID+"/"+room_ID,IP,port)
                publisher.start()
                msg={"parameter":"pmv","value":self.catalog.retrieveRoomInfo(platform_ID,room_ID).get("PMV"),"unit":"","timestamp":json_body['timestamp']}
                publisher.myPublish(json.dumps(msg))
                time.sleep(0.4)
                publisher.stop()
            except:
                output=None
            saveFlag=True


        else:
            raise cherrypy.HTTPError(501, "No operation!")
        if saveFlag:
            self.catalog.save()
        if output is not None:
            print(output)
        return json.dumps(res)


    """
    def POST(self, *uri):
        body=cherrypy.request.body.read()
        json_body=json.loads(body.decode('utf-8'))
        command=str(uri[0])
        saveFlag=False
        if command=='setParameter':
            platform_ID=uri[1]
            room_ID=str(uri[2])
            parameter=json_body['parameter']
            if(parameter=="Icl_clo" or parameter=="M_met"):
                parameter_value=float(json_body['parameter_value'])
            
            else:
                parameter_value=json_body['parameter_value']
            newSetting=self.catalog.setRoomParameter(platform_ID,room_ID,parameter,parameter_value)
            if newSetting==True:
                output="Platform '{}' - Room '{}': {} is now {}".format(platform_ID, room_ID, parameter,parameter_value)
                self.catalog.compute_PMV(platform_ID,room_ID)
                self.catalog.compute_PPD(platform_ID,room_ID)
                request=requests.get(server.serviceCatalogAddress+"/broker").json()
                IP=request.get('IP_address')
                port=request.get('port')
                publisher=MyPublisher("server_p",platform_ID+"/"+room_ID,IP,port)
                publisher.start()
                msg={"parameter":"pmv","value":self.catalog.retrieveRoomInfo(platform_ID,room_ID).get("PMV"),"unit":"","timestamp":time.time()}
                publisher.myPublish(json.dumps(msg))
                time.sleep(0.4)
                publisher.stop()
                saveFlag=True
            else:
                output="Platform '{}' - Room '{}': Can't change {} ".format(platform_ID, room_ID,parameter)
        elif command=="warning":
            platform_ID=uri[1]
            room_ID=str(uri[2])
            status,suggestion=self.catalog.parse_warning(platform_ID,room_ID)
            requestProfiles=requests.get(server.serviceCatalogAddress+"/profiles_catalog").json()
            profilesURL=self.buildAddress(requestProfiles.get('IP_address'),requestProfiles.get('port'),requestProfiles.get('service'))
            
            request=requests.get(server.serviceCatalogAddress+"/broker").json()
            IP=request.get('IP_address')
            port=request.get('port')
            publisher=MyPublisher("server","warning/"+platform_ID+"/"+room_ID,IP,port)
            publisher.start()

            json_body["platform_ID"]=platform_ID
            json_body["room_name"]=requests.get(profilesURL+'/'+platform_ID+"/preferences/"+room_ID).json().get('room_name')
            json_body["message"]=json_body["message"]+" ("+status+") " +"at "+time.strftime('%H:%M')
            json_body["suggestion"]=suggestion
            publisher.myPublish(json.dumps(json_body))
            output="platform_ID\nroom_ID\n"+json.dumps(json_body)
            publisher.stop()

        else:
            raise cherrypy.HTTPError(501, "No operation!")
        if saveFlag:
            self.catalog.save()
        print(output)
    """

    def DELETE(self,*uri):
        saveFlag=False
        uriLen=len(uri)
        if uriLen>0:
            platform_ID=uri[0]
            if uriLen>1:
                room_ID=uri[1]
                if uriLen>2:
                    device_ID=uri[2]
                    removedDevice=self.catalog.removeDevice(platform_ID,room_ID,device_ID)
                    if removedDevice==True:
                        output="Platform '{}' - Room '{}' - Device '{}' removed".format(platform_ID,room_ID,device_ID)
                        self.catalog.dateUpdate(self.catalog.retrieveRoomInfo(platform_ID,room_ID))
                        saveFlag=True
                    else:
                        output="Platform '{}'- Room '{}' - Device '{}' not found ".format(platform_ID,room_ID,device_ID)
                else:
                    requestGrafana=requests.get(self.serviceCatalogAddress+"/grafana_catalog").json()
                    self.grafana_IP=requestGrafana.get('IP_address')
                    self.grafana_port=requestGrafana.get('port')
                    self.grafana_service=requestGrafana.get('service')
                    removedDash=requests.delete(self.buildAddress(self.grafana_IP,self.grafana_port,self.grafana_service)+"/deleteDashboard/"+platform_ID+"/"+room_ID).json()
                    if removedDash['result']:
                        removedRoom=self.catalog.removeRoom(platform_ID,room_ID)
                        if removedRoom==True:

                            output="Platform '{}' - Room '{}' removed".format(platform_ID,room_ID)
                            saveFlag=True
                        else:
                            output="Platform '{}'- Room '{}' not found ".format(platform_ID,room_ID)
                    else:
                        output="Error in removing dashboard"
            else:
                removedPlatform=self.catalog.removePlatform(platform_ID) 
                if removedPlatform==True:
                    output="Platform '{}' removed".format(platform_ID)
                    saveFlag=True
                else:
                    output="Platform '{}' not found ".format(platform_ID)
        else:
            raise cherrypy.HTTPError(501, "No operation!")
        if saveFlag:
            self.catalog.save()
        print(output)


if __name__ == '__main__':
    conf=sys.argv[1]
    db=sys.argv[2]
    server=ResourcesServerREST(conf,db)
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
        }
    }
    cherrypy.tree.mount(server, server.service, conf)
    cherrypy.config.update({'server.socket_host': server.catalog.serviceIP})
    cherrypy.config.update({'server.socket_port': server.catalog.servicePort})
    cherrypy.engine.start()
    cherrypy.engine.block()

