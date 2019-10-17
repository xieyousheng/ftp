import configparser

config = configparser.ConfigParser()

# config["DEFAULT"]= {  }
# config["xie"] =  {
#     'username':'xie',
#     'password':'123',
#     'home':'xie',
#     'homemaxsize':'100'
# }
# config["alex"] = {
#     'username':'alex',
#     'password':'123',
#     'home':'alex',
#     'homemaxsize':'50'
# }
#
# with open('account.cfg', 'w') as configfile:
#    config.write(configfile)
import os,sys

# config.read('account.cfg')
#
# config.remove_section('qwe')
# config.write(open('account.cfg', 'w'))

# print(os.path.getsize('s'))
print(os.path.join('sadsa',*['sad','sadsa']))
