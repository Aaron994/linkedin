import time
from functools import wraps
# from dateutil.parser import parse  # dateutil 中的 parser 模块可以帮我们将几乎任何形式的字符串日期数据解析为datetime 对象
from flask import Flask, render_template, request, redirect, url_for, session
from sqlalchemy import func
from models import User, Group, Userlog, Groupcontent, Mess, Friend
from db import db
# from hashlib import md5
import config
from flask import jsonify
import random
import string
# from flask_mail import Mail, Message

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)

# mail=Mail()
# mail.init_app(app)





# 一次性创建数据库
db.create_all(app=app)

@app.route('/', methods=['GET','POST'])
def homepage():
    return render_template('index.html')

@app.route('/')

@app.route('/register', methods=['GET','POST'])
def register():
    return render_template('register.html')

@app.route('/regist', methods=['POST'])
def regist():
    account=request.form.get('account')
    password=request.form.get('password')
    admin = User(account, password)
    db.session.add(admin)
    db.session.commit()
    return '插入成功'


@app.route('/api/v1.0/actions/login', methods=['POST'])
def login():
    account = request.form.get('account')
    other = request.form.get('other')

    if not User.query.filter_by(account=account).first():  # 验证账号是否存在
        return jsonify({'result': 0})
    info = User.query.filter_by(account=account).first()

    if other == info.password:  # 验证密码是否正确

        # 每次登录都自动生成一个专门的识别码
        login_code = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(20))
        # 保存到服务器
        User.query.filter_by(account=account).first().update({'login_code':login_code})
        db.session.commit()  # 这里是要确认更新

        info = User.query.filter_by(account=account).first()
        data = {'account': info.account,
                'level': info.level,
                'reg_time': func.date_format((info.reg_time), "%Y-%m-%d %H:%i:%s"),  # 时间戳格式化
                'vipTime': func.date_format((info.vipTime), "%Y-%m-%d %H:%i:%s"),
                'diaTime': func.date_format((info.diaTime), "%Y-%m-%d %H:%i:%s"),
                'supTime': func.date_format((info.supTime), "%Y-%m-%d %H:%i:%s"), }
        return jsonify({'result': 1, 'data': data, 'login_code': info.login_code})
    else:  # 密码错误
        return jsonify({'result': 2})

#检查账号，密码，登录超时，没有绑定领英，试用期超过30天等的 装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        account = request.form.get('account')
        my_urn = request.form.get('my_urn')
        login_code = request.form.get('login_code')

        if not account:
            return jsonify({'result': 3})
        update_time=User.query.filter_by(account=account).first().update_time
        if not my_urn:
            return jsonify({'result': 4})
        if time.time()-update_time.timestampe> 86400: #最后一次修改账号的login_code 为最近一次登录，超过一天则为过期
            return jsonify({'result': 5})
        if not User.query.filter_by(login_code=login_code).first():
            return jsonify({'result': 6})
        if User.query.filter_by(account=account).first().level=='0' and time.time() - User.query.filter_by(account=account).first().reg_time.timestamp > 86400 * 30:
            return jsonify({'result': 7})
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/v1.0/actions/bindLinkedin', methods=['POST'])
def bindLinkedin():  # 只需更新信息即可
    other = request.form.get('other')
    data = request.form.get('data')
    account = request.form.get('account')
    if other:  # true,用户想绑定LinkedIn账户,需要更新原先的信息/false 自动绑定
        userinfo = User.query.filter_by(account=account).first()
        userinfo.my_urn = data['my_urn']
        userinfo.public_id = data['public_id']
        userinfo.first_name = data['first_name']
        userinfo.last_name = data['last_name']
        userinfo.img = data['img']
        db.session.commit()
    if request.form.get('tag') == 'bind':
        userinfo = User.query.filter_by(account=account).first()
        userinfo.isbind = '1'
        db.session.commit()
        return jsonify({"result": 1})

    return jsonify({"result": 1})


@app.route('/api/v1.0/actions/probe', methods=['POST'])
@login_required
def probe():    #需要了解调用哪个一个数据库：参数是keyword,country,page
    try:
        account=request.form.get('account')
        if User.query.filter_by(account=account).first().level <2:
            return jsonify({'result':2})
        else:
            return  jsonify({'result':1})
    except:
        return jsonify({'result':0})
#
@app.route('/api/v1.0/actions/getSendForAuto', methods=['POST'])
def getSendForAuto():   #JlHttp('getSendForAuto', send, skip, parseInt(items.s_skip_time))    send 为urn list, skip 为0 不掠过，skip time为掠过的次数
    try:
        infos=[]
        datas=request.form.get("data")
        for data in datas:
            info=Friend.query.filter_by(urn=data).first()
            infos.append({"urn":info.urn,"first_name":info.first_name,"last_name":info.last_name,"img":info.img}
                        )
        return jsonify({'result':1,'data':infos})
    except:
        return jsonify({'result':0})



@app.route('/api/v1.0/actions/getGroup', methods=['POST'])
@login_required
def getGroup():
    try:
        account = request.form.get('account')
        tag = request.form.get('tag')
        data = request.form.get('data')
        from models import User, Group, Userlog, Groupcontent, Mess, Friend
        if data == 1:  # 说明要获取所有的组名和组id
            Group = Group.query.filter_by(account=account).all()
            infos = []
            for group in Group:
                info = {'group_name': group.group_name, 'group_id': group.group_id}
                infos.append(info)
            return jsonify({"result": 1, "data": infos, "tag": tag, "groupId": "1"})
    except:
        return jsonify({'result':0})


@app.route('/api/v1.0/actions/saveTidings', methods=['POST'])
@login_required
def saveTidings():
    try:
        tiding_id = request.form.get('data')
        tiding = request.form.get('other')
        if Groupcontent.query.filtr_by(tiding_id=tiding_id).first():
            info = Groupcontent.query.filtr_by(tiding_id=tiding_id).first()
            info.tiding = tiding  # 此处的令值能否生效
            return jsonify({'result': 2})
        tiding1 = Groupcontent(tiding, tiding_id)
        db.session.add(tiding1)
        db.session.commit()
        return jsonify({'result':1})
    except:
        return jsonify({'result':0})


@app.route('/api/v1.0/actions/getMes', methods=['POST'])
@login_required
def getMes():
    try:
        account = request.form.get('account')
        tag = request.form.get('tag')
        if tag == 'show':  # 获取所有的个性化消息
            infos = Mess.query.filter_by(account=account).all()
            datas = []
            for info in infos:
                data = {"mess_id": info.mess_id, "mess": info.mess, "is_select": info.is_select}
                datas.append(data)
                return jsonify({"result": 1, "data": datas, "tag": "show"})
    except:
        return jsonify({'result': 0})


@app.route('/api/v1.0/actions/selectAllMes', methods=['POST'])
@login_required
def selectAllMes():
    try:
        data = request.form.get('data')
        other = request.form.get('other')
        account = request.form.get('account')
        if data == '1':
            Mess.query.filter_by(account=account).all().update({'is_select': '1'})
            return jsonify({'result': 1,'action':1})
        if data == '0':
            Mess.query.filter_by(account=account).all().update({'is_select': '0'})
            return jsonify({'result':1,'action':0})
    except:
        return jsonify({'result':0})


@app.route('/api/v1.0/actions/selectMes', methods=['POST'])
@login_required
def selectMes():
    data = request.form.get('data')
    other = request.form.get('other')
    # if other=='0':
    #     Mess.query.filter_by(is_select=data).all().update({'is_select': '0'})
    if type(data) == list:
        for dat in data:
            Mess.query.filter_by(mess_id=dat).all().update({'is_select': '1'})
        return jsonify({'result': 1, 'tidings_id': data, 'action': '1'})

    if other == '1':
        Mess.query.filter_by(mess_id=data).first().update({'is_select': '1'})
        return jsonify({'result': 1, 'tidings_id': data, 'action': '1'})
    return jsonify({'result': 0})

@app.route('/api/v1.0/actions/saveThumbsRecord', methods=['POST'])
@login_required
def saveThumbsRecord():
    account = request.form.get('account')
    today = time.strftime("%Y-%m-%d", time.localtime())  # 日期年月日字段
    if Userlog.query.filter_by(account=account, log_date=today).first():
        Userlog.query.filter_by(account=account, log_date=today).first().update(
            {'thumbs_num': Userlog.thumbs_num + 1})
        return jsonify({'result': 1})


@app.route('/api/v1.0/actions/saveFriend', methods=['POST'])
@login_required
def saveFriend():
    try:
        datas=request.form.get('data')  #urn 列表
        finfos=[]

        for data in datas:
            if Friend.query.filter_by(urn=data['entityUrn']).first():
                continue
            else:
                info=Friend(urn=data['entityUrn'],
                             public_id=data['public_id'],
                             firstName=data['firstName'],
                             lastName=data['lastName'],
                             position=data['position'],
                             img=data['img'],
                             connected=data['connected'])
                db.session.add(info)
                db.session.commit()
        for data in datas:
            urn=data['entityUrn']
            finfo=Friend.query.filter_by(urn=urn).first()
            finfo={
                'friend_urn':finfo.urn,
                'dig_state':finfo.state,
                'is_prohibit':finfo.is_prohibit,
                'send_queue':finfo.send_queue,
                'send_time':finfo.send_time,
                'remark':finfo.remark,
                'group_name':finfo.group_name
            }
            finfos.append(finfo)
        return jsonify({"result":1,"data":finfos})
    except:
        return jsonify({'result':0})

@app.route('/api/v1.0/actions/getLog', methods=['POST'])
@login_required
def getLog():
    try:
        account = request.form.get('account')
        datas = Userlog.query.filter_by(account=account).all()
        return jsonify({'result': 1, 'data': datas})
    except:
        return jsonify({'result':0})

@app.route('/api/v1.0/actions/saveRecallRecord', methods=['POST'])
@login_required
def saveRecallRecord():  # 不保留，纯粹查询是否登录

    return jsonify({'result': 1})

@app.route('/api/v1.0/actions/getTidings', methods=['POST'])
@login_required
def getTidings():
    account = request.form.get('account')
    datass = Groupcontent.query.filtr_by(account=account).all()
    return jsonify({'result': 1, 'data': datass})


#
@app.route('/api/v1.0/actions/getDig', methods=['POST'])
@login_required
def getDig():
    account = request.form.get('account')
    my_urn = request.form.get('my_urn')
    login_code = request.form.get('login_code')
    return None

@app.route('/api/v1.0/actions/getSendForFriend', methods=['POST'])
@login_required
def getSendForFriend():
    try:
        infos=[]
        datas=request.form.get("data")
        for data in datas:
            info=Friend.query.filter_by(urn=data).first()
            infos.append({"urn":info.urn,"first_name":info.first_name,"last_name":info.last_name,"img":info.img}
                        )
        tidings=Mess.query.filter_by(is_select='1').all()
        return jsonify({'result':1,'tidings':tidings,'data':infos})
    except:
        return jsonify({'result':0})

@app.route('/api/v1.0/actions/saveProfile', methods=['POST'])
def saveProfile():  #搜索到的好友列表
    try:
        datas=request.form.get('data') #list
        for data in datas:  #{"entityUrn":"ACoAAAFqJEUBxGwuBvEH77mRZqE_nDffRsBcfVs","public_id":"mazda-rezainejad-685b467","firstName":"Mazda","lastName":"Rezainejad","position":"CEO / Owner Royal world glass LLC","img":"https:/rg"}
            if Friend.query.filter_by(urn=data['entityUrn']).first():
                continue
            else:
                info = Friend(urn=data['entityUrn'], public_id=data['public_id'], firstName=data['firstName'],
                               lastName=data['lastName'], position=data['position'], img=data['img'],
                               connected=data['connected'])
                db.session.add(info)
                db.session.commit()
        return jsonify({'result':1})
    except:
        return jsonify({'result':1})

@app.route('/api/v1.0/actions/deleteMes', methods=['POST'])
@login_required
def deleteMes():
    account = request.form.get('account')
    my_urn = request.form.get('my_urn')
    login_code = request.form.get('login_code')

    if request.form.get('other') == '1':
        Mess.query.filter_by(is_select='1').all().delete()
        return jsonify({'result': 1})
    return jsonify({'result': 0})



@app.route('/api/v1.0/actions/saveSendRecord', methods=['POST'])
@login_required
def saveSendRecord():
    try:
        send_time=time.strftime("%Y-%m-%d", time.localtime())
        urn=request.form.get('data')
        Friend.query.filter_by(urn=urn).first.update({'send_time':send_time})
        db.session.commit()
        return jsonify({'result':1})
    except:
        return jsonify({'result':0})

@app.route('/api/v1.0/actions/saveAddRecord', methods=['POST'])
@login_required
def saveAddRecord():
    account=request.form.get('account')
    log_date=time.strftime("%Y-%m-%d", time.localtime())
    if Userlog.query.filter_by(log_date=log_date).first():
        info=Userlog.query.filter_by(log_date=log_date).first().update('')

@app.route('/api/v1.0/actions/saveGroup', methods=['POST'])
@login_required
def saveGroup():
    try:
        data=request.form.get('data')
        other=request.form.get('other')
        if Group.query.filter_by(group_id=data).first():
            info=Group.query.filter_by(group_id=data).first()
            info=info.update({"group_name":other})
            db.session.add(info)
            db.session.commit()
            return jsonify({'result':2})
        else:
            info=Group(group_id=data,group_name=other)
            db.session.add(info)
            db.session.commit()
            return jsonify({'result':1})
    except:
        return jsonify({'result':0})
#
@app.route('/api/v1.0/actions/getLevel', methods=['POST'])
@login_required
def getLevel():
    try:
        account=request.form.get('account')
        info=User.query.filter_by(account=account).first()
        data={
            'account':info.account,
            'reg_time':func.date_format((info.reg_time), "%Y-%m-%d %H:%i:%s"),
            'vip_time':func.date_format((info.vipTime), "%Y-%m-%d %H:%i:%s"),
            'dia_time':func.date_format((info.diaTime), "%Y-%m-%d %H:%i:%s"),
            'sup_time':func.date_format((info.supTime), "%Y-%m-%d %H:%i:%s"),
            'level':info.level
        }
        return jsonify({"result":1,"data":data})
    except:
        return jsonify({'result':0})

@app.route('/api/v1.0/actions/saveMes', methods=['POST'])
@login_required
def saveMes():
    account=request.form.get('account')
    infos=Mess.query.filter_by(account=account).all()
    datas=[]
    for info in infos:
        data={'mess_id':info.mess_id,'mess':info.mess}
        datas.append(data)
    return jsonify({'result':1,'data':datas,'tag':'show'})

@app.route('/api/v1.0/actions/getFriendProfile', methods=['POST'])
@login_required
def getFriendProfile(): #获取单个好友的信息
    try:
        data=request.form.get('data')
        account=request.form.get('account')
        my_urn=request.form.get('my_urn')

        datas=Friend.query.filter_by(account=account,my_urn=my_urn,urn=data).first()
        info=datas.popitem('account').popitem('my_urn')
        return jsonify({"result":1,"data":[{"urn":info}]})
    except:
        return jsonify({'result':0})


@app.route('/api/v1.0/actions/propose', methods=['POST'])
@login_required
def propose():   #试用会员忽略建议
    return jsonify({'result':1})

@app.route('/api/v1.0/actions/editRemark', methods=['POST'])
@login_required
def editRemark():   #修改备注
    try:
        data=request.form.get('data')  # urn
        tag=request.form.get("tag") # f_
        other=request.form.get('other') #remark的内容
        info=Friend.query.filter_by(urn=data).first().update({'remark':other})
        db.session.add(info)
        db.session.commit()
        return jsonify({"result":1,"urn":data,"remark":other,"tag":tag})
    except:
        return jsonify({'result':0})

@app.route('/api/v1.0/actions/getDigForGroup', methods=['POST'])
@login_required
def getDigForGroup():
    try:
        datas=request.form.get('data')
        infos=[]
        for data in datas:
            info=Friend.query.filter_by(urn=data).first()
            info={'urn':info.urn,'public_id':info.public_id,'img':info.img}
            infos.append(info)
        return jsonify({'result':1,'data':infos})
    except:
        return jsonify({'result':0})
#
@app.route('/api/v1.0/actions/getMesForAddFriend', methods=['POST'])
@login_required
def getMesForAddFriend():
    try:
        data=Mess.query.filter_by(is_select='1').first()
        return jsonify({'result':1,'data':data})
    except:
        return jsonify({'result':0})

@app.route('/api/v1.0/actions/grouping', methods=['POST'])
@login_required
def grouping():
    try:
        datas=request.form.get('data') #urn 列表 组成员
        gid=request.form.get('other')# 组 id
        tag=request.form.get('tag')  #  已经分组的为friend, 未分组的group
        for data in datas:
            infos=Friend.query.filter_by(urn=data).first().update({'group_id':gid,'tag':tag})
            db.session.add(infos)
            db.session.commit()
        groupName=Group.query.filter_by(group_id=gid).group_name
        return jsonify({'result':1,'data':datas,'tag':tag,'groupName':groupName})
    except:
        return jsonify({'result':0})
#
@app.route('/api/v1.0/actions/updateProhibit', methods=['POST'])
@login_required
def updateProhibit():  # f_ g_的意思？？？
    try:
        datas=request.form.get('data')
        tag=request.form.get('tag')
        other=request.form.get('other')  #1表示禁发
        for data in datas:
            infos=Friend.query.filter_by(urn=data).first().update({'is_prohibit':other})
            db.session.add(infos)
            db.session.commit()
        return jsonify({'result':1,'friend':datas,'state':other,'tag':tag})
    except:
        return jsonify({'result':0})

@app.route('/api/v1.0/actions/selectAllTidings', methods=['POST'])
@login_required
def selectAllTidings():
    try:
        data=request.form.get('data')  #1
        other=request.form.get("other") # 2
        account=request.form.get('account')
        if data=='1':
            infos=Groupcontent.query.filtr_by(account=account).all().update({'is_select':1})
            db.session.add(infos)
            db.session.commit()
        return jsonify({'result':1,'action':1,'count':other})
    except:
        return jsonify({'result':0})
@app.route('/api/v1.0/actions/deleteInvalidFriend', methods=['POST'])
def deleteInvalidFriend():
    try:
        data=request.form.get('data')
        info=Friend.query.filter_by(urn=data).first()
        db.session.delete(info)
        db.session.commit()
        return None
    except:
        return None

@app.route('/api/v1.0/actions/getSendForGroup', methods=['POST'])
@login_required
def getSendForGroup():
    try:
        data=request.form.get('data')
        tag=request.form.get('tag')
        other=request.form.get('other')

        tidings=[]
        infos=Mess.query.filter_by(is_select='1').all()
        for info in infos:
            tidings.append(info.mess)

        ginfos=Friend.query.filter_by(group_id=data).all()
        datas=[]
        for qinfo in ginfos:
            datas.append({"urn":qinfo.urn,"first_name":qinfo.first_name,"last_name":qinfo.last_name,
                    "img":qinfo.img,})
        return jsonify({
            'result':1,
            'tidings':tidings,
            'data':datas
                    })
    except:
        return jsonify({'result':0})

@app.route('/api/v1.0/actions/deleteTidings', methods=['POST'])
@login_required
def deleteTidings():
    try:
        infos=Groupcontent.query.filtr_by(is_select='1').all().delete()
        db.session.add(infos)
        db.session.commit()
        return jsonify({'result':1})
    except:
        return jsonify({'result':0})

@app.route('/api/v1.0/actions/getAutoDig', methods=['POST'])
def getAutoDig():
    try:
        account=request.form.get('account')
        infos=Friend.query.filter_by(account=account,dig_state='0').all()
        datas=[]
        for info in infos:
            datas.append({
                'urn':info.urn,
                'public_id':info.public_id
            })
        return jsonify({'result':1,'data':datas})
    except:
        return jsonify({'result':0})

@app.route('/api/v1.0/actions/logout', methods=['POST'])
def logout():
    account = request.form.get('account')
    User.query.filter_by(account=account).first().update({'login_code': ""})

    return {'result': 1}

@app.route('/api/v1.0/actions/startAddFriend', methods=['POST'])
@login_required
def startAddFriend():
    try:
        infos=[]
        messs=[]
        datas=request.form.get('data') #urn 列表
        mess=Mess.query.filter_by(is_select='1').all()
        for i in mess:
            messs.append({
                'tidings':i.mess
            })
        for data in datas:
            info=Friend.query.filter_by(urn=data).first()
            infos.append({
                'urn':info.urn,
                'public_id':info.public_id,
                'first_name':info.first_name,
                'last_name':info.last_name,
                'img':info.img
            })
        return jsonify({
            'result':1,
            'mess':messs,
            'data':infos
        })
    except:
        return jsonify({'result':0})



@app.route('/api/v1.0/actions/getDigForFriend', methods=['POST'])
@login_required
def getDigForFriend():
    try:
        datas=request.form.get('data') # list
        infos=[]
        for data in datas:
            info=Friend.query.filter_by(urn=data).first()
            infos.append({
                'urn':info.urn,
                'public_id':info.public_id,
                'img':info.img
            })

    except:
        return jsonify({'result':0})


@app.route('/api/v1.0/actions/sortGroup', methods=['POST'])
@login_required
def sortGroup():
    try:
        datas=request.form.get('data') # [{"groupId":"1584596816750","sort":3},{"groupId":"1584457159345","sort":2},{"groupId":"1584596838038","sort":1}]
        for data in datas:
            info=Group.query.filter_by(group_id=data['groupId']).update({'sort':data['sort']})
            db.session.add(info)
            db.session.commit()
        return jsonify({'result':1})
    except:
        return jsonify({'result':0})

@app.route('/api/v1.0/actions/deleteGroup', methods=['POST'])
@login_required
def deleteGroup():
    try:
        data=request.form.get('data')
        if type(data)== list:
            for dat in data:
                Group.query.filter_by(group_id=dat).first().delete()
                Friend.query.filter_by(group_id=dat).all().delete()

            return jsonify({'result':1})
        else:
            Group.query.filter_by(group_id=data).first().delete()
            Friend.query.filter_by(group_id=data).all().delete()
            return jsonify({'result': 1})
    except:
        return jsonify({'result':0})

@app.route('/api/v1.0/actions/getGroupFriend', methods=['POST'])
@login_required
def getGroupFriend():
    try:
        from models import User, Group, Userlog, Groupcontent, Mess, Friend
        data=request.form.get('data') # {"firstName":"","lastName":"","gid":"1612144508201","start":0,"count":10}
        if data['firstName']:
            infos = Friend.query.filter_by(firstName=data['firstname'],group_id=data['gid']).all()[data['start']:data['count']]

        if data['lastName']:
            infos = Friend.query.filter_by(lastName=data['lastName'],group_id=data['gid']).all()[data['start']:data['count']]
        if not data['firstName'] and not data['lastName']:
            infos = Friend.query.filter_by(group_id=data['gid']).all()[data['start']:data['count']]
        total=len(Friend.query.filter_by(group_id=data['gid']).all())
        pos=data['start']+data['count']
        Friend=[]
        for info in infos:
            friend={"urn":info.urn,"public_id":info.public_id,"first_name":info.first_name,"last_name":info.last_name,
                    "img":info.img,
                "position":info.position,
                    "send_time":info.send_time,
                    "dig_state":info.dig_state,
                    "is_prohibit":info.is_prohibit,
                    "send_queue":info.send_queue,
                   "remark":info.remark}
            Friend.append(friend)
        return jsonify({"result":1,"total":total,"pos":pos,"groupId":data['gid'],"data":Friend})
    except:
        return jsonify({'result':0})

@app.route('/api/v1.0/actions', methods=['POST'])
def actions():
    action = request.form.get('action')

    if action == 'login':
        return redirect(url_for('login'))
    if action == 'bindLinkedin':
        return redirect(url_for('bindLinkedin'))
    if action == 'getMes':
        return redirect(url_for('getMes'))
    if action == 'selectAllTidings':
        return redirect(url_for('selectAllTidings'))
    if action == 'getSendForFriend':
        return redirect(url_for('getSendForFriend'))
    if action == 'getFriendProfile':
        return redirect(url_for('getFriendProfile'))
    if action == 'probe':
        return redirect(url_for('probe'))
    if action == 'getSendForAuto':
        return redirect(url_for('getSendForAuto'))
    if action == 'getGroup':
        return redirect(url_for('getGroup'))
    if action == 'getLog':
        return redirect(url_for('getLog'))
    if action == 'deleteInvalidFriend':
        return redirect(url_for('deleteInvalidFriend'))
    if action == 'saveProfile':
        return redirect(url_for('saveProfile'))
    if action == 'deleteMes':
        return redirect(url_for('deleteMes'))
    if action == 'propose':
        return redirect(url_for('propose'))
    if action == 'getGroupFriend':
        return redirect(url_for('getGroupFriend'))
    if action == 'deleteTidings':
        return redirect(url_for('deleteTidings'))
    if action == 'startAddFriend':
        return redirect(url_for('startAddFriend'))
    if action == 'getTidings':
        return redirect(url_for('getTidings'))
    if action == 'saveAddRecord':
        return redirect(url_for('saveAddRecord'))
    if action == 'getDigForFriend':
        return redirect(url_for('getDigForFriend'))
    if action == 'sortGroup':
        return redirect(url_for('sortGroup'))
    if action == 'logout':
        return redirect(url_for('logout'))
    if action == 'getMesForAddFriend':
        return redirect(url_for('getMesForAddFriend'))
    if action == 'getSendForGroup':
        return redirect(url_for('getSendForGroup'))
    if action == 'getLevel':
        return redirect(url_for('getLevel'))
    if action == 'saveMes':
        return redirect(url_for('saveMes'))
    if action == 'selectAllMes':
        return redirect(url_for('selectAllMes'))
    if action == 'saveFriend':
        return redirect(url_for('saveFriend'))
    if action == 'saveTidings':
        return redirect(url_for('saveTidings'))
    if action == 'selectMes':
        return redirect(url_for('selectMes'))
    if action == 'grouping':
        return redirect(url_for('grouping'))
    if action == 'getDigForGroup':
        return redirect(url_for('getDigForGroup'))
    if action == 'deleteGroup':
        return redirect(url_for('deleteGroup'))
    if action == 'saveRecallRecord':
        return redirect(url_for('saveRecallRecord'))
    if action == 'saveThumbsRecord':
        return redirect(url_for('saveThumbsRecord'))
    if action == 'updateProhibit':
        return redirect(url_for('updateProhibit'))
    if action == 'getAutoDig':
        return redirect(url_for('getAutoDig'))
    if action == 'editRemark':
        return redirect(url_for('editRemark'))
    if action == 'saveGroup':
        return redirect(url_for('saveGroup'))
    if action == 'getDig':
        return redirect(url_for('getDig'))

if __name__ == '__main__':
    app.run(threaded=True)
