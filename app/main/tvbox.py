# -*- coding: utf-8 -*-
from flask import request, jsonify, render_template, current_app, redirect, url_for
from flask_login import login_required

from sqlalchemy import or_, func, desc, distinct, cast, case
from sqlalchemy.dialects.mysql import INTEGER, CHAR
from sqlalchemy.exc import IntegrityError

from datetime import datetime, timedelta
import uuid, os

from . import main
from .functions import *
from ..models import *

from .. import redis_store

# 上传csv文件
@main.route('/api/tvbox/upload',methods = ['POST'])
@login_required
def upload_tvbox():
    if request.method == 'POST':
        size = current_app.config['UPLOAD_MAX_SIZE']
        ext = ['csv', 'txt']

        file = request.files.get('csv', None)
        if file and file.filename.split('.')[1] in ext:
            return jsonify({'data': file.read()})
        else:
            return jsonify({'data': u'不支持的文件类型，仅支持csv txt'}) 
    else:
        # 返回404错误
        return jsonify({'msg': '404'})
  
# 批量导入电视盒
@main.route('/api/tvbox/import',methods = ['POST'])
@login_required
def import_tvbox():
    # 获取请求参数
    content = request.json['content']

    # 返回消息
    message = 0

    # 电视盒
    stbs = []
    vip_time = [365*10, 30, 90, 365, 365*3]
    
    for line in content.strip().split('\r\n'):
        if not line.startswith('#'):
            sn, customer, product, vip, partner, grouping = line.split(',')
            stb = Stb()
            stb.uuid = str(uuid.uuid1())
            stb.sn = sn
            stb.create_time = datetime.now()

            if partner:
                stb.partner_uuid = partner
            
            if grouping:
                stb.grouping_uuid = grouping

            # 关联产品包
            products = Channel_product.query.filter(Channel_product.uuid==product).all()
            stb.products = products

            # 关联购买人
            if customer:
                c = Customer.query.filter(Customer.name==customer).first()
                if c:
                    stb.customer_uuid = c.uuid
                else:
                    new_customer = Customer(uuid=str(uuid.uuid1()), name=customer, create_time=datetime.now())
                    db.session.add(new_customer)
                    stb.customer_uuid = new_customer.uuid

            # 关联会员
            if vip in ['0', '1', '2', '3', '4']:
                vip_uuid = str(uuid.uuid1())
                v = Vip(uuid=vip_uuid, category=vip, create_time=datetime.now(), effect_time=datetime.now(), expire_time=datetime.now() + timedelta(days=vip_time[int(vip)]))
                db.session.add(v)
                stb.vip_uuid = vip_uuid
            stbs.append(stb)

    db.session.add_all(stbs)
    message = len(stbs)
    
    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'电视盒 [%s] 数据新建成功!' % message}
        return jsonify(data)

    except IntegrityError as e:
        print e
        db.session.rollback()
        data = {'msg': u'电视盒 [%s] 数据新建失败!' % message}
        return jsonify(data)

# 获取所有电视盒信息
@main.route('/api/tvbox/list', methods=['GET'])
@login_required
def get_tvbox_list():
    # 获取请求参数
    draw = request.args['draw']
    start = request.args['start']
    length = request.args['length']
    search = request.args['search']
    order_name = request.args['order_name']
    order = request.args['order']

    # 联合查询 (不用子查询)
    query = Stb.query \
        .outerjoin(Customer, Stb.customer_uuid == Customer.uuid) \
        .outerjoin(Vip, Stb.vip_uuid == Vip.uuid) \
        .outerjoin(Partner, Stb.partner_uuid == Partner.uuid) \
        .outerjoin(Stb_grouping, Stb.grouping_uuid == Stb_grouping.uuid) \
        .outerjoin(Live_node, Stb.live_node_uuid == Live_node.uuid) \
        .join(stbs_products).join(Channel_product) \
        .group_by(Stb.uuid) \
        .with_entities(Stb.uuid, Stb.sn, Stb.model, Stb.version, Stb.status, Stb.create_time, Stb.update_time, Stb.purchase_time, Stb.access_location, Stb.access_ip, Stb.access_time) \
        .add_columns(Customer.name.label('customer'), Vip.category.label('vip'), Partner.cname.label('partner'), Stb_grouping.cname.label('grouping'), \
            Live_node.cname.label('live_node'), func.group_concat(Channel_product.cname).label('product'))

    # 搜索
    if search:
        query = query \
            .filter(or_(
                Stb.sn.like('%' + search + '%'),
                Stb.model.like('%' + search + '%'),
                Customer.name.like('%' + search + '%'),
                Stb_grouping.cname.like('%' + search + '%'),
                Stb.purchase_time.like('%' + search + '%'),
                Stb.access_location.like('%' + search + '%'),
                Stb.access_time.like('%' + search + '%'),   
                Live_node.cname.like('%' + search + '%'),
                Vip.category.in_(vip_type_to_id(search)),
                Stb.status.in_(stb_status_to_id(search))))

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
        'sn': q.sn,
        'model': q.model,
        'version': q.version,
        'customer': q.customer,
        'purchase_time': q.purchase_time,
        'product': q.product,
        'vip': q.vip,
        'partner': q.partner,
        'grouping': q.grouping,
        'access_location': q.access_location,
        'access_ip': q.access_ip,
        'access_time': q.access_time,
        'live_node': q.live_node,
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

# 获取指定电视盒信息
@main.route('/api/tvbox', methods=['GET'])
@login_required
def get_tvbox():
    # 获取请求参数
    uuid = request.args['uuid']

    # 子查询 - 每个电视盒指派产品包的uuid
    query_product = Stb.query \
        .join(stbs_products).join(Channel_product) \
        .with_entities(Stb.uuid, Channel_product.cname) \
        .add_columns(func.group_concat(Channel_product.uuid).label('product_uuid')) \
        .group_by(Stb.uuid) \
        .filter(Stb.uuid == uuid) \
        .subquery()

    # 联合查询
    query = Stb.query \
        .outerjoin(Customer, Stb.customer_uuid == Customer.uuid) \
        .outerjoin(Vip, Stb.vip_uuid == Vip.uuid) \
        .outerjoin(Partner, Stb.partner_uuid == Partner.uuid) \
        .outerjoin(Stb_grouping, Stb.grouping_uuid == Stb_grouping.uuid) \
        .outerjoin(Live_node, Stb.live_node_uuid == Live_node.uuid) \
        .outerjoin(query_product, Stb.uuid == query_product.c.uuid) \
        .with_entities(Stb.uuid, Stb.sn, Stb.model, Stb.version, Stb.status, Stb.create_time, Stb.update_time, Stb.purchase_time, Stb.access_location, Stb.access_ip, Stb.access_time) \
        .add_columns(Customer.uuid.label('customer_uuid'), Vip.uuid.label('vip_uuid'), Partner.uuid.label('partner_uuid'), \
            Stb_grouping.uuid.label('grouping_uuid'), Live_node.uuid.label('live_uuid'), query_product.c.product_uuid) \
        .filter(Stb.uuid == uuid).first()

    data = {
        'uuid': query.uuid,
        'sn': query.sn,
        'model': query.model,
        'version': query.version,
        'purchase_time': query.purchase_time,
        'access_location': query.access_location,
        'access_ip': query.access_ip,
        'access_time': query.access_time,
        'status': query.status,
        'create_time': query.create_time,
        'update_time': query.update_time,
        'customer_uuid': query.customer_uuid,
        'vip_uuid': query.vip_uuid,
        'partner_uuid': query.partner_uuid,
        'grouping_uuid': query.grouping_uuid,
        'live_node_uuid': query.live_uuid,
        'product_uuid': query.product_uuid
    }

    return jsonify(data)

# 新建电视盒信息
@main.route('/api/tvbox', methods=['POST'])
@login_required
def add_tvbox():
    # 获取请求参数
    sn = request.json['sn']
    customer = request.json['customer']
    product = request.json['product']
    partner = request.json['partner']
    grouping = request.json['grouping']
    status = request.json['status']

    # 返回消息
    message = sn

    # 电视盒
    stb = Stb()
    stb.uuid = str(uuid.uuid1())
    stb.sn = sn
    stb.customer_uuid = customer
    stb.partner_uuid = partner
    stb.grouping_uuid = grouping
    stb.status = status
    stb.create_time = datetime.now()

    db.session.add(stb)

    # 产品包
    if product:
        products = Channel_product.query.filter(Channel_product.uuid.in_(product)).all()
        stb.products = products
    
    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'电视盒 [%s] 数据新建成功!' % message}
        return jsonify(data)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'电视盒 [%s] 数据新建失败!' % message}
        return jsonify(data)

# 更新redis
@login_required
def reset_stb_streamcode(sn):
    if sn is None or sn == "":
        return u"参数不能为空."

    signature = redis_store.hget(sn, "signature")
    if signature is None:
        return u"redis中签名为空"

    token = redis_store.get(signature)
    if token is None:
        redis_store.delete(sn)
        return u"redis中token为空"

    redis_store.delete(token)
    redis_store.delete(signature)
    redis_store.delete(sn)

# 更新指定电视盒信息
@main.route('/api/tvbox', methods=['PUT'])
@login_required
def update_tvbox():
    # 获取请求参数
    uuid = request.json['uuid']
    sn = request.json['sn']
    customer = request.json['customer']
    product = request.json['product']
    partner = request.json['partner']
    grouping = request.json['grouping']
    live_node = request.json['live_node']
    status = request.json['status']

    # 返回消息
    message = sn

    # 电视盒
    stb = Stb.query.filter(Stb.uuid == uuid).first()
    stb.sn = sn
    stb.customer_uuid = customer
    stb.partner_uuid = partner
    stb.grouping_uuid = grouping
    stb.live_node_uuid = live_node
    stb.status = status
    stb.update_time = datetime.now()

    # 清空redis
    reset_stb_streamcode(sn)

    # 产品包
    if product:
        products = Channel_product.query.filter(Channel_product.uuid.in_(product)).all()
        stb.products = products
    else:
        # 数据空，删除已存在关系
        for d in stb.products:
            stb.products.remove(d)

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'电视盒 [%s] 数据更新成功!' % message}
        return jsonify(data)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'电视盒 [%s] 数据更新失败!' % message}
        return jsonify(data)

# 删除指定电视盒信息
@main.route('/api/tvbox', methods=['DELETE'])
@login_required
def delete_tvbox():
    # 获取请求参数
    uuid = request.json['uuid']

    # 返回消息
    message = []
    constraint = []

    # 删除信息
    for i in uuid:
        stb = Stb.query.filter(Stb.uuid==i).first()
        # 业务约束(会员卡关联)
        if stb.vip_uuid:
            constraint.append(stb.sn)
        else:
            message.append(stb.sn)
            db.session.delete(stb)

    # 提交数据库
    try:
        db.session.commit()
        if len(constraint) == 0:
            data = {'msg': u'电视盒 [%s] 数据删除成功!' % ','.join(message)}
        else:
            data = {'msg': u'电视盒 [%s] 数据删除未成功，请先解除会员卡关联后再删除！' % ','.join(constraint)}

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'电视盒数据删除失败!'}

    return jsonify(data)

# 获取指定电视盒关联的用户信息
@main.route('/api/tvbox/customer', methods=['GET'])
@login_required
def get_tvbox_customer():
    # 获取请求参数
    uuid = request.args['uuid']

    # 联合查询
    query = Stb.query \
        .outerjoin(Customer, Stb.customer_uuid == Customer.uuid) \
        .with_entities(Customer.uuid, Customer.name, Customer.phone, Customer.mail, Customer.address, \
            Customer.description, Customer.create_time, Customer.update_time) \
        .filter(Stb.uuid == uuid).first()

    data = {
        'uuid': query.uuid,
        'name': query.name,
        'phone': query.phone,
        'mail': query.mail,
        'address': query.address,
        'description': query.description,
        'create_time': query.create_time,
        'update_time': query.update_time
    }

    return jsonify(data)