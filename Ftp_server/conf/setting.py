import os
BASEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

IP = '0.0.0.0'
PORT = 8090
HOME_PATH = os.path.join(BASEDIR,'data')
ACCOUNT_PATH = os.path.join(BASEDIR,'conf','account.cfg')

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

    900 :   "md5 valdate success",

    901 :   "OK",

    902 :   "the directory exist!",

    903 :   "the directory not exist!",

    904 :   "No such file or directory"
}