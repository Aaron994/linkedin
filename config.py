#encoding: utf-8
import os
DEBUG = True

#数据库的参数
SECRET_KEY = os.urandom(24)

DIALECT = 'mysql'
DRIVER = 'mysqldb'
USERNAME = 'root'
PASSWORD = ''
HOST = 'localhost'
PORT = '3306'
DATABASE = 'users'


SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost:3306/users?charset=utf8'
SQLALCHEMY_TRACK_MODIFICATIONS = False

#自动发邮件的参数
MAIL_SERVER='smtp.qq.com'
MAIL_PORT = 465
MAIL_USERNAME = '1192558663@qq.com'
MAIL_PASSWORD = 'xfwpfvnmsaqjibdf'
MAIL_USE_TLS= False
MAIL_USE_SSL = True #原文出自【易百教程】，商业转载请联系作者获得授权，非商业请保留原文链接：https://www.yiibai.com/flask/flask_mail.html

