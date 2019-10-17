import os
from conf import setting

'''
服务端处理客户的类

'''

class Client:

    def __init__(self,user,passwd,home,maxsize):
        '''

        :param user:    用户名
        :param passwd:  密码
        :param home:    家目录
        :param maxsize: 家目录空间大小
        self.basedir ftp的根目录，所有家目录都是从这个目录开始
        self.path 目录列表，最开始的是家目录，然后添加到列表的是cd的目录，这里就限制了用户的根目录就是自己的家目录
        self.free 表示用户家目录剩余的空间大小
        '''
        self.user = user
        self.passwd = passwd
        self.basedir = setting.HOME_PATH
        self.home = home
        self.path = [self.home]
        self.maxsize = maxsize
        self.free = float(maxsize) - float(self.use_size()/1024)

    def get_bash(self):
        return '%s @ %s >>> :' % (self.user,self.path[-1])


    def use_size(self):
        '''
        用户家目录已使用的大小
        :param path:
        :return:
        '''
        size = 0
        for i in os.listdir(os.path.join(self.basedir,self.home)):
            if os.path.isdir(i):
                size += self.use_size(os.path.join(self.basedir,self.home,i))
            size += os.path.getsize(os.path.join(self.basedir,self.home,i))
        size = float(size/1024)
        #由于系统4K 对齐，所以最小存储单位为 4KB
        res = divmod(size,4)
        if res[1]:
            res = res[0] + 1
        else:
            res = res[0]
        return res

    def get_path(self):
        '''
        获取当前所在目录的绝对路径
        :return:
        '''
        basepath = self.basedir
        for i in self.path:
            basepath = os.path.join(basepath,i)
        return basepath





if __name__ == '__main__':
    c = Client('xie','asd','src',100)
    c.free_size(c.home)