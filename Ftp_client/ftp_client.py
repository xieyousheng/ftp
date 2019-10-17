#coding=utf8
import optparse
from socket import *
import json
import os,sys
import struct
import hashlib

STATUS_CODE = {
    250 :   "Invalid cmd format, e.g : {'action':'get','filename':'test.py','size':344}",
    251 :   "Invalid cmd",
    252 :   "Invalid auth data",
    253 :   "Wrong username or password",
    254 :   "Passed authentication",
    255 :   "Filename doesn't provided",
    256 :   "File doesn't exist on server",
    257 :   "Ready to send file",
    258 :   "md5 verification",
    259 :   "Insufficient space left",

    800 :   "the file exist ,but not enough , is continue?",
    801 :   "the file exist!",
    802 :   "ready to receive datas",
    803 :   "User already exists",
    804 :   "This directory is used by other users",
    805 :   "This user does not exist",
    806:    "Delete home directory or not",

    900 :   "md5 valdate success",
    901: "OK",
    902: "the directory exist!"
}

class ClientHandler():
    def __init__(self):
        '''
        初始化，通过make_connection()得到一个socket连接，
        然后执行handler通信处理函数
        '''
        self.op = optparse.OptionParser()
        self.op.add_option('-s','--server',dest="server",help="server name or server ip")
        self.op.add_option('-P', '--port', dest="port", help="server port（0-65535）")
        self.op.add_option('-u', '--username', dest="username", help="username")
        self.op.add_option('-p', '--password', dest="password", help="password")
        self.options,self.argv = self.op.parse_args()
        self.main_path = os.path.dirname(os.path.abspath(__file__))
        self.verify_argv(self.options,self.argv)
        self.make_connection()
        self.handler()

    def handler(self):
        '''
        如果认证通过就进入通信循环，
        接受用户输入的命令，如果是quit或者exit就退出，输入命令为空就跳过此次循环
        根据用户输入的命令通过hasattr与getattr进行分发功能
        如果没有通过，接关闭socket连接
        :return:
        '''
        if self.authenticate():
            while True:
                cmd_info = input(self.pwd).strip()
                if cmd_info == 'quit' or cmd_info == 'exit':exit()
                if not cmd_info: continue
                cmd_list = cmd_info.split()
                if hasattr(self,cmd_list[0]):
                    func = getattr(self,cmd_list[0])
                    func(*cmd_list)
                else:
                    print("无效的命令")
        else:
            self.sock.close()

    def authenticate(self):
        '''
        认证判断用户输入的username和password是否为None
        如果是就提示用户输入，然后进入认证get_auth_result
        如果不是为None就直接认证get_auth_result
        :return:
        '''
        if (self.options.username is None) or (self.options.password is None):
            username = input("username :")
            password = input("password :")
            return self.get_auth_result(username,password)
        return self.get_auth_result(self.options.username,self.options.password)

    def get_auth_result(self,username,password):
        '''
        认证函数
        准备一个字典，字典中的action 是固定的 "auth"对应服务端的auth功能，认证功能字典中应该带有用户名和密码
        把字典传给resphonse功能进行发送给服务端
        通过request功能进行接受服务端发过来的字典
        判断服务端发来的状态码
        如果为254 即  254 :   "Passed authentication" 认证通过，
        就把self.user = username
        self.pwd = 服务端发送过来的路径
        如果不为254，直接输入状态码信息
        :param username:
        :param password:
        :return:
        '''
        data = {
            "action": "auth",
            "username":username,
            "password":password
        }
        self.resphonse(data)
        res = self.request()
        if res['status_code'] == 254:
            self.user = username
            print(STATUS_CODE[res['status_code']])
            self.pwd = res["bash"]
            return True
        else:
            print(STATUS_CODE[res['status_code']])

    def request(self):
        '''
        接受功能函数，
        从服务端接受包的长度，然后再从服务端接受包，这样可以解决粘包的问题，这里包编码前的格式为json
        接收到包之后进行解码，然后把json字符串转为为原有的格式（字典）

        :return:
        '''
        length = struct.unpack('i',self.sock.recv(4))[0]
        data = json.loads(self.sock.recv(length).decode('utf-8'))
        return data

    def resphonse(self,data):
        '''
        发送功能
        把接受到的字典，转换为json字符串然后进行编码
        使用struct.pack封装json字符串的长度
        向服务端发送长度，然后再发送已经编码的json字符串
        :param data:
        :return:
        '''
        data = json.dumps(data).encode('utf8')
        length = struct.pack('i',len(data))
        self.sock.send(length)
        self.sock.send(data)

    def make_connection(self):
        '''
        创建连接
        :return:
        '''
        self.sock = socket(AF_INET,SOCK_STREAM)
        self.sock.connect((self.options.server,int(self.options.port)))

    def verify_argv(self,options,argv):
        '''
        端口参数验证
        :param options:
        :param argv:
        :return:
        '''
        if int(options.port) > 0 and int(options.port) < 65535:
            return True
        else:
            exit("端口范围0-65535")

    def processbar(self,num,total):  # 进度条
        rate = num / total
        rate_num = int(rate * 100)
        is_ok = 0
        if rate_num == 100:
            r = '\r%s>%d%%\n' % ('=' * rate_num, rate_num,)
            is_ok = 1
        else:
            r = '\r%s>%d%%' % ('=' * rate_num, rate_num,)
        sys.stdout.write(r)
        sys.stdout.flush
        return is_ok


    def put(self,*cmd_list):
        cmd_list = cmd_list[1:]
        if not cmd_list:
            print("请输入要上传的文件路径!")
            return
        file_path = os.path.join(self.main_path,cmd_list[0])
        filename = os.path.basename(cmd_list[0])
        filesize = os.path.getsize(file_path)
        data = {
            "action" : "put",
            "filename" : filename,
            "filesize" :filesize
        }
        if len(cmd_list) == 1:
            data['target_path']= "."
        else:
            data['target_path'] = cmd_list[1]

        self.resphonse(data)

        is_exist = self.request()
        f = open(file_path,'rb')
        if is_exist["status_code"] == 802:
            has_received = 0
            f.seek(has_received)

        elif is_exist["status_code"] == 801 or is_exist["status_code"] == 259:
            print(STATUS_CODE[is_exist["status_code"]])
            return
        elif is_exist["status_code"] == 800:
            u_choice = input("the file exist,but not enough,is continue?[Y/N]").strip()
            self.resphonse({"choice": u_choice.upper()[0]})
            if u_choice.upper()[0] == "Y":
                has_received = self.request()['has_received']
                f.seek(has_received)
            else:
                has_received = 0
                f.seek(has_received)

        while has_received < filesize:
            file_data = f.read(1024)
            self.sock.send(file_data)
            has_received += len(file_data)
            self.processbar(has_received,filesize)
        f.close()

        print("put success!")

    def mkdir(self,*cmd_list):
        data = {
            "action" : "mkdir",
            "dirname": cmd_list[1:]
        }
        self.resphonse(data)
        res = self.request()
        if res["status_code"] != 901:
            print(STATUS_CODE[res["status_code"]])

    def rm(self,*cmd_list):
        data = {
            "action":"rm",
            "dirname":cmd_list[1:]
        }
        self.resphonse(data)
        res = self.request()


    def cd(self,*cmd_list):
        if len(cmd_list)==1 : return
        data = {
            "action" : "cd",
            "dirname" : cmd_list[1]
        }
        self.resphonse(data)
        res = self.request()
        self.pwd = res["bash"]

    def ls(self,*cmd_list):
        data = {
            "action": "ls",
        }
        if len(cmd_list) == 1:
            data["dirname"] = "."
        else:
            data["dirname"] = cmd_list[1]
        self.resphonse(data)
        res = self.request()
        if res["status_code"] == 903 :
            print(res["data"])
        else:
            print('\n'.join(res["data"]))

    def useradd(self,*cmd_list):
        if self.user != 'root':
            print("你无权限执行此命令!")
            return
        data = {
            "action" : "useradd",
        }
        data = self.useradd_verify_argv(*cmd_list,**data)
        self.resphonse(data)
        print(STATUS_CODE[self.request()["status_code"]])


    def useradd_verify_argv(self,*cmd_list,**data):
        op = optparse.OptionParser()
        op.add_option('-u', '--username', dest="username")
        op.add_option('-p', '--password', dest="password")
        op.add_option('-d', '--drictory', dest="drictory")
        op.add_option('-m', '--maxsize', dest="maxsize")
        options, argv = op.parse_args(list(cmd_list))
        data["username"] = options.username
        data["password"] = options.password
        data["home"] = options.drictory
        data["homemaxsize"] = options.maxsize
        if data["username"] is None: data["username"] = input("username : ")
        if data["action"] == "useradd":
            if data["password"] is None: data["password"] = input("password : ")
        if data["home"] is None: data["home"] = data["username"]
        if data["homemaxsize"] is None: data["homemaxsize"] = 1000
        return data

    def usermod(self,*cmd_list):
        if self.user != 'root':
            print("你无权限执行此命令!")
            return
        data = {
            "action" : "usermod",
        }
        data = self.useradd_verify_argv(*cmd_list, **data)
        self.resphonse(data)
        print(STATUS_CODE[self.request()["status_code"]])

    def userdel(self,*cmd_list):
        if self.user != 'root':
            print("你无权限执行此命令!")
            return
        data = {
            "action":"userdel",
            "username":cmd_list[1]
        }
        self.resphonse(data)
        res = self.request()
        if res["status_code"] == 805:
            print(STATUS_CODE[res["status_code"]])
            return
        choice = input("Delete home directory or not,Y/N:").strip()
        self.sock.send(choice.upper()[0].encode('utf8'))
        print(STATUS_CODE[res["status_code"]])

    def wget(self,*cmd_list):
        data = {
            "action" : "wget",
        }
        file_path = os.path.dirname(os.path.abspath(__file__))
        if len(cmd_list) == 1:
            print("请输入文件名!")
            return
        elif len(cmd_list) >= 3:
            if os.path.isabs(cmd_list[2]):
                file_path = cmd_list[2]
                if not os.path.exists(cmd_list[2]):
                    print("目标路径不存在!")
                    return
            else:
                file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),cmd_list[2])
                if not os.path.exists(file_path):
                    print("目标路径不存在!")
                    return


        data["filename"] = cmd_list[1]
        self.resphonse(data)
        res = self.request()
        if res["status_code"] == 256:
            print(STATUS_CODE[res["status_code"]])
            return
        try:
            f = open(os.path.join(file_path,os.path.basename(data["filename"])),'wb')

        except PermissionError as e:
            print(e)
            self.sock.send('0'.encode('utf-8'))
            return
        if res["filesize"] == 0 :
            f.close()
            return
        self.sock.send('1'.encode('utf-8'))
        size = 0
        while True:
            file_data = self.sock.recv(4096)
            f.write(file_data)
            size += len(file_data)
            if self.processbar(size,res["filesize"]):
                break

        f.close()








if __name__ == '__main__':
    c = ClientHandler()
    c.handler()