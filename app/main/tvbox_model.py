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

from ..models import Stb, Stb_model, Stb_software

# 获取所有电视盒型号信息
@main.route('/api/tvbox_model/list', methods=['GET'])
@login_required
def get_tvbox_model_list():
    # 获取请求参数
    draw = request.args['draw']
    start = request.args['start']
    length = request.args['length']
    search = request.args['search']
    order_name = request.args['order_name']
    order = request.args['order']

    # 子查询 - 每个电视盒型号指派的软件版本
    query_software = Stb_model.query \
        .outerjoin(Stb_software, Stb_model.uuid==Stb_software.model_uuid) \
        .with_entities(Stb_model.uuid) \
        .add_columns(func.group_concat(Stb_software.version).label('software')) \
        .group_by(Stb_model.uuid) \
        .subquery()

    # 子查询 - 每个电视盒型号指派的电视盒
    query_stb = Stb_model.query \
        .outerjoin(Stb, Stb_model.code==Stb.model) \
        .with_entities(Stb_model.uuid) \
        .add_columns(func.count(Stb.sn).label('stb')) \
        .group_by(Stb_model.uuid) \
        .subquery()

    # 子查询 - 每个电视盒型号指派的app
    query_app = Stb_model.query \
        .outerjoin(App, Stb_model.code==App.model) \
        .with_entities(Stb_model.uuid) \
        .add_columns(func.count(App.app_id).label('app')) \
        .group_by(Stb_model.uuid) \
        .subquery()

    # 联合查询
    query = Stb_model.query \
        .join(query_software, query_software.c.uuid == Stb_model.uuid) \
        .join(query_stb, query_stb.c.uuid == Stb_model.uuid) \
        .join(query_app, query_app.c.uuid == Stb_model.uuid) \
        .with_entities(Stb_model.uuid, Stb_model.code, Stb_model.name, Stb_model.cname, Stb_model.create_time, Stb_model.update_time) \
        .add_columns(query_software.c.software, query_stb.c.stb, query_app.c.app) 

    # 搜索
    if search:
        query = query \
            .filter(or_(
                Stb_model.code.like('%' + search + '%'),
                Stb_model.name.like('%' + search + '%')))

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
        'code': q.code,
        'name': q.name,
        'cname': q.cname,
        'software': q.software,
        'stb': q.stb,
        'app': q.app,
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

# 获取指定电视盒型号信息
@main.route('/api/tvbox_model', methods=['GET'])
@login_required
def get_tvbox_model():
    # 获取请求参数
    uuid = request.args['uuid']
    
    # 子查询 - 每个电视盒型号指派的软件版本
    query_software = Stb_model.query \
        .join(Stb_software) \
        .with_entities(Stb_model.uuid) \
        .add_columns(func.group_concat(Stb_software.version).label('software')) \
        .group_by(Stb_model.uuid) \
        .subquery()

    # 子查询 - 每个电视盒型号指派的电视盒
    query_stb = Stb_model.query \
        .join(Stb) \
        .with_entities(Stb_model.uuid) \
        .add_columns(func.count(Stb.sn).label('stb')) \
        .group_by(Stb_model.uuid) \
        .subquery()

    # 子查询 - 每个电视盒型号指派的app
    query_app = Stb_model.query \
        .join(App) \
        .with_entities(Stb_model.uuid) \
        .add_columns(func.count(App.app_id).label('app')) \
        .group_by(Stb_model.uuid) \
        .subquery()

    # 联合查询
    q = Stb_model.query \
        .join(query_software, query_software.c.uuid == Stb_model.uuid) \
        .join(query_stb, query_stb.c.uuid == Stb_model.uuid) \
        .join(query_app, query_stb.c.uuid == Stb_model.uuid) \
        .with_entities(Stb_model.uuid, Stb_model.code, Stb_model.name, Stb_model.cname, Stb_model.create_time, Stb_model.update_time) \
        .add_columns(query_software.c.software, query_stb.c.stb, query_app.c.app) \
        .filter(Stb_model.uuid==uuid) \
        .first()

    data = {
        'uuid': q.uuid,
        'code': q.code,
        'name': q.name,
        'cname': q.cname,
        'software': q.software,
        'stb': q.stb,
        'app': q.app,
        'create_time': q.create_time,
        'update_time': q.update_time,
    }

    return jsonify(data)

# 新建电视盒型号信息
@main.route('/api/tvbox_model', methods=['POST'])
@login_required
def add_tvbox_model():
    # 获取请求参数
    code = request.json['code']
    name = request.json['name']
    cname = request.json['cname']

    # 返回消息
    message = name

    # 电视盒型号
    model = Stb_model()
    model.uuid = str(uuid.uuid1())
    model.code = code
    model.name = name
    model.cname = cname
    model.create_time = datetime.now()
    
    db.session.add(model)

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'电视盒型号 [%s] 数据新建成功!' % message}
        return jsonify(data)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'电视盒型号 [%s] 数据新建失败!' % message}
        return jsonify(data)

# 更新电视盒型号信息
@main.route('/api/tvbox_model', methods=['PUT'])
@login_required
def update_tvbox_model():
    # 获取请求参数
    uuid = request.json['uuid']
    code = request.json['code']
    name = request.json['name']
    cname = request.json['cname']

    # 返回消息
    message = name
    
    # 电视盒型号
    model = Stb_model.query.filter(Stb_model.uuid==uuid).first()
    model.code = code
    model.name = name
    model.cname = cname
    model.update_time = datetime.now()

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'电视盒型号 [%s] 数据更新成功!' % message}
        return jsonify(data)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'电视盒型号 [%s] 数据更新失败!' % message}
        return jsonify(data)

# 删除电视盒型号信息
@main.route('/api/tvbox_model', methods=['DELETE'])
@login_required
def delete_tvbox_model():
    # 获取请求参数
    uuid = request.json['uuid']

    # 返回消息
    message = []

    # 删除信息
    message = [model.code for model in Stb_model.query.filter(Stb_model.uuid.in_(uuid)).all()]
    db.session.query(Stb_model).filter(Stb_model.uuid.in_(uuid)).delete(synchronize_session=False)

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'电视盒型号 [%s] 数据删除成功!' % ','.join(message)}

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'电视盒型号数据删除失败!'}

    return jsonify(data)

# 获取指定硬件型号关联电视盒信息
@main.route('/api/tvbox_model/tvbox', methods=['GET'])
@login_required
def get_tvbox_model_tvbox():
    # 获取请求参数
    uuid = request.args['uuid']
    
    data = [ q.sn for q in Stb_model.query.join(Stb, Stb.model==Stb_model.code) \
        .with_entities(Stb.sn).filter(Stb_model.uuid==uuid).order_by(Stb.sn).all()]

    return jsonify(data)

# 获取指定硬件型号关联app信息
@main.route('/api/tvbox_model/app', methods=['GET'])
@login_required
def get_tvbox_model_app():
    # 获取请求参数
    uuid = request.args['uuid']
    
    data = [ q.app_id for q in Stb_model.query.join(App, App.model==Stb_model.code) \
        .with_entities(App.app_id).filter(Stb_model.uuid==uuid).order_by(App.app_id).all()]

    return jsonify(data)