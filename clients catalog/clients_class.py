import json

class PlatformsCatalog():
    def __init__(self, db_filename="database/platforms.json"):
        self.db_filename=db_filename
        self.content=json.load(open(self.db_filename,"r"))
        
    def set_value(self,platform_ID,field,value):
        platform=self.find_platform(platform_ID)
        platform[field]=value
        
        
    def find_platform(self,platform_ID):
        notFound=1
        for platform in self.content['platforms']:
            if platform['platform_ID']==platform_ID:
                notFound=0
                break
        if notFound==1:
            return False
        else:
            return platform
    def save(self):
        with open(self.db_filename,'w') as file:
            json.dump(self.content,file, indent=4)
        
class UsersCatalog():
    def __init__(self, db_filename="database/users.json"):
        self.db_filename=db_filename
        self.content=json.load(open(self.db_filename,"r"))
        self.createDict()
        
    def createDict(self):
        d = self.content['users']
        self.userpassdict = dict((i["username"],["password"]) for i in d)
        
    def find_user(self,username):
        notFound=1
        for user in self.content['users']:
            if user.get('username').lower()==username.lower():
                notFound=0
                break
        if notFound==1:
            return False
        else:
            return user
        
    def login(self,username,password):
        user=self.find_user(username)
        if user is not False and user['password']==password:
            return user
        else:
            return False  
        
    def removePlatform(self,username,platform_ID):
        user=self.find_user(username)
        if user is not False:
            try:
                user['platforms_list'].remove(platform_ID)
                return True
            except Exception as e:
                return False
        else:
            return False
    
    def removeUser(self,username):
        user=self.find_user(username)
        if user is not False:
            try:
                self.content['users'].remove(user)
                return True
            except Exception as e:
                return False
        else:
            return False
        
    def save(self):
        self.createDict()
        with open(self.db_filename,'w') as file:
            json.dump(self.content,file, indent=4)
    

class ClientsCatalog():
    def __init__(self, db_filename):
        self.db_filename=db_filename
        self.clientsContent=json.load(open(self.db_filename,"r"))
        self.users=UsersCatalog()
        self.platforms=PlatformsCatalog()
        
    def check_registration(self,username,platform_ID):
        if self.users.find_user(username) is not False:
            return "user"
        platform=self.platforms.find_platform(platform_ID)
        if platform is not False:
            if platform['associated']:
                return "associated"
            else:
                return False
        else:
            return "platform"
            
            
        









