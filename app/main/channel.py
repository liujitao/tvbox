# -*- coding: utf-8 -*-
from flask import request, jsonify, render_template
from flask_login import login_required

from sqlalchemy import or_, func, desc, distinct, cast, case, collate
from sqlalchemy.dialects.mysql import INTEGER, CHAR
from sqlalchemy.exc import IntegrityError

import uuid
from datetime import datetime

from . import main
from .functions import *
from .selects import *

from ..models import Channel, Channel_category, Channel_product, products_channels, categories_channels, Live_channel
from .. import redis_store

# 直播频道同步
@main.route('/api/channel/sync', methods=['GET'])
@login_required
def sync_channel():
    # 获取请求参数
    action = request.args['action']

    # 直播频道
    channels = Live_channel.query.with_entities(Live_channel.name, Live_channel.cname).distinct(Live_channel.name).all()
    live_channel = [channel.name for channel in channels]
    data = {channel.name: channel.cname for channel in channels}

    # 产品包频道
    channels = Channel.query.with_entities(Channel.name).all()
    product_channel = [channel.name for channel in channels]

    # 交集比较
    add = list(set(live_channel) - set(product_channel))
    remove = list(set(product_channel) - set(live_channel))

    # 处理
    if action == 'check':
        return jsonify({'add': sorted(add), 'remove': sorted(remove)})

    if action == 'sync':
        # 返回消息
        message = []
        constraint = []

        # 添加
        if len(add) > 0:
            channels = [Channel(uuid=str(uuid.uuid1()), name=channel_name, cname=data[channel_name], sort_id='0', status='1', create_time=datetime.now()) for channel_name in add]
            db.session.add_all(channels)

        # 删除
        if len(remove) > 0:
            #产品包关联约束频道
            query = Channel.query \
                .outerjoin(products_channels).outerjoin(Channel_product) \
                .with_entities(Channel.name, Channel.cname) \
                .add_columns(func.count(Channel_product.cname).label('product')) \
                .group_by(Channel.uuid) \
                .filter(Channel.name.in_(remove))

            for channel in query:
                if channel.product and channel.product > 0:
                    constraint.append(channel.cname)
                else:
                    message.append(channel.name)
            
            if len(message) > 0:
                db.session.query(Channel).filter(Channel.name.in_(message)).delete(synchronize_session=False)

    # 提交数据库
    try:
        db.session.commit()
        if len(constraint) == 0:
            data = {'msg': u'直播 [%s] 频道同步成功!' % len(add)+len(message)}
            
            # 清除redis缓存 （同步频道时需要解绑产品包，已在变更频道时清除，此处不再清除）
        else:
            data = {'msg': u'直播 [%s] 频道同步成功, 频道 [%s] 请先解除产品包关联后再删除！' % (len(add)+len(message), ','.join(constraint))}

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'直播频道同步失败!'}

    return jsonify(data)

# 排序频道
@main.route('/api/channel/sort', methods=['PUT'])
@login_required
def sort_channel():
    # 获取请求参数
    uuid = request.json['uuid']

    # 返回消息
    message = len(uuid)

    # 产品包uuid
    product_uuid = [ q.product
        for q in Channel.query \
            .join(products_channels).join(Channel_product) \
            .add_columns(Channel_product.uuid.label('product')).all()
    ]

    # 批量更新频道
    channels = [{'uuid': id, 'sort_id': str(idx)} for idx, id in enumerate(uuid, 1)]
    db.session.bulk_update_mappings(Channel, channels)

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'频道 [%s] 条数据排序成功!' % message}

        # 清除redis缓存
        if product_uuid:
            redis_store.hdel(current_app.config['REDIS_PRODUCT_CHANNEL_KEY'], *product_uuid)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'频道 [%s] 条数据排序失败!' % message}
        
    return jsonify(data)

# 获取所有频道信息
@main.route('/api/channel/list', methods=['GET'])
@login_required
def get_channel_list():
    # 获取请求参数
    draw = request.args['draw']
    start = request.args['start']
    length = request.args['length']
    search = request.args['search']
    order_name = request.args['order_name']
    order = request.args['order']

    # 子查询 - 每个频道归属产品包
    query_product = Channel.query \
        .join(products_channels).join(Channel_product) \
        .with_entities(Channel.uuid) \
        .add_columns(func.group_concat(Channel_product.cname).label('product')) \
        .group_by(Channel.uuid) \
        .subquery()

    # 子查询 - 每个频道归属频道
    query_category = Channel.query \
        .join(categories_channels).join(Channel_category) \
        .with_entities(Channel.uuid) \
        .add_columns(func.group_concat(Channel_category.cname).label('category')) \
        .group_by(Channel.uuid) \
        .subquery()

    # 联合查询
    query = Channel.query \
        .outerjoin(query_product, Channel.uuid == query_product.c.uuid) \
        .outerjoin(query_category, Channel.uuid == query_category.c.uuid) \
        .with_entities(Channel.uuid, Channel.name, Channel.cname, Channel.tname, Channel.sort_id, Channel.status, Channel.create_time, Channel.update_time) \
        .add_columns(query_product.c.product, query_category.c.category)

    # 搜索
    if search:
        query = query.filter(or_( \
            Channel.name.like('%' + search + '%'),  
            Channel.cname.like('%' + search + '%'),
            query_category.c.category.like('%' + search + '%'),
            Channel.status.in_(status_to_id(search))
        ))

    # 排序
    if order == 'asc':
        if order_name == 'sort_id':
            query = query.order_by(cast(Channel.sort_id, INTEGER))
        elif order_name == 'cname':
            query = query.order_by(cast(Channel.cname, CHAR(charset='gbk')))
        else:
            query = query.order_by(order_name)
    else:
        if order_name == 'sort_id':
            query = query.order_by(desc(cast(Channel.sort_id, INTEGER)))
        elif order_name == 'cname':
            query = query.order_by(desc(cast(Channel.cname, CHAR(charset='gbk'))))
        else:
            query = query.order_by(desc(order_name))

    # 记录总数
    total = query.count()

    # 分页
    query = query.paginate(int(start) / int(length) + 1, int(length), False)

    # 返回datatable数据
    data = [{
        'uuid': q.uuid,
        'name': q.name,
        'cname': q.cname,
        'tname': q.tname,
        'category': q.category,
        'sort_id': q.sort_id,
        'product': q.product,
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

# 获取指定频道信息
@main.route('/api/channel', methods=['GET'])
@login_required
def get_channel():
     # 获取请求参数
    uuid = request.args['uuid']

    # 子查询 - 每个频道指派的频道分类uuid
    query_category = Channel.query \
        .join(categories_channels).join(Channel_category) \
        .with_entities(Channel.uuid) \
        .add_columns(func.group_concat(Channel_category.uuid).label('category_uuid')) \
        .group_by(Channel.uuid) \
        .subquery()

    # 子查询 - 每个频道指派的产品包uuid
    query_product = Channel.query \
        .join(products_channels).join(Channel_product) \
        .with_entities(Channel.uuid) \
        .add_columns(func.group_concat(Channel_product.uuid).label('product_uuid')) \
        .group_by(Channel.uuid) \
        .subquery()

    # 联合查询
    query = Channel.query \
        .outerjoin(query_category, Channel.uuid == query_category.c.uuid) \
        .outerjoin(query_product, Channel.uuid == query_product.c.uuid) \
        .with_entities(Channel.uuid, Channel.name, Channel.cname, Channel.tname,
                       Channel.sort_id, Channel.status, Channel.create_time, Channel.update_time) \
        .add_columns(query_category.c.category_uuid, query_product.c.product_uuid) \
        .filter(Channel.uuid == uuid).first()

    # 返回datatable数据
    data = {
        'uuid': query.uuid,
        'name': query.name,
        'cname': query.cname,
        'tname': query.tname,
        'sort_id': query.sort_id,
        'category_uuid': query.category_uuid,
        'product_uuid': query.product_uuid,
        'status': query.status,
        'create_time': query.create_time,
        'update_time': query.update_time
    }

    return jsonify(data)

# 新建频道信息
@main.route('/api/channel', methods=['POST'])
@login_required
def add_channel():
    # 获取请求参数
    name = request.json['name']
    cname = request.json['cname']
    tname = request.json['tname']
    category = request.json['category']
    product = request.json['product']
    sort_id = request.json['sort_id']
    status = request.json['status']

    # 返回消息
    message = cname

    # 频道分类
    channel = Channel()
    channel.uuid = str(uuid.uuid1())
    channel.name = name
    channel.cname = cname
    channel.tname = tname
    channel.sort_id = sort_id
    channel.status = status
    channel.create_time = datetime.now()

    db.session.add(channel)

    # 频道
    if category:
        categories = Channel_category.query.filter(
            Channel_category.uuid.in_(category)).all()
        channel.categories = categories

    # 产品包
    if product:
        products = Channel_product.query.filter(
            Channel_product.uuid.in_(product)).all()
        channel.products = products

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'频道 [%s] 数据新建成功!' % message}

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'频道 [%s] 数据新建失败!' % message}
    
    return jsonify(data)

# 更新频道信息
@main.route('/api/channel', methods=['PUT'])
@login_required
def update_channel():
    # 获取请求参数
    uuid = request.json['uuid']
    name = request.json['name']
    cname = request.json['cname']
    tname = request.json['tname']
    category = request.json['category']
    product = request.json['product']
    sort_id = request.json['sort_id']
    status = request.json['status']

    # 返回消息
    message = cname

    # 产品包uuid
    product_uuid = [ q.product
        for q in Channel.query \
            .join(products_channels).join(Channel_product) \
            .add_columns(Channel_product.uuid.label('product')).all()
    ]

    # 频道
    channel = Channel.query.filter(Channel.uuid == uuid).first()
    channel.name = name
    channel.cname = cname
    channel.tname = tname
    channel.sort_id = sort_id
    channel.status = status
    channel.update_time = datetime.now()

    # 频道
    if category:
        categories = Channel_category.query.filter(
            Channel_category.uuid.in_(category)).all()
        channel.categories = categories
    else:
        # 数据空，删除已存在关系
        for d in channel.categories:
            channel.categories.remove(d)

    # 产品包
    if product:
        products = Channel_product.query.filter(
            Channel_product.uuid.in_(product)).all()
        channel.products = products
    else:
        # 数据空，删除已存在关系
        for d in channel.products:
            channel.products.remove(d)

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'频道 [%s] 数据更新成功!' % message}
        
        # 清除redis缓存
        if product_uuid:
            redis_store.hdel(current_app.config['REDIS_PRODUCT_CHANNEL_KEY'], *product_uuid)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'频道 [%s] 数据更新失败!' % message}
        
    return jsonify(data)

# 删除频道信息
@main.route('/api/channel', methods=['DELETE'])
@login_required
def delete_channel():
    # 获取请求参数
    uuid = request.json['uuid']

    # 返回消息
    message = []
    constraint = []

    # 删除信息
    for i in uuid:
        channel = Channel.query.filter(Channel.uuid == i).first()
        # 业务约束(产品包关联)
        product = Channel_product.query \
            .join(products_channels).join(Channel) \
            .filter(Channel.uuid == i).all()
        if product:
            constraint.append(channel.name)
        else:
            message.append(channel.name)
            db.session.delete(channel)

    # 提交数据库
    try:
        db.session.commit()
        if len(constraint) == 0:
            data = {'msg': u'频道 [%s] 数据删除成功!' % ','.join(message)}
            
            # 清除redis缓存 (删除频道需解绑产品包，已在变更频道时清除，此处不再清除)

        else:
            data = {'msg': u'频道 [%s] 数据删除成功，频道 [%s] 请先解除产品包关联后再删除！' % (
                ','.join(message), ','.join(constraint))}

    except IntegrityError:
        db.ession.rollback()
        data = {'msg': u'频道数据删除失败!'}

    return jsonify(data)
