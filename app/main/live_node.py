# -*- coding: utf-8 -*-

from flask import request, jsonify, current_app
from flask_login import login_required

from sqlalchemy import or_, func, desc, distinct, cast, case
from sqlalchemy.dialects.mysql import INTEGER, CHAR
from sqlalchemy.exc import IntegrityError

from datetime import datetime
from StringIO import StringIO
import uuid
import json
import gzip
import urllib
import urllib2

from . import main
from .functions import *
from .selects import *

from ..models import Live_node, Live_channel, Continent, continents_nodes

from .. import redis_store

# 同步节点频道资源
@main.route('/api/live_node/channel', methods=['PUT'])
@login_required
def update_live_node_channel():
    # 获取请求参数
    add = request.json['add']
    remove = request.json['remove']
    api = request.json['api']
    node_uuid = request.json['uuid']
    node_cname = request.json['cname']

    # 返回消息
    message = 0
        
    # 增加效率，使用批量插入与删除
    if add:
        channels = [ Live_channel(uuid=str(uuid.uuid1()), name=channel.split('|')[1], cname=channel.split('|')[0], \
            api=json.dumps(api[channel.split('|')[1]]), node_uuid=node_uuid, create_time=datetime.now()) for channel in add.split(',') ]
        db.session.add_all(channels)
        message += len(channels)

    if remove:
        message += len(remove.split(','))
        db.session.query(Live_channel).filter(Live_channel.node_uuid==node_uuid).filter(Live_channel.name.in_(remove.split(','))).delete(synchronize_session=False)
        
    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'直播节点 [%s] [%s] 频道同步成功!' % (node_cname, message)}

        # 清除redis缓存
        node = Live_node.query.filter(Live_node.uuid == node_uuid).first()
        redis_store.hdel(current_app.config['REDIS_NODE_CHANNEL_KEY'], node.code)

    except IntegrityError, e:
        db.session.rollback()
        data = {'msg': u'直播节点 [%s] [%s] 频道同步失败!' % (node_cname, message)}
       
    return jsonify(data)

def get_live_node_channel_info(domain):
    '''
     获取直播节点频道接口信息
    '''
    # 构造请求
    url = 'http://%s/approve/getchannel?format=json' % domain
    req = urllib2.Request(url)
    req.add_header('Accept-encoding', 'gzip')

    # 响应内容解压
    try:
        resp = urllib2.urlopen(req, timeout=10)   # 5秒延时，超时返回 
        if resp.info().get('Content-Encoding') == 'gzip':
            buf = StringIO(resp.read())
            f = gzip.GzipFile(fileobj=buf)
            data = f.read()
        else:
            data = resp.read()

        # 直播节点无频道信息
        if json.loads(data).has_key('FAILED'):
            data = [u'节点异常']
            return data
        else:
            return json.loads(data)
    
    except BaseException, e:
            data = [u'节点异常']
            return data

@login_required
def compare_channel(uuid):
    '''
    分别在直播接口与数据库获取频道信息，进行比对，返回新增与移除的频道列表，返回类型为元组 (add, remove)
    '''
    # 获取本地数据库的直播节点频道信息
    query = Live_node.query \
        .outerjoin(Live_channel, Live_channel.node_uuid==Live_node.uuid) \
        .with_entities(Live_node.uuid, Live_node.domain) \
        .add_columns(func.group_concat(Live_channel.name).label('channel')) \
        .group_by(Live_node.uuid) \
        .filter(Live_node.uuid == uuid) \
        .first()

    # 获取直播节点接口返回的频道信息
    channel = get_live_node_channel_info(query.domain)
    if isinstance(channel, list):
        return channel, channel

    remote = channel.keys()

    # 数据库无频道信息
    if query.channel is None:
        remote_channel = ','.join([v['chinese_name'] + '|' + v['english_name'] for k, v in channel.items()])
        return remote_channel, None

    # 均有频道信息, 远程频道与本地频道做集合运算
    local = query.channel.split(',')
    add = list(set(remote) - set(local))
    remove = list(set(local) - set(remote))
    if len(add) > 0:
        remote_channel = ','.join([v['chinese_name'] + '|' + v['english_name'] for k, v in channel.items() if k in add])
    else:
        remote_channel = None

    if len(remove) > 0:
        local_channel = ','.join(remove)
    else:
        local_channel = None

    return remote_channel, local_channel

# 获取所有直播节点信息
@main.route('/api/live_node/list', methods=['GET'])
@login_required
def get_live_node_list():
    # 获取请求参数
    draw = request.args['draw']
    start = request.args['start']
    length = request.args['length']
    search = request.args['search']
    order_name = request.args['order_name']
    order = request.args['order']

    # 子查询 - 每台直播服务器的频道
    query_channel = Live_node.query \
        .join(Live_channel, Live_channel.node_uuid==Live_node.uuid) \
        .with_entities(Live_node.uuid) \
        .add_columns(func.group_concat(Live_channel.cname).label('channel')) \
        .group_by(Live_node.uuid) \
        .subquery()

    # 子查询 - 每台直播服务器的归属大洲
    query_continent = Live_node.query \
        .join(continents_nodes).join(Continent) \
        .with_entities(Live_node.uuid) \
        .add_columns(func.group_concat(Continent.cname).label('continent')) \
        .group_by(Live_node.uuid) \
        .subquery()

    # 联合查询
    query = Live_node.query \
        .outerjoin(query_channel, Live_node.uuid == query_channel.c.uuid) \
        .outerjoin(query_continent, Live_node.uuid == query_continent.c.uuid) \
        .with_entities(Live_node.uuid, Live_node.code, Live_node.cname, Live_node.alias, Live_node.rate, Live_node.domain,
                       Live_node.speed_test_url, Live_node.status, Live_node.create_time, Live_node.update_time) \
        .add_columns(query_channel.c.channel, query_continent.c.continent)

    # 搜索

    # 排序
    if order == 'asc':
        if order_name == 'sort_id':
            query = query.order_by(cast(Channel_category.sort_id, INTEGER))
        elif order_name == 'cname':
            query = query.order_by(cast(Live_node.cname, CHAR(charset='gbk')))
        else:
            query = query.order_by(order_name)
    else:
        if order_name == 'sort_id':
            query = query.order_by(desc(cast(Channel_category.sort_id, INTEGER)))
        elif order_name == 'cname':
            query = query.order_by(desc(cast(Live_node.cname, CHAR(charset='gbk'))))
        else:
            query = query.order_by(desc(order_name))
    # 记录总数
    total = query.count()

    # 分页
    query = query.paginate(int(start) / int(length) + 1, int(length), False)

    # 返回datatable数据
    data = []
    for q in query.items:
        if q.status == '1':
            add, remove = compare_channel(q.uuid)

        tmp = {}
        tmp['uuid'] = q.uuid
        tmp['code'] = q.code
        tmp['cname'] = q.cname
        tmp['alias'] = q.alias
        tmp['domain'] = q.domain
        tmp['speed_test_url'] = q.speed_test_url
        tmp['continent'] = q.continent
        tmp['rate'] = q.rate
        tmp['channel'] = q.channel
        tmp['add'] = add
        tmp['remove'] = remove
        tmp['create_time'] = q.create_time
        tmp['update_time'] = q.update_time
        tmp['status'] = q.status
        data.append(tmp)

    return jsonify(
        {
            'draw': int(draw),
            'recordsTotal': total,
            'recordsFiltered': total,
            'data': data
        }
    )

# 获取指定直播节点信息
@main.route('/api/live_node', methods=['GET'])
@login_required
def get_live_node():
    # 获取请求参数
    uuid = request.args['uuid']

 # 子查询 - 每台直播服务器的频道
    query_channel = Live_node.query \
        .join(Live_channel, Live_channel.node_uuid==Live_node.uuid) \
        .with_entities(Live_node.uuid) \
        .add_columns(func.group_concat(Live_channel.cname).label('channel')) \
        .group_by(Live_node.uuid) \
        .subquery()

    # 子查询 - 每台直播服务器的归属大洲uuid
    query_continent = Live_node.query \
        .join(continents_nodes).join(Continent) \
        .with_entities(Live_node.uuid) \
        .add_columns(func.group_concat(Continent.uuid).label('continent')) \
        .group_by(Live_node.uuid) \
        .subquery()

    # 联合查询
    query = Live_node.query \
        .outerjoin(query_channel, Live_node.uuid == query_channel.c.uuid) \
        .outerjoin(query_continent, Live_node.uuid == query_continent.c.uuid) \
        .with_entities(Live_node.uuid, Live_node.code, Live_node.cname, Live_node.alias, Live_node.rate, Live_node.domain,
                       Live_node.speed_test_url, Live_node.status, Live_node.create_time, Live_node.update_time) \
        .add_columns(query_channel.c.channel, query_continent.c.continent) \
        .filter(Live_node.uuid == uuid).first()

    # 返回datatable数据
    data = {
        'uuid': query.uuid,
        'code': query.code,
        'cname': query.cname,
        'alias': query.alias,
        'channel': query.channel,
        'rate': query.rate,
        'domain': query.domain,
        'speed_test_url': query.speed_test_url,
        'continent_uuid': query.continent,
        'status': query.status,
        'create_time': query.create_time,
        'update_time': query.update_time
    }

    return jsonify(data)

# 新建直播节点信息
@main.route('/api/live_node', methods=['POST'])
@login_required
def add_live_node():
    # 获取请求参数
    code = request.json['code']
    cname = request.json['cname']
    alias = request.json['alias']
    rate = request.json['rate']
    domain = request.json['domain']
    speed_test_url = request.json['speed_test_url']
    continent = request.json['continent']
    status = request.json['status']

    # 返回消息
    message = cname

    # 直播节点
    node = Live_node()
    node.uuid = str(uuid.uuid1())
    node.code = code
    node.cname = cname
    node.alias = alias
    node.rate = rate
    node.domain = domain
    node.speed_test_url = speed_test_url
    node.status = status
    node.create_time = datetime.now()

    db.session.add(node)

    # 大洲
    if continent:
        continents = Continent.query.filter(
            Continent.uuid.in_(continent)).all()
        node.continents = continents

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'直播节点 [%s] 数据新建成功!' % message}
        return jsonify(data)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'直播节点 [%s] 数据新建失败!' % message}
        return jsonify(data)

# 更新指定直播节点信息
@main.route('/api/live_node', methods=['PUT'])
@login_required
def update_live_node():
    # 获取请求参数
    node_uuid = request.json['uuid']
    code = request.json['code']
    cname = request.json['cname']
    alias = request.json['alias']
    rate = request.json['rate']
    domain = request.json['domain']
    speed_test_url = request.json['speed_test_url']
    continent = request.json['continent']
    status = request.json['status']

    # 返回消息
    message = cname

    #  直播节点
    node = Live_node.query.filter(Live_node.uuid == node_uuid).first()
    node.code = code
    node.cname = cname
    node.alias = alias
    node.rate = rate
    if node.domain != domain:
        node.domain = domain
        # 同步数据库接口信息
        channel_info = get_live_node_channel_info(domain)
        db.session.query(Live_channel).filter(Live_channel.node_uuid==node_uuid).delete()
        channels = [ Live_channel(uuid=str(uuid.uuid1()), name=channel, cname=channel_info[channel]['chinese_name'], \
            api=json.dumps(channel_info[channel]), node_uuid=node_uuid, create_time=datetime.now()) for channel in channel_info.keys()]

        db.session.add_all(channels)

    node.speed_test_url = speed_test_url
    node.status = status
    node.update_time = datetime.now()

    # 大洲
    if continent:
        continents = Continent.query.filter(
            Continent.uuid.in_(continent)).all()
        node.continents = continents
    else:
        # 数据空，删除已存在关系
        for d in node.continents:
            node.continents.remove(d)

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'直播节点 [%s] 数据更新成功!' % message}
        # 清除redis缓存
        if status == '0':
            redis_store.hdel(current_app.config['REDIS_NODE_CHANNEL_KEY'], code)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'直播节点 [%s] 数据更新失败!' % message}
    
    return jsonify(data)

# 删除指定直播节点信息
@main.route('/api/live_node', methods=['DELETE'])
def delete_live_node():
    # 获取请求参数
    uuid = request.json['uuid']

    # 返回消息
    message = []

    # 节点code
    field = [q.code for q in Live_node.query.filter(Live_node.uuid.in_(uuid)).all()]

    # 删除信息
    #message = [ q.cname for q in Live_node.query.filter(Live_node.uuid.in_(uuid)).all()]
    #db.session.query(Live_node).filter(Live_node.uuid.in_(uuid)).delete(synchronize_session=False)
    for i in uuid:
        node = Live_node.query.filter(Live_node.uuid==i).first()
        message.append(node.cname)
        db.session.delete(node)

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'直播节点 [%s] 数据删除成功!' % ','.join(message)}
        
        # 清除redis缓存
        redis_store.hdel(current_app.config['REDIS_NODE_CHANNEL_KEY'], *field)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'直播节点 [%s] 数据删除失败!' % ','.join(message)}

    return jsonify(data)