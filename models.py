# 用户信息
from datetime import datetime
from db import db
# from sqlalchemy.orm import relationship
# from sqlalchemy import ForeignKey


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)  # 数据库唯识别id
    account = db.Column(db.String(60), nullable=False)  # 登录账号名
    password = db.Column(db.String(60))
    level = db.Column(db.SmallInteger)  # 会员等级
    reg_time = db.Column(db.DateTime, default=datetime.now)  # 普通会员注册时间
    vipTime = db.Column(db.DateTime, default=datetime.now)  # 高级会员
    diaTime = db.Column(db.DateTime, default=datetime.now)  # 钻石会员
    supTime = db.Column(db.DateTime, default=datetime.now)  # 至尊会员
    my_urn = db.Column(db.String(60), default='0')  # LinkedIn识别码/类似cookie
    img = db.Column(db.String(60), default='0')  # LinkedIn头像
    name = db.Column(db.String(8), default='0')  # 姓名
    public_id = db.Column(db.String(60), default='0')
    first_name = db.Column(db.String(60), default='0')
    last_name = db.Column(db.String(60), default='0')
    isbind = db.Column(db.SmallInteger, default='0')  # 0为没绑定，1为绑定
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 用户数据最后一次修改，识别登陆有效期
    # LinkedIn公开id
    login_code = db.Column(db.String(60))  # 每次登录的设备识别码

    userlogs=db.relationship('Userlog')
    groups=db.relationship('Group')
    messs=db.relationship('Mess')
    friends=db.relationship('Friend')
    groupconents=db.relationship('Groupcontent')

    def __init__(self, account, password):
        self.account = account
        self.password = password

    # def __repr__(self):
    #    return {'id':self.id,
    #            'account':self.account,
    #            'level':self.level,
    #            'reg_time':self.reg_time,
    #            'vipTime':self.vipTime,
    #            'diaTime':self.diaTime,
    #            'supTime':self.supTime,
    #            'my_urn':self.my_urn,
    #            'img':self.img,
    #            'name':self.name,
    #            'public_id':self.public_id,
    #            'login_code':self.login_code}


#
class Userlog(db.Model):
    __tablename__ = 'userlog'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)  # 数据库唯识别id
    account = db.Column(db.String(60), db.ForeignKey('user.account'))
    log_date = db.Column(db.String(20))
    send_num = db.Column(db.Integer)
    dig_num = db.Column(db.Integer)
    add_num = db.Column(db.Integer)
    thumbs_num = db.Column(db.Integer)

    def __init__(self, log_date):
        self.log_date = log_date  # time.strftime("%Y-%m-%d", time.localtime())


class Group(db.Model):
    __tablename__ = 'group'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)  # 数据库唯识别id
    account = db.Column(db.String(60), db.ForeignKey('user.account'))
    group_name = db.Column(db.String(60))
    group_id = db.Column(db.String(60))
    sort = db.Column(db.String(5))


    def __init__(self, group_name, group_id):
        self.group_name = group_name
        self.group_id = group_id


class Friend(db.Model):  # 每个组的信息
    __tablename__ = 'friend'
    account = db.Column(db.String(60), db.ForeignKey('user.account'))
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)  # 数据库唯识别id
    group_name=db.Column(db.String(60))
    group_id= db.Column(db.String(60))
    school = db.Column(db.String(17))
    company = db.Column(db.String(17))
    urn = db.Column(db.String(20))
    public_id = db.Column(db.String(20))
    city = db.Column(db.String(20))
    industry = db.Column(db.String(20))
    about = db.Column(db.String(20))
    country = db.Column(db.String(20))
    firstname = db.Column(db.String(20))
    img = db.Column(db.String(20))
    twitter = db.Column(db.String(20))
    websites = db.Column(db.String(20))
    tag = db.Column(db.String(20))  # group 为未分组；friend为已经分组的
    remark = db.Column(db.String(20))  # 备注
    send_time = db.Column(db.String(20))  # 群发记录 2021-02-01
    dig_state = db.Column(db.String(20))  # 是否挖掘过 状态码1/0
    is_prohibit = db.Column(db.String(20))  # 状态码 1/0   0为没有禁发
    send_queue = db.Column(db.String(20))  # 1/0
    # state=db.Column(db.String(20)) # 是否被禁发
    connected = db.Column(db.String(3))  # 是否成功添加好友

    def __init__(self, urn, public_id, firstName, lastName, img, connected, position):
        self.urn = urn
        self.public_id = public_id
        self.firstName = firstName
        self.lastName = lastName
        self.img = img
        self.connected = connected
        self.position = position


class Groupcontent(db.Model):  # 群发内容
    __tablename__ = 'groupcontent'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)  # 数据库唯识别id
    account = db.Column(db.String(60), db.ForeignKey('user.account'))
    tiding = db.Column(db.String(300))
    tiding_id = db.Column(db.String(15))
    is_select = db.Column(db.String(2))  #

    def __init__(self, tiding, tiding_id):
        self.tiding = tiding
        self.tiding_id = tiding_id


class Mess(db.Model):
    __tablename__ = 'mess'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)  # 数据库唯识别id
    account = db.Column(db.String(60), db.ForeignKey('user.account'))
    mess_id = db.Column(db.String(15))
    mess = db.Column(db.String(15))
    is_select = db.Column(db.String(2))

    def __init__(self, mess, mess_id):
        self.mess = mess
        self.mess_id = mess_id

# class Friends(db.Model):
#     __tablename__='friends'
#     id = db.Column(db.Integer, autoincrement=True, primary_key=True)  # 数据库唯识别id
#     account = db.Column(db.String(17), db.ForeignKey('users.account'))# 哪个账号的好友
#     my_urn = db.Column(db.String(60), db.ForeignKey('users.my_urn'))  # LinkedIn识别码/类似cookie  哪个LinkedIn账号的好友
#     phone=db.Column(db.String(30))
#     ims=db.Column(db.String(30))
#     email=db.Column(db.String(30))
#     address=db.Column(db.String(60))
#     school=db.Column(db.String(17))
#     company=db.Column(db.String(17))
#     urn=db.Column(db.String(20))
#     publicId=db.Column(db.String(20))
#     city=db.Column(db.String(20))
#     industry=db.Column(db.String(20))
#     about=db.Column(db.String(20))
#     country=db.Column(db.String(20))
#     firstname=db.Column(db.String(20))
#     lastname=db.Column(db.String(20))
#     position=db.Column(db.String(40))
#     img=db.Column(db.String(20))
#     twitter=db.Column(db.String(20))
#     websites=db.Column(db.String(20))
#     tag=db.Column(db.String(20))
