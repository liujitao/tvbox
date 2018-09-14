# -*- coding: utf-8 -*-

from flask import request, jsonify, current_app
from flask_login import login_required

from sqlalchemy import or_, func, desc, distinct, cast, case
from sqlalchemy.dialects.mysql import INTEGER, CHAR
from sqlalchemy.exc import IntegrityError

from datetime import datetime
import uuid, json

from . import main
from .functions import *
from .selects import *

from ..models import *
from .. import redis_store

# 获取所有产品包信息
@main.route('/api/channel_product/list', methods=['GET'])
@login_required
def get_channel_product_list():
    # 获取请求参数
    draw = request.args['draw']
    start = request.args['start']
    length = request.args['length']
    search = request.args['search']
    order_name = request.args['order_name']
    order = request.args['order']

    # 子查询 - 每个产品包关联的频道
    query_channel = Channel_product.query \
        .join(products_channels).join(Channel) \
        .with_entities(Channel_product.uuid) \
        .add_columns(func.group_concat(Channel.cname).label('channel')) \
        .group_by(Channel_product.uuid) \
        .subquery()

    # 子查询 - 每个产品包关联的电视盒
    query_stb = Channel_product.query \
        .join(stbs_products).join(Stb) \
        .with_entities(Channel_product.uuid) \
        .add_columns(func.count(Stb.sn).label('stb')) \
        .group_by(Channel_product.uuid) \
        .subquery()

    # 子查询 - 每个产品包关联的app帐号
    query_app = Channel_product.query \
        .join(apps_products).join(App) \
        .with_entities(Channel_product.uuid) \
        .add_columns(func.count(App.app_id).label('app')) \
        .group_by(Channel_product.uuid) \
        .subquery()

    # 联合查询
    query = Channel_product.query \
        .outerjoin(query_channel, query_channel.c.uuid == Channel_product.uuid) \
        .outerjoin(query_stb, query_stb.c.uuid == Channel_product.uuid) \
        .outerjoin(query_app, query_app.c.uuid == Channel_product.uuid) \
        .group_by(Channel_product.uuid) \
        .with_entities(Channel_product.uuid, Channel_product.cname, Channel_product.category, Channel_product.description, Channel_product.status, \
            Channel_product.create_time, Channel_product.update_time) \
        .add_columns(query_channel.c.channel, query_stb.c.stb, query_app.c.app)

    # 搜索
    if search:
        query = query.filter(or_( \
            Channel_product.cname.like('%' + search + '%'),
            Channel_product.category.in_(category_to_id(search)),
            Channel_product.status.in_(status_to_id(search))
        ))

    # 排序
    if order == 'asc':
        if order_name == 'sort_id':
            query = query.order_by(cast(Channel_product.sort_id, INTEGER))
        elif order_name == 'cname':
            query = query.order_by(cast(Channel_product.cname, CHAR(charset='gbk')))
        else:
            query = query.order_by(order_name)
    else:
        if order_name == 'sort_id':
            query = query.order_by(desc(cast(Channel_product.sort_id, INTEGER)))
        elif order_name == 'cname':
            query = query.order_by(desc(cast(Channel_product.cname, CHAR(charset='gbk'))))
        else:
            query = query.order_by(desc(order_name))

    # 记录总数
    total = query.count()

    # 分页
    query = query.paginate(int(start) / int(length) + 1, int(length), False)

    # 返回datatable数据
    data = [{
        'uuid': q.uuid,
        'cname': q.cname,
        'category': q.category,
        'description': q.description,
        'channel': q.channel,
        'stb': q.stb,
        'app': q.app,
        'status': q.status,
        'create_time': q.create_time,
        'update_time': q.update_time
    } for q in query.items]

    return jsonify(
        {
            'draw': int(draw),
            'recordsTotal': total,
            'recordsFiltered': total,
            'data': data
        }
    )

# 获取指定产品包信息
@main.route('/api/channel_product', methods=['GET'])
@login_required
def get_channel_product():
    # 获取请求参数
    uuid = request.args['uuid']
    
    # 子查询 - 每个产品包指派的频道uuid
    query_channel = Channel_product.query \
        .join(products_channels).join(Channel) \
        .with_entities(Channel_product.uuid) \
        .add_columns(func.group_concat(Channel.uuid).label('channel_uuid')) \
        .group_by(Channel_product.uuid) \
        .subquery()

    # 联合查询
    query = Channel_product.query \
        .outerjoin(query_channel, Channel_product.uuid == query_channel.c.uuid) \
        .with_entities(Channel_product.uuid, Channel_product.cname, Channel_product.description, \
            Channel_product.category, Channel_product.status, Channel_product.create_time, Channel_product.update_time) \
        .add_columns(query_channel.c.channel_uuid) \
        .filter(Channel_product.uuid==uuid).first()
    
    # 返回datatable数据
    data = {
        'uuid': query.uuid,
        'cname': query.cname,
        'description': query.description,
        'channel_uuid': query.channel_uuid,
        'category': query.category,
        'status': query.status,
        'create_time': query.create_time,
        'update_time': query.update_time
    }

    return jsonify(data)

# 新建产品包信息
@main.route('/api/channel_product', methods=['POST'])
@login_required
def add_channel_product():
    # 获取请求参数
    cname = request.json['cname']
    description = request.json['description']
    channel = list(set(request.json['channel'])) # 频道去重
    category = request.json['category']
    status = request.json['status']

    # 返回消息
    message = cname

    # 产品包
    channel_product = Channel_product()
    channel_product.uuid = str(uuid.uuid1())
    channel_product.cname = cname
    channel_product.description = description
    channel_product.category = category
    channel_product.status = status
    channel_product.channel = channel
    channel_product.create_time = datetime.now()

    db.session.add(channel_product)

    # 频道
    if channel:
        channels = Channel.query.filter(Channel.uuid.in_(channel)).all()
        channel_product.channels = channels

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'产品包 [%s] 数据新建成功!' % message}

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'产品包 [%s] 数据新建失败!' % message}
        
    return jsonify(data)

# 更新产品包信息
@main.route('/api/channel_product', methods=['PUT'])
@login_required
def update_channel_product():
    # 获取请求参数
    uuid = request.json['uuid']
    cname = request.json['cname']
    description = request.json['description']
    channel = list(set(request.json['channel'])) # 频道去重
    category = request.json['category']
    status = request.json['status']

    # 返回消息
    message = cname
    
    # 产品包
    channel_product = Channel_product.query.filter(Channel_product.uuid==uuid).first()
    channel_product.cname = cname
    channel_product.description = description
    channel_product.channel = channel
    channel_product.category = category
    channel_product.status = status
    channel_product.update_time = datetime.now()

    # 频道
    if channel:
        channels = Channel.query.filter(Channel.uuid.in_(channel)).all()
        channel_product.channels = channels
    else:
        # 数据空，删除已存在关系
        for d in channel_product.channels:
            channel_product.channels.remove(d)

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'产品包 [%s] 数据更新成功!' % message}
        
        # 清除redis缓存
        redis_store.hdel(current_app.config['REDIS_PRODUCT_CHANNEL_KEY'], uuid)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'产品包 [%s] 数据更新失败!' % message}
    
    return jsonify(data)

# 删除产品包信息
@main.route('/api/channel_product', methods=['DELETE'])
@login_required
def delete_channel_product():
    # 获取请求参数
    uuid = request.json['uuid']

    # 返回消息
    message = []
    constraint = []

    # 删除信息
    for i in uuid:
        product = Channel_product.query.filter(Channel_product.uuid==i).first()
        # 业务约束(电视盒关联)
        stb = Stb.query \
            .join(stbs_products).join(Channel_product) \
            .filter(Channel_product.uuid==i).all()

        if stb:
            constraint.append(product.cname)
        else:
            message.append(product.cname)
            db.session.delete(product)

    # 提交数据库
    try:
        db.session.commit()
        if len(constraint) == 0:
            data = {'msg': u'产品包 [%s] 数据删除成功!' % ','.join(message)}

            # 清除redis缓存
            redis_store.hdel(current_app.config['REDIS_PRODUCT_CHANNEL_KEY'], *uuid)
        else:
            data = {'msg': u'产品包 [%s] 数据删除未成功，请先解除电视盒关联后再删除！' % ','.join(constraint)}

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'产品包数据删除失败!'}

    return jsonify(data)

# 获取指定产品包关联电视盒信息
@main.route('/api/channel_product/tvbox', methods=['GET'])
@login_required
def get_channel_product_tvbox():
    # 获取请求参数
    uuid = request.args['uuid']
    
    data = [ q.sn for q in Channel_product.query.join(stbs_products).join(Stb) \
        .with_entities(Stb.sn).filter(Channel_product.uuid==uuid).order_by(Stb.sn).all()]

    return jsonify(data)

# 获取指定产品包关联app信息
@main.route('/api/channel_product/app', methods=['GET'])
@login_required
def get_channel_product_app():
    # 获取请求参数
    uuid = request.args['uuid']
    
    data = [ q.app_id for q in Channel_product.query.join(apps_products).join(App) \
        .with_entities(App.app_id).filter(Channel_product.uuid==uuid).order_by(App.app_id).all()]

    return jsonify(data)