#coding=utf8
import socketserver
import struct
import json,os
import configparser
from conf import setting
from lib import client

class FtpHandler(socketserver.BaseRequestHandler):
    '''
    sockerserver多线程类
    '''
    def ser_recv(self):
        '''
        接受客户端数据
        :return: 返回客户端发给来的字典
        '''
        try:
            length = struct.unpack('i',self.request.recv(4))[0]
            return json.loads(self.request.recv(length).decode('utf8'))
        except Exception as e:
            print(e)
            return False
    def ser_resphone(self,data):
        '''
        给客户端相应的函数
        :param data:
        :return:
        '''
        data = json.dumps(data).encode('utf-8')
        length = struct.pack('i',len(data))
        self.request.send(length)
        self.request.sendall(data)

    def handle(self):
        '''
        通信循环，获取客户端发过来的字典，通过字典中的action来判断功能，用hasattr/getattr来分发功能
        :return:
        '''
        while True:
            data = self.ser_recv()
            if not data: break
            if data.get("action") is not None:
                if hasattr(self,data.get("action")):
                    func = getattr(self,data["action"])
                    func(**data)
                else:
                    print("无效的操作")
            else:
                print("无效的操作!")

    def auth(self,**data):
        username = data["username"]
        password = data["password"]
        user = self.authenticate(username,password)
        if user:
            res = {
                "status_code": 254,
                'bash': self.user.get_bash()
            }
        else:
            res = {
                "status_code":253,
            }
        self.ser_resphone(res)

    def authenticate(self,username,password):
        cfg = configparser.ConfigParser()
        cfg.read(setting.ACCOUNT_PATH)
        if username in cfg.sections() and password == cfg[username]["password"]:
            self.user = client.Client(username,password,cfg[username]['home'],cfg[username]['homemaxsize'])
            return username

    def cd(self,**data):
        if data["dirname"] == ".":
            res = {"bash":self.user.get_bash()}
        elif data["dirname"] == "..":
            if len(self.user.path) > 1:
                self.user.path.pop()
            os.chdir(self.user.get_path())

            res = {"bash":self.user.get_bash()}
        else:
            self.user.path.append(data["dirname"])
            os.chdir(self.user.get_path())
            res = {"bash":self.user.get_bash()}
        self.ser_resphone(res)

    def ls(self,**data):
        pwd = self.user.get_path()
        if data["dirname"] == "." :
            new_path = pwd
        else:
            new_path = os.path.join(pwd, data["dirname"])
        if (data["dirname"] == ".") or (os.path.exists(new_path)):
            listdir = os.listdir(new_path)
            res = {
                "status_code":901,
                "data" : listdir
            }
        else:
            res = {
                "status_code": 903,
                "data": "该目录不存在"
            }

        self.ser_resphone(res)




    def wget(self,**data):
        file_name = os.path.basename(data["filename"])
        file_path = os.path.join(self.user.get_path(),data["filename"])
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                self.ser_resphone({"status_code": 901,"filesize":os.path.getsize(file_path)})
                if self.request.recv(1).decode("utf8") == "1":
                    with open(file_path,'rb') as f:
                        while True:
                            data = f.read(4096)
                            if not data: break
                            self.request.send(data)
                return

        return self.ser_resphone({"status_code":256})


    def put(self,**data):
        file_name = data['filename']
        file_size = data['filesize']
        if self.user.free < file_size/1024/1024:
            return self.ser_resphone({"status_code": 259})

        target_path = data['target_path']

        if target_path == '.':
            abs_path = os.path.join(self.user.get_path(),file_name)
        else:
            abs_path = os.path.join(self.user.get_path(),target_path,file_name)

        has_received = 0
        if os.path.exists(abs_path):
            file_has_size = os.path.getsize(abs_path)
            if file_has_size < file_size:
                #断点续传
                self.ser_resphone({"status_code":800})
                client_choice = self.ser_recv()
                if client_choice["choice"] == "Y":
                    self.ser_resphone({"has_received":file_has_size})
                    f = open(abs_path,"ab")
                    has_received += file_has_size
                else:
                    f = open(abs_path,"wb")
            else:
                return self.ser_resphone({"status_code":801})

        else:
            self.ser_resphone({"status_code":802})
            f = open(abs_path,"wb")


        while has_received < file_size:
            data = self.request.recv(1024)
            f.write(data)
            has_received += len(data)

        f.close()



    def mkdir(self,**data):
        dir_list = data["dirname"]
        for i in dir_list:
            try:
                os.makedirs(os.path.join(self.user.get_path(),i))
            except FileExistsError as e:
                print(e)
                res = {"status_code":902}
                return self.ser_resphone(res)

        res = {"status_code":901}
        self.ser_resphone(res)

    def rm_handle(self,**data):
        recv_data = data
        basedir = self.user.get_path()
        if data["action"] == "userdel": basedir = setting.HOME_PATH
        for i in recv_data["dirname"]:
            path = os.path.join(basedir,*data["path"],i)
            print(path)
            if os.path.exists(path):
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    data["dirname"] =[i for i in os.listdir(path)]
                    data["path"].append(i)
                    self.rm_handle(**data)
                    data["path"].pop()
                    os.rmdir(path)
            else:
                return  {"status": 904 ,"dirname":i}
        return {"status": 901}

    def rm(self,**data):
        data["path"] = []
        res = self.rm_handle(**data)
        self.ser_resphone(res)


    def useradd(self,**data):
        config = configparser.ConfigParser()
        code = self.useradd_verify_argv(config,**data)
        if code == 803 or code == 804:return self.ser_resphone({"status_code":code})
        del data["action"]
        config[data["username"]] = data
        if not os.path.exists(os.path.join(setting.HOME_PATH,data['home'])): os.mkdir(os.path.join(setting.HOME_PATH,data['home']))
        with open(setting.ACCOUNT_PATH, 'w') as configfile:
            config.write(configfile)
        self.ser_resphone({"status_code": code})

    def useradd_verify_argv(self,conf,**data):
        conf.read(setting.ACCOUNT_PATH)
        if data["action"] == "useradd":
            if data["username"] in conf.sections():
                return 803
            for i in conf.sections():
                if data["home"] == conf[i]["home"]:
                    return 804
            return 901
        elif data["action"] == "usermod":
            if data["username"] in conf.sections():
                if data["password"] is None:
                    data["password"] = conf[data["username"]]["password"]
                print(data["home"],conf[data["username"]]["home"])
                if data["home"] != conf[data["username"]]["home"]:
                    for i in conf.sections():
                        if data["home"] == conf[i]["home"]:
                            return 804
                del data["action"]
                return 901, data
            else:
                return 805
        else:
            if data["username"] in conf.sections():
                return 901
            else:
                return 805


    def usermod(self,**data):
        config = configparser.ConfigParser()
        code = self.useradd_verify_argv(config, **data)
        if code == 805 or code == 804 : return self.ser_resphone({"status_code": code})
        if not os.path.exists(os.path.join(setting.HOME_PATH,data['home'])): os.mkdir(os.path.join(setting.HOME_PATH, data['home']))
        config[data["username"]] = code[1]
        with open(setting.ACCOUNT_PATH, 'w') as configfile:
            config.write(configfile)
        self.ser_resphone({"status_code": code[0]})

    def userdel(self,**data):
        config = configparser.ConfigParser()
        config.read(setting.ACCOUNT_PATH)
        code = self.useradd_verify_argv(config, **data)
        if code == 805 : return self.ser_resphone({"status_code": code})
        self.ser_resphone({"status_code": code})
        choice = self.request.recv(1).decode('utf8')
        if choice == "Y":
            home = config[data["username"]]["home"]
            self.rm_handle(**{"dirname":[home],"action":"userdel","path":[]})
        config.remove_section(data["username"])
        config.write(open(setting.ACCOUNT_PATH, 'w'))




