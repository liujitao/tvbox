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

from ..models import Stb, Stb_software, Stb_grouping, softwares_groupings

# 获取所有电视盒分组信息
@main.route('/api/tvbox_grouping/list', methods=['GET'])
@login_required
def get_tvbox_grouping_list():
    # 获取请求参数
    draw = request.args['draw']
    start = request.args['start']
    length = request.args['length']
    search = request.args['search']
    order_name = request.args['order_name']
    order = request.args['order']

    # 子查询 - 每个电视盒分组指派的软件版本
    query_software = Stb_grouping.query \
        .join(softwares_groupings).join(Stb_software) \
        .with_entities(Stb_grouping.uuid) \
        .add_columns(func.group_concat(Stb_software.version).label('software')) \
        .group_by(Stb_grouping.uuid) \
        .subquery()

    # 子查询 - 每个电视盒分组指派的电视盒
    query_stb = Stb_grouping.query \
        .join(Stb, Stb.grouping_uuid==Stb_grouping.uuid) \
        .with_entities(Stb_grouping.uuid) \
        .add_columns(func.count(Stb.sn).label('stb')) \
        .group_by(Stb_grouping.uuid) \
        .subquery()

    # 联合查询
    query = Stb_grouping.query \
        .outerjoin(query_software, query_software.c.uuid == Stb_grouping.uuid) \
        .outerjoin(query_stb, query_stb.c.uuid == Stb_grouping.uuid) \
        .with_entities(Stb_grouping.uuid, Stb_grouping.cname, Stb_grouping.description, Stb_grouping.create_time, Stb_grouping.update_time) \
        .add_columns(query_software.c.software, query_stb.c.stb)
    # 搜索

    # 排序
    if order == 'asc':
        if order_name == 'cname':
            query = query.order_by(cast(Stb_grouping.cname, CHAR(charset='gbk')))
        else:
            query = query.order_by(order_name)
    else:
        if order_name == 'cname':
            query = query.order_by(desc(cast(Stb_grouping.cname, CHAR(charset='gbk'))))
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
        'description': q.description,
        'software': q.software,
        'stb': q.stb,
        'create_time': q.create_time,
        'update_time': q.update_time,
    } for q in query.items]

    return jsonify(
        {
            'draw': int(draw),
            'recordsTotal': total,
            'recordsFiltered': total,
            'data': data
        }
    )

# 获取指定电视盒分组信息
@main.route('/api/tvbox_grouping', methods=['GET'])
@login_required
def get_tvbox_grouping():
    # 获取请求参数
    uuid = request.args['uuid']
    
    # 子查询 - 每个电视盒分组指派的软件版本
    query_software = Stb_grouping.query \
        .join(softwares_groupings).join(Stb_software) \
        .with_entities(Stb_grouping.uuid) \
        .add_columns(func.group_concat(Stb_software.version).label('software')) \
        .group_by(Stb_grouping.uuid) \
        .subquery()

    # 子查询 - 每个电视盒分组指派的电视盒
    query_stb = Stb_grouping.query \
        .join(Stb, Stb.grouping_uuid==Stb_grouping.uuid) \
        .with_entities(Stb_grouping.uuid) \
        .add_columns(func.count(Stb.sn).label('stb')) \
        .group_by(Stb_grouping.uuid) \
        .subquery()

    # 联合查询
    q = Stb_grouping.query \
        .outerjoin(query_software, query_software.c.uuid == Stb_grouping.uuid) \
        .outerjoin(query_stb, query_stb.c.uuid == Stb_grouping.uuid) \
        .with_entities(Stb_grouping.uuid, Stb_grouping.cname, Stb_grouping.description, Stb_grouping.create_time, Stb_grouping.update_time) \
        .add_columns(query_software.c.software, query_stb.c.stb) \
        .filter(Stb_grouping.uuid==uuid) \
        .first()

    data = {
        'uuid': q.uuid,
        'cname': q.cname,
        'description': q.description,
        'software': q.software,
        'stb': q.stb,
        'create_time': q.create_time,
        'update_time': q.update_time,
    }

    return jsonify(data)

# 新建电视盒分组信息
@main.route('/api/tvbox_grouping', methods=['POST'])
@login_required
def add_tvbox_grouping():
    # 获取请求参数
    cname = request.json['cname']
    description = request.json['description']

    # 返回消息
    message = cname

    # 电视盒分组
    model = Stb_grouping()
    model.uuid = str(uuid.uuid1())
    model.cname = cname
    model.description = description
    model.create_time = datetime.now()
    
    db.session.add(model)

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'电视盒分组 [%s] 数据新建成功!' % message}
        return jsonify(data)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'电视盒分组 [%s] 数据新建失败!' % message}
        return jsonify(data)

# 更新电视盒分组信息
@main.route('/api/tvbox_grouping', methods=['PUT'])
@login_required
def update_tvbox_grouping():
    # 获取请求参数
    uuid = request.json['uuid']
    cname = request.json['cname']
    description = request.json['description']

    # 返回消息
    message =cname
    
    # 电视盒分组
    model = Stb_grouping.query.filter(Stb_grouping.uuid==uuid).first()
    model.cname = cname
    model.description = description
    model.update_time = datetime.now()

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'电视盒分组 [%s] 数据更新成功!' % message}
        return jsonify(data)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'电视盒分组 [%s] 数据更新失败!' % message}
        return jsonify(data)

# 删除电视盒分组信息
@main.route('/api/tvbox_grouping', methods=['DELETE'])
@login_required
def delete_tvbox_grouping():
    # 获取请求参数
    uuid = request.json['uuid']

    # 返回消息
    message = []
    constraint = []

    # 删除信息
    for i in uuid:
        grouping = Stb_grouping.query.filter(Stb_grouping.uuid==i).first()
        # 业务约束(电视盒关联)
        stb = Stb.query.filter(Stb.grouping_uuid==i).first()
        if stb:
            constraint.append(grouping.cname)
        else:
            message.append(grouping.cname)
            db.session.delete(grouping)

    # 提交数据库
    try:
        db.session.commit()
        if len(constraint) == 0:
            data = {'msg': u'电视盒分组 [%s] 数据删除成功!' % ','.join(message)}
        else:
            data = {'msg': u'电视盒分组 [%s] 数据删除未成功，请先解除电视盒关联后再删除！' % ','.join(constraint)}

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'电视盒分组数据删除失败!'}

    return jsonify(data)

# 获取指定分组关联电视盒信息
@main.route('/api/tvbox_grouping/tvbox', methods=['GET'])
@login_required
def get_tvbox_grouping_tvbox():
    # 获取请求参数
    uuid = request.args['uuid']
    
    data = [ q.sn for q in Stb_grouping.query.join(Stb, Stb.grouping_uuid==Stb_grouping.uuid) \
        .with_entities(Stb.sn).filter(Stb_grouping.uuid==uuid).order_by(Stb.sn).all()]

    return jsonify(data)