# -*- coding: utf-8 -*-

from flask import request, jsonify, render_template
from flask_login import login_required

from sqlalchemy import or_, func, desc, distinct, cast, case
from sqlalchemy.dialects.mysql import INTEGER, CHAR
from sqlalchemy.exc import IntegrityError

from datetime import datetime
import uuid

from . import main
from .functions import *
from .selects import *

from ..models import Channel, Channel_category, categories_channels, Channel_product, products_channels
from .. import redis_store

# 获取所有频道分类信息
@main.route('/api/channel_category/list', methods=['GET'])
@login_required
def get_channel_category_list():
    # 获取请求参数
    draw = request.args['draw']
    start = request.args['start']
    length = request.args['length']
    search = request.args['search']
    order_name = request.args['order_name']
    order = request.args['order']

    # 子查询 - 每个频道分类指派的频道
    query_channel = Channel_category.query \
        .join(categories_channels).join(Channel) \
        .with_entities(Channel_category.uuid) \
        .add_columns(func.group_concat(Channel.cname).label('channel')) \
        .group_by(Channel_category.uuid) \
        .subquery()

    # 联合查询
    query = Channel_category.query \
        .outerjoin(query_channel, Channel_category.uuid == query_channel.c.uuid) \
        .with_entities(Channel_category.uuid, Channel_category.name, Channel_category.cname, Channel_category.tname, \
            Channel_category.sort_id, Channel_category.status, Channel_category.create_time, Channel_category.update_time) \
        .add_columns(query_channel.c.channel)

    # 搜索

    # 排序
    if order == 'asc':
        if order_name == 'sort_id':
            query = query.order_by(cast(Channel_category.sort_id, INTEGER))
        elif order_name == 'cname':
            query = query.order_by(cast(Channel_category.cname, CHAR(charset='gbk')))
        else:
            query = query.order_by(order_name)
    else:
        if order_name == 'sort_id':
            query = query.order_by(desc(cast(Channel_category.sort_id, INTEGER)))
        elif order_name == 'cname':
            query = query.order_by(desc(cast(Channel_category.cname, CHAR(charset='gbk'))))
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
        'channel': q.channel,
        'sort_id': q.sort_id,
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

# 获取指定频道分类信
@main.route('/api/channel_category', methods=['GET'])
@login_required
def get_channel_category():
    # 获取请求参数
    uuid = request.args['uuid']
    
    # 子查询 - 每个频道分类指派的频道uuid
    query_channel = Channel_category.query \
        .join(categories_channels).join(Channel) \
        .with_entities(Channel_category.uuid) \
        .add_columns(func.group_concat(Channel.uuid).label('channel_uuid')) \
        .group_by(Channel_category.uuid) \
        .subquery()

    # 联合查询
    query = Channel_category.query \
        .outerjoin(query_channel, Channel_category.uuid == query_channel.c.uuid) \
        .with_entities(Channel_category.uuid, Channel_category.name, Channel_category.cname, Channel_category.tname, \
                       Channel_category.sort_id, Channel_category.status, Channel_category.create_time, Channel_category.update_time) \
        .add_columns(query_channel.c.channel_uuid) \
        .filter(Channel_category.uuid==uuid).first()
    
    # 返回datatable数据
    data = {
        'uuid': query.uuid,
        'name': query.name,
        'cname': query.cname,
        'tname': query.tname,
        'sort_id': query.sort_id,
        'channel_uuid': query.channel_uuid,
        'status': query.status,
        'create_time': query.create_time,
        'update_time': query.update_time
    }

    return jsonify(data)

# 新建频道分类信息
@main.route('/api/channel_category', methods=['POST'])
@login_required
def add_channel_category():
    # 获取请求参数
    name = request.json['name']
    cname = request.json['cname']
    tname = request.json['tname']
    sort_id = request.json['sort_id']
    channel = request.json['channel']
    status = request.json['status']

    # 返回消息
    message = cname

    # 频道分类
    channel_category = Channel_category()
    channel_category.uuid = str(uuid.uuid1())
    channel_category.name = name
    channel_category.cname = cname
    channel_category.tname = tname
    channel_category.sort_id = sort_id
    channel_category.status = status
    channel_category.create_time = datetime.now()

    db.session.add(channel_category)

    # 频道
    if channel:
        channels = Channel.query.filter(Channel.uuid.in_(channel)).all()
        channel_category.channels = channels

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'频道分类 [%s] 数据新建成功!' % message}
        return jsonify(data)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'频道分类 [%s] 数据新建失败!' % message}
        return jsonify(data)


# 更新频道分类信息
@main.route('/api/channel_category', methods=['PUT'])
@login_required
def update_channel_category():
    # 获取请求参数
    uuid = request.json['uuid']
    name = request.json['name']
    cname = request.json['cname']
    tname = request.json['tname']
    sort_id = request.json['sort_id']
    channel = request.json['channel']
    status = request.json['status']

    # 返回消息
    message = cname
    
    # 产品包uuid
    product_uuid = [ q.product
        for q in Channel.query \
            .join(products_channels).join(Channel_product) \
            .add_columns(Channel_product.uuid.label('product')).all()
    ]

    # 频道分类
    channel_category = Channel_category.query.filter(Channel_category.uuid==uuid).first()
    channel_category.name = name
    channel_category.cname = cname
    channel_category.tname = tname
    channel_category.sort_id = sort_id
    channel_category.status = status
    channel_category.update_time = datetime.now()

    # 频道
    if channel:
        channels = Channel.query.filter(Channel.uuid.in_(channel)).all()
        channel_category.channels = channels
    else:
        # 数据空，删除已存在关系
        for d in channel_category.channels:
            channel_category.channels.remove(d)

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'频道分类 [%s] 数据更新成功!' % message}
        
        # 清除redis缓存
        if product_uuid:
            redis_store.hdel(current_app.config['REDIS_PRODUCT_CHANNEL_KEY'], *product_uuid)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'频道分类 [%s] 数据更新失败!' % message}
        
    return jsonify(data)

# 删除频道分类信息
@main.route('/api/channel_category', methods=['DELETE'])
@login_required
def delete_channel_category():
    # 获取请求参数
    uuid = request.json['uuid']

    # 返回消息
    message = []
    constraint = []

    # 删除信息
    for i in uuid:
        channel_category = Channel_category.query.filter(Channel_category.uuid==i).first()
        # 业务约束(频道关联)
        channel = Channel.query \
            .join(categories_channels).join(Channel_category) \
            .filter(Channel_category.uuid==i).all()

        if channel:
            constraint.append(channel_category.cname)
        else:
            message.append(channel_category.cname)
            db.session.delete(channel_category)

    # 提交数据库
    try:
        db.session.commit()
        if len(constraint) == 0:
            data = {'msg': u'频道分类 [%s] 数据删除成功!' % ','.join(message)}

            # 清除redis缓存（删除频道分类，需要解绑频道，已在变更频道分类时清除缓存，此处不再处理）
        else:
            data = {'msg': u'频道分类 [%s] 数据删除成功，客户 [%s] 请先解除频道关联后再删除！' % (','.join(message), ','.join(constraint))}

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'频道分类数据删除失败!'}

    return jsonify(data)

