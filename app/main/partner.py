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

from ..models import Stb, Partner

# 获取所合作商信息
@main.route('/api/partner/list', methods=['GET'])
@login_required
def get_partner_list():
    # 获取请求参数
    draw = request.args['draw']
    start = request.args['start']
    length = request.args['length']
    search = request.args['search']
    order_name = request.args['order_name']
    order = request.args['order']

    # 查询
    query = Partner.query \
        .outerjoin(Stb, Partner.uuid == Stb.partner_uuid) \
        .with_entities(Partner.uuid, Partner.name, Partner.cname, Partner.logo_url, Partner.create_time, Partner.update_time) \
        .add_columns(func.count(Stb.sn).label('stb')) \
        .group_by(Partner.uuid)

    # 搜索
    if search:
        query = query.filter(or_(
            Partner.name.like('%' + search + '%'),
            Partner.cname.like('%' + search + '%')
        ))

    # 排序
    if order == 'asc':
        if order_name == 'cname':
            query = query.order_by(cast(Partner.cname, CHAR(charset='gbk')))
        else:
            query = query.order_by(order_name)
    else:
        if order_name == 'cname':
            query = query.order_by(desc(cast(Partner.cname, CHAR(charset='gbk'))))
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
        'logo_url': q.logo_url,
        'stb': q.stb,
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

# 获取指定合作商信息
@main.route('/api/partner', methods=['GET'])
@login_required
def get_partner():
    # 获取请求参数
    uuid = request.args['uuid']

    # 查询
    q = Partner.query \
        .outerjoin(Stb, Partner.uuid == Stb.partner_uuid) \
        .with_entities(Partner.uuid, Partner.name, Partner.cname, Partner.logo_url, Partner.create_time, Partner.update_time) \
        .group_by(Partner.uuid) \
        .filter(Partner.uuid == uuid).first()

    data = {
        'uuid': q.uuid,
        'name': q.name,
        'cname': q.cname,
        'logo_url': q.logo_url,
        'create_time': q.create_time,
        'update_time': q.update_time
    }

    return jsonify(data)

# 新建合作商信息
@main.route('/api/partner', methods=['POST'])
@login_required
def add_partner():
    # 获取请求参数
    name = request.json['name']
    cname = request.json['cname']
    logo_url = request.json['logo_url']

    # 返回消息
    message = cname

    # 合作商
    partner = Partner()
    partner.uuid = str(uuid.uuid1())
    partner.name = name
    partner.cname = cname
    partner.logo_url = logo_url
    partner.create_time = datetime.now()

    db.session.add(partner)

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'合作商 [%s] 数据新建成功!' % message}
        return jsonify(data)

    except IntegrityError as e:
        db.session.rollback()
        print e
        data = {'msg': u'合作商 [%s] 数据新建失败!' % message}
        return jsonify(data)

# 更新合作商信息
@main.route('/api/partner', methods=['PUT'])
@login_required
def update_partner():
    # 获取请求参数
    uuid = request.json['uuid']
    name = request.json['name']
    cname = request.json['cname']
    logo_url = request.json['logo_url']

    # 返回消息
    message = cname

    # 合作商
    partner = Partner().query.filter(Partner.uuid == uuid).first()
    partner.name = name
    partner.cname = cname
    partner.logo_url = logo_url
    partner.update_time = datetime.now()

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'合作商 [%s] 数据更新成功!' % message}
        return jsonify(data)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'合作商 [%s] 数据更新失败!' % message}
        return jsonify(data)

# 删除合作商信息
@main.route('/api/partner', methods=['DELETE'])
@login_required
def delete_partner():
    # 获取请求参数
    uuid = request.json['uuid']

    # 返回消息
    message = []
    constraint = []

    # 删除信息
    for i in uuid:
        partner = Partner.query.filter(Partner.uuid==i).first()
        # 业务约束(电视盒关联)
        stb = Stb.query.filter(Stb.partner_uuid==i).first()
        if stb:
            constraint.append(partner.cname)
        else:
            message.append(partner.cname)
            db.session.delete(partner)

    # 提交数据库
    try:
        db.session.commit()
        if len(constraint) == 0:
            data = {'msg': u'合作商 [%s] 数据删除成功!' % ','.join(message)}
        else:
            data = {'msg': u'合作商 [%s] 数据删除成功，合作商 [%s] 请先解除电视盒关联后再删除！' % (','.join(message), ','.join(constraint))}

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'合作商数据删除失败!'}

    return jsonify(data)