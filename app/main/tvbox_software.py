# -*- coding: utf-8 -*-

from flask import request, jsonify, render_template
from flask_login import login_required

from sqlalchemy import or_, func, desc, distinct
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import uuid

from . import main
from .functions import *
from .selects import *

from ..models import Stb_model, Stb_software, Stb_grouping, softwares_groupings

# 获取所有电视盒升级软件信息
@main.route('/api/tvbox_software/list', methods=['GET'])
@login_required
def get_tvbox_software_list():
    # 获取请求参数
    draw = request.args['draw']
    start = request.args['start']
    length = request.args['length']
    search = request.args['search']
    order_name = request.args['order_name']
    order = request.args['order']

    # 子查询 - 每个电视盒软件指派的分组
    query_grouping = Stb_software.query \
        .join(softwares_groupings).join(Stb_grouping) \
        .with_entities(Stb_software.uuid) \
        .add_columns(func.group_concat(Stb_grouping.cname).label('grouping')) \
        .group_by(Stb_software.uuid) \
        .subquery()

    # 联合查询
    query = Stb_software.query \
        .outerjoin(Stb_model, Stb_model.uuid == Stb_software.model_uuid) \
        .outerjoin(query_grouping, query_grouping.c.uuid == Stb_software.uuid) \
        .with_entities(Stb_software.uuid, Stb_software.version, Stb_software.download_url, Stb_software.size, Stb_software.md5, \
            Stb_software.category, Stb_software.force_update, Stb_software.status, Stb_software.create_time, Stb_software.update_time) \
        .add_columns(Stb_model.code.label('model'), query_grouping.c.grouping)

    # 搜索
    if search:
        query = query.filter(or_( \
            Stb_model.code.like('%' + search + '%'),
            Stb_software.version.like('%' + search + '%')))

    # 排序
    if order == 'asc':
        query = query.order_by(order_name)
    else:
        query = query.order_by(desc(order_name))

    # 记录总数
    total = query.count()

    # 分页
    query = query.paginate(int(start) / int(length) + 1, int(length), False)

    # 返回datatable数据
    data = [{
        'uuid': q.uuid,
        'model': q.model,
        'version': q.version,
        'download_url': q.download_url,
        'size': q.size,
        'md5': q.md5,
        'force_update': q.force_update,
        'category': q.category,
        'grouping': q.grouping,
        'create_time': q.create_time,
        'update_time': q.update_time,
        'status': q.status
    } for q in query.items]

    return jsonify(
        {
            'draw': int(draw),
            'recordsTotal': total,
            'recordsFiltered': total,
            'data': data
        }
    )

# 获取指定电视盒软件信息
@main.route('/api/tvbox_software', methods=['GET'])
@login_required
def get_tvbox_software():
    # 获取请求参数
    uuid = request.args['uuid']
    
    # 子查询 - 每个电视盒软件指派的分组uuid
    query_grouping = Stb_software.query \
        .join(softwares_groupings).join(Stb_grouping) \
        .with_entities(Stb_software.uuid) \
        .add_columns(func.group_concat(Stb_grouping.uuid).label('grouping_uuid')) \
        .group_by(Stb_software.uuid) \
        .subquery()

    # 查询
    q = Stb_software.query \
        .outerjoin(Stb_model, Stb_software.model_uuid == Stb_model.uuid) \
        .outerjoin(query_grouping, query_grouping.c.uuid == Stb_software.uuid) \
        .with_entities(Stb_software.uuid, Stb_software.version, Stb_software.download_url, Stb_software.size, Stb_software.md5, \
            Stb_software.category, Stb_software.force_update, Stb_software.status, Stb_software.create_time, Stb_software.update_time) \
        .add_columns(Stb_model.uuid.label('model_uuid'), query_grouping.c.grouping_uuid) \
        .filter(Stb_software.uuid==uuid) \
        .first()

    data = {
        'uuid': q.uuid,
        'model_uuid': q.model_uuid,
        'version': q.version,
        'download_url': q.download_url,
        'size': q.size,
        'md5': q.md5,
        'force_update': q.force_update,
        'category': q.category,
        'grouping_uuid': q.grouping_uuid,
        'create_time': q.create_time,
        'update_time': q.update_time,
        'status': q.status
    }

    return jsonify(data)

# 新建电视盒软件信息
@main.route('/api/tvbox_software', methods=['POST'])
@login_required
def add_tvbox_software():
    # 获取请求参数
    model = request.json['model']
    version = request.json['version']
    download_url = request.json['download_url']
    size = request.json['size']
    md5 = request.json['md5']
    force_update = request.json['force_update']
    category = request.json['category']
    grouping = request.json['grouping']
    status = request.json['status']

    # 返回消息
    message = version

    # 电视盒软件
    software = Stb_software()
    software.uuid = str(uuid.uuid1())
    software.model_uuid = model
    software.version = version
    software.download_url = download_url
    software.size = int(size)
    software.md5 = md5
    software.force_update = force_update
    software.category = category
    software.status = status
    software.create_time = datetime.now()
    
    db.session.add(software)

    # 分组
    if grouping:
        groupings = Stb_grouping.query.filter(Stb_grouping.uuid.in_(grouping)).all()
        software.groupings = groupings

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'电视盒软件版本 [%s] 数据新建成功!' % message}
        return jsonify(data)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'电视盒软件版本 [%s] 数据新建失败!' % message}
        return jsonify(data)

# 更新电视盒软件信息
@main.route('/api/tvbox_software', methods=['PUT'])
@login_required
def update_tvbox_software():
    # 获取请求参数
    uuid = request.json['uuid']
    model = request.json['model']
    version = request.json['version']
    download_url = request.json['download_url']
    size = request.json['size']
    md5 = request.json['md5']
    force_update = request.json['force_update']
    category = request.json['category']
    grouping = request.json['grouping']
    status = request.json['status']

    # 返回消息
    message = version
    
    # 电视盒软件
    software = Stb_software().query.filter(Stb_software.uuid==uuid).first()
    software.model_uuid = model
    software.version = version
    software.download_url = download_url
    software.size = int(size)
    software.md5 = md5
    software.force_update = force_update
    software.category = category
    software.status = status
    software.update_time = datetime.now()

    # 产品包
    if grouping:
        groupings = Stb_grouping.query.filter(Stb_grouping.uuid.in_(grouping)).all()
        software.groupings = groupings
    else:
        # 数据空，删除已存在关系
        for d in software.groupings:
            software.groupings.remove(d)

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'电视盒软件 [%s] 数据更新成功!' % message}
        return jsonify(data)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'电视盒软件 [%s] 数据更新失败!' % message}
        return jsonify(data)

# 删除电视盒软件信息
@main.route('/api/tvbox_software', methods=['DELETE'])
@login_required
def delete_tvbox_software():
    # 获取请求参数
    uuid = request.json['uuid']

    # 返回消息
    message = []

    # 删除软件信息
    for i in uuid:
        software = Stb_software.query.filter(Stb_software.uuid==i).first()
        message.append(software.version)
        db.session.delete(software)

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'电视盒软件版本 [%s] 数据删除成功!' % ','.join(message)}
    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'电视盒软件版本 [%s] 数据删除失败!' % ','.join(message)}

    return jsonify(data)
