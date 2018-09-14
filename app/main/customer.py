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

from ..models import Stb, Customer

# 获取所客户信息
@main.route('/api/customer/list', methods=['GET'])
@login_required
def get_customer_list():
    # 获取请求参数
    draw = request.args['draw']
    start = request.args['start']
    length = request.args['length']
    search = request.args['search']
    order_name = request.args['order_name']
    order = request.args['order']

    # 查询
    query = Customer.query \
        .outerjoin(Stb, Customer.uuid == Stb.customer_uuid) \
        .with_entities(Customer.uuid, Customer.name, Customer.phone, Customer.mail, Customer.address, Customer.description, Customer.create_time, Customer.update_time) \
        .add_columns(func.group_concat(Stb.sn).label('stb')) \
        .group_by(Customer.uuid)

    # 搜索
    if search:
        query = query.filter(or_(
            Customer.name.like('%' + search + '%'),
            Customer.phone.like('%' + search + '%'),
            Customer.mail.like('%' + search + '%'),
            Customer.description.like('%' + search + '%'),
        ))

    # 排序
    if order == 'asc':
        if order_name == 'name':
            query = query.order_by(cast(Customer.name, CHAR(charset='gbk')))
        else:
            query = query.order_by(order_name)
    else:
        if order_name == 'name':
            query = query.order_by(desc(cast(Customer.name, CHAR(charset='gbk'))))
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
        'phone': q.phone,
        'mail': q.mail,
        'address': q.address,
        'description': q.description,
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

# 获取指定客户信息
@main.route('/api/customer', methods=['GET'])
@login_required
def get_customer():
    # 获取请求参数
    uuid = request.args['uuid']

    # 查询
    q = Customer.query \
        .outerjoin(Stb, Customer.uuid == Stb.customer_uuid) \
        .with_entities(Customer.uuid, Customer.name, Customer.phone, Customer.mail, Customer.address, Customer.description, Customer.create_time, Customer.update_time) \
        .add_columns(func.group_concat(Stb.uuid).label('stb_uuid')) \
        .group_by(Customer.uuid) \
        .filter(Customer.uuid == uuid).first()

    data = {
        'uuid': q.uuid,
        'name': q.name,
        'phone': q.phone,
        'mail': q.mail,
        'address': q.address,
        'description': q.description,
        'stb_uuid': q.stb_uuid,
        'create_time': q.create_time,
        'update_time': q.update_time
    }

    return jsonify(data)

# 新建客户信息
@main.route('/api/customer', methods=['POST'])
@login_required
def add_customer():
    # 获取请求参数
    name = request.json['name']
    phone = request.json['phone']
    mail = request.json['mail']
    address = request.json['address']
    description = request.json['description']
    stb = request.json['stb']

    # 返回消息
    message = name

    # 客户
    customer = Customer()
    customer.uuid = str(uuid.uuid1())
    customer.name = name
    customer.phone = phone
    customer.mail = mail
    customer.address = address
    customer.description = description
    customer.create_time = datetime.now()

    if len(stb) > 0:
        stbs = Stb.query.filter(Stb.sn.in_(stb)).all()
        customer.stbs = stbs

    db.session.add(customer)

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'客户 [%s] 数据新建成功!' % message}
        return jsonify(data)

    except IntegrityError as e:
        db.session.rollback()
        print e
        data = {'msg': u'客户 [%s] 数据新建失败!' % message}
        return jsonify(data)

# 更新客户信息
@main.route('/api/customer', methods=['PUT'])
@login_required
def update_customer():
    # 获取请求参数
    uuid = request.json['uuid']
    name = request.json['name']
    phone = request.json['phone']
    mail = request.json['mail']
    address = request.json['address']
    description = request.json['description']
    stb = request.json['stb']

    # 返回消息
    message = name

    # 客户
    customer = Customer().query.filter(Customer.uuid == uuid).first()
    customer.name = name
    customer.phone = phone
    customer.mail = mail
    customer.address = address
    customer.description = description
    customer.update_time = datetime.now()

    # 更新电视盒关联
    if len(stb) > 0:
        local = [s.sn for s in Stb.query.filter(
            Stb.customer_uuid == uuid).all()]
        add = list(set(stb) - set(local))
        remove = list(set(local) - set(stb))

        if len(add) > 0:
            customer.stbs = Stb.query.filter(Stb.sn.in_(add)).all()

        if len(remove) > 0:
            for d in Stb.query.filter(Stb.sn.in_(remove)).all():
                customer.stbs.remove(d)

    else:
        # 数据空，删除已存在关系
        for d in customer.stbs:
            customer.stbs.remove(d)

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'客户 [%s] 数据更新成功!' % message}
        return jsonify(data)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'客户 [%s] 数据更新失败!' % message}
        return jsonify(data)

# 删除客户信息
@main.route('/api/customer', methods=['DELETE'])
@login_required
def delete_customer():
    # 获取请求参数
    uuid = request.json['uuid']

    # 返回消息
    message = []
    constraint = []

    # 删除信息
    for i in uuid:
        customer = Customer.query.filter(Customer.uuid==i).first()
        # 业务约束(电视盒关联)
        stb = Stb.query.filter(Stb.customer_uuid==i).first()
        if stb:
            constraint.append(customer.name)
        else:
            message.append(customer.name)
            db.session.delete(customer)

    # 提交数据库
    try:
        db.session.commit()
        if len(constraint) == 0:
            data = {'msg': u'客户 [%s] 数据删除成功!' % ','.join(message)}
        else:
            data = {'msg': u'客户 [%s] 数据删除成功，客户 [%s] 请先解除电视盒关联后再删除！' % (','.join(message), ','.join(constraint))}

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'客户数据删除失败!'}

    return jsonify(data)
