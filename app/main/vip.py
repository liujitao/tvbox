# -*- coding: utf-8 -*-

from flask import request, jsonify, render_template
from flask_login import login_required

from sqlalchemy import or_, func, desc, distinct, cast, case
from sqlalchemy.dialects.mysql import INTEGER, CHAR
from sqlalchemy.exc import IntegrityError

from datetime import datetime, timedelta
import uuid

from . import main
from .functions import *
from .selects import *

from ..models import Stb, Customer, Vip

# 获取所有会员卡信息
@main.route('/api/vip/list', methods=['GET'])
@login_required
def get_vip_list():
    # 获取请求参数
    draw = request.args['draw']
    start = request.args['start']
    length = request.args['length']
    search = request.args['search']
    order_name = request.args['order_name']
    order = request.args['order']

    # 查询
    query = Vip.query \
        .outerjoin(Stb, Vip.uuid == Stb.vip_uuid) \
        .outerjoin(Customer, Customer.uuid == Stb.customer_uuid) \
        .with_entities(Vip.uuid, Vip.category, Vip.effect_time, Vip.expire_time, Vip.create_time, Vip.update_time, \
            Stb.sn.label('stb'), Customer.name.label('customer'))

    # 搜索
    if search:
        query = query.filter(or_(
            Vip.category.in_(vip_type_to_id(search)),
            Stb.sn.like('%' + search + '%'),
            Customer.name.like('%' + search + '%'),
        ))

    # 排序
    if order == 'asc':
        if order_name == 'customer':
            query = query.order_by(cast(Customer.name, CHAR(charset='gbk')))
        else:
            query = query.order_by(order_name)
    else:
        if order_name == 'customer':
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
        'category': q.category,
        'stb': q.stb,
        'customer': q.customer,
        'effect_time': q.effect_time,
        'expire_time': q.expire_time,
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

# 获取指定会员卡信息
@main.route('/api/vip', methods=['GET'])
@login_required
def get_vip():
    # 获取请求参数
    uuid = request.args['uuid']

    # 查询
    q = Vip.query \
        .outerjoin(Stb, Vip.uuid == Stb.vip_uuid) \
        .with_entities(Vip.uuid, Vip.category, Stb.uuid.label('stb_uuid')) \
        .filter(Vip.uuid == uuid).first()

    data = {
        'uuid': q.uuid,
        'category': q.category,
        'stb_uuid': q.stb_uuid,
    }
    return jsonify(data)

# 新建会员卡信息
@main.route('/api/vip', methods=['POST'])
@login_required
def add_vip():
    # 获取请求参数
    category = request.json['category']
    count = request.json['count']

    # 返回消息
    message = count

    # 会员卡
    vips = [Vip(uuid=str(uuid.uuid1()), category=category, create_time=datetime.now()) for i in xrange(int(count))]
    db.session.add_all(vips)

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'会员卡 [%s] 条数据新建成功!' % message}
        return jsonify(data)

    except IntegrityError as e:
        db.session.rollback()
        print e
        data = {'msg': u'会员卡 [%s] 条数据新建失败!' % message}
        return jsonify(data)

# 更新会员卡信息
@main.route('/api/vip', methods=['PUT'])
@login_required
def update_vip():
    # 获取请求参数
    uuid = request.json['uuid']
    category = request.json['category']
    stb = request.json['stb']
    
    # 会员时间
    vip_time = [365*10, 30, 90, 365, 365*3]

    # 返回消息
    message = uuid

    # 会员卡
    vip = Vip().query.filter(Vip.uuid==uuid).first()
    if vip.effect_time is None:
        vip.effect_time = datetime.now()
        vip.expire_time = datetime.now() + timedelta(days=vip_time[int(category)])
    vip.update_time = datetime.now()

    # 更新关联电视盒
    vip.stbs = Stb.query.filter(Stb.uuid==stb).first()

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'会员卡 [%s] 数据更新成功!' % message}
        return jsonify(data)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'会员卡 [%s] 数据更新失败!' % message}
        return jsonify(data)

# 删除会员卡信息
@main.route('/api/vip', methods=['DELETE'])
@login_required
def delete_vip():
    # 获取请求参数
    uuid = request.json['uuid']

    # 返回消息
    message = []
    constraint = []

    # 删除信息
    for i in uuid:
        vip = Vip.query.filter(Vip.uuid==i).first()
        # 业务约束(电视盒关联)
        stb = Stb.query.filter(Stb.vip_uuid==i).first()
        if stb:
            constraint.append(vip.uuid)
        else:
            message.append(vip.uuid)
            db.session.delete(vip)

    # 提交数据库
    try:
        db.session.commit()
        if len(constraint) == 0:
            data = {'msg': u'会员卡 [%s] 条数据删除成功!' % len(message)}
        else:
            data = {'msg': u'会员卡 [%s] 条数据删除未成功，请先解除电视盒关联后再删除！' % len(constraint)}

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'客户数据删除失败!'}

    return jsonify(data)

