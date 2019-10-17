
import optparse
from src import server_handler
import socketserver
from conf.setting import *

class ArgvHandler():
    '''
    参数处理类，
    使用optparse.OptionParser来处理参数
    '''
    def __init__(self):
        self.op = optparse.OptionParser()
        options,argv = self.op.parse_args()
        self.verify_argv(options,argv)

    def verify_argv(self,options,argv):
        '''
        验证参数函数，通过获取的argv 参数，然后利用hasattr和getattr反射功能来分发功能，比如 start 、help等
        :param options:
        :param argv:
        :return:
        '''
        cmd = argv[0]

        if hasattr(self,cmd):
            func = getattr(self,cmd)
            func()
        else:
            print("参数错误!")

    def start(self):
        '''
        服务启动功能
        :return:
        '''
        print("server is working...")
        s = socketserver.ThreadingTCPServer((IP,PORT), server_handler.FtpHandler)
        s.serve_forever()

    def help(self):
        pass