# -*- coding: utf-8 -*-
from flask import request, jsonify, render_template, current_app, redirect, url_for
from werkzeug.security import check_password_hash
from flask_login import login_required

from sqlalchemy import or_, func, desc
from sqlalchemy.exc import IntegrityError

from datetime import datetime
import uuid, os

from . import main
from .functions import *
from .selects import *

from ..models import App, Channel_product, apps_products, Live_node

# 上传csv文件
@main.route('/api/app/upload',methods = ['POST'])
@login_required
def upload_app():
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
  
# 批量导入app帐号
@main.route('/api/app/import',methods = ['POST'])
@login_required
def import_app():
    # 获取请求参数
    content = request.json['content']

    # 返回消息
    message = 0

    # app帐号
    apps = []
    for line in content.strip().split('\r\n'):
        if not line.startswith('#'):
            app_id, password, product, status = line.split(',')
            app = App()
            app.uuid = str(uuid.uuid1())
            app.app_id =app_id
            app.password = password
            app.status = status
            app.create_time = datetime.now()

            # 关联产品包
            products = Channel_product.query.filter(Channel_product.uuid==product).all()
            app.products = products
            apps.append(app)

    db.session.add_all(apps)
    message = len(apps)
    
    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'app帐号 [%s] 数据新建成功!' % message}
        return jsonify(data)

    except IntegrityError as e:
        print e
        db.session.rollback()
        data = {'msg': u'app帐号 [%s] 数据新建失败!' % message}
        return jsonify(data)

# 获取所有app帐号信息
@main.route('/api/app/list', methods=['GET'])
@login_required
def get_app_list():
    # 获取请求参数
    draw = request.args['draw']
    start = request.args['start']
    length = request.args['length']
    search = request.args['search']
    order_name = request.args['order_name']
    order = request.args['order']

    '''
    # 子查询 - 每个app帐号指派的产品包
    query_product = App.query \
        .join(apps_products).join(Channel_product) \
        .with_entities(App.uuid) \
        .add_columns(func.group_concat(Channel_product.cname).label('product')) \
        .group_by(App.uuid) \
        .subquery()
    '''

    # 联合查询
    query = App.query \
        .outerjoin(Live_node, App.live_node_uuid == Live_node.uuid) \
        .join(apps_products).join(Channel_product) \
        .group_by(App.uuid) \
        .with_entities(App.uuid, App.app_id, App.name, App.password_hash, App.model, App.version, App.status, App.create_time, App.update_time, App.first_time, App.access_location, App.access_ip, App.access_time) \
        .add_columns(Live_node.cname.label('live_node'), func.group_concat(Channel_product.cname).label('product'))

    # 搜索
    if search:
        query = query \
            .filter(or_(
                App.app_id.like('%' + search + '%'),
                App.name.like('%' + search + '%'),
                App.version.like('%' + search + '%'),
                App.access_location.like('%' + search + '%'),
                App.access_time.like('%' + search + '%'),
                App.status.in_(status_to_id(search))))

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
        'app_id': q.app_id,
        'name': q.name,
        'password_hash': q.password_hash,
        'model': q.model,
        'version': q.version,
        'product': q.product,
        'first_time': q.first_time,
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

# 获取指定app帐号信息
@main.route('/api/app', methods=['GET'])
@login_required
def get_app():
    # 获取请求参数
    uuid = request.args['uuid']

    # 子查询 - 每个app帐号指派产品包的uuid
    query_product = App.query \
        .join(apps_products).join(Channel_product) \
        .with_entities(App.uuid, Channel_product.cname) \
        .add_columns(func.group_concat(Channel_product.uuid).label('product_uuid')) \
        .group_by(App.uuid) \
        .filter(App.uuid == uuid) \
        .subquery()

    # 联合查询
    query = App.query \
        .outerjoin(query_product, App.uuid == query_product.c.uuid) \
        .outerjoin(Live_node, App.live_node_uuid == Live_node.uuid) \
        .with_entities(App.uuid, App.app_id, App.name, App.password_hash, App.model, App.version, App.status, \
            App.create_time, App.update_time, App.first_time, App.access_location, App.access_ip, App.access_time) \
        .add_columns(Live_node.uuid.label('live_node_uuid'), query_product.c.product_uuid) \
        .filter(App.uuid == uuid).first()

    data = {
        'uuid': query.uuid,
        'app_id': query.app_id,
        'name': query.name,
        'password_hash': query.password_hash,
        'model': query.model,
        'version': query.version,
        'product_uuid': query.product_uuid,
        'first_time': query.first_time,
        'access_location': query.access_location,
        'access_ip': query.access_ip,
        'access_time': query.access_time,
        'live_node_uuid': query.live_node_uuid,
        'status': query.status,
        'create_time': query.create_time,
        'update_time': query.update_time
    }

    return jsonify(data)

# 新建app帐号信息
@main.route('/api/app', methods=['POST'])
@login_required
def add_app():
    # 获取请求参数
    app_id = request.json['app_id']
    name = request.json['name']
    password = request.json['password']
    product = request.json['product']
    status = request.json['status']

    # 返回消息
    message = app_id

    # app帐号
    app = App()
    app.uuid = str(uuid.uuid1())
    app.app_id = app_id
    app.name = name
    app.password = password
    app.status = status
    app.create_time = datetime.now()

    db.session.add(app)

    # 产品包
    if product:
        products = Channel_product.query.filter(Channel_product.uuid.in_(product)).all()
        app.products = products
    
    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'app帐号 [%s] 数据新建成功!' % message}
        return jsonify(data)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'app帐号 [%s] 数据新建失败!' % message}
        return jsonify(data)

# 更新指定app帐号信息
@main.route('/api/app', methods=['PUT'])
@login_required
def update_app():
    # 获取请求参数
    uuid = request.json['uuid']
    app_id = request.json['app_id']
    name = request.json['name']
    password = request.json['password']
    product = request.json['product']
    status = request.json['status']

    # 返回消息
    message = app_id

    # app帐号
    app = App.query.filter(App.uuid == uuid).first()
    app.app_id = app_id
    app.name = name

    # 密码修改
    if app.password_hash != password:
        app.password = password

    app.status = status
    app.update_time = datetime.now()

    # 产品包
    if product:
        products = Channel_product.query.filter(Channel_product.uuid.in_(product)).all()
        app.products = products
    else:
        # 数据空，删除已存在关系
        for d in app.products:
            app.products.remove(d)

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'app帐号 [%s] 数据更新成功!' % message}
        return jsonify(data)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'app帐号 [%s] 数据更新失败!' % message}
        return jsonify(data)

# 删除指定app帐号信息
@main.route('/api/app', methods=['DELETE'])
@login_required
def delete_app():
    # 获取请求参数
    uuid = request.json['uuid']

    # 返回消息
    message = []

    # 删除信息
    for i in uuid:
        app = App.query.filter(App.uuid==i).first()
        message.append(app.app_id)
        db.session.delete(app)

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'app帐号 [%s] 数据删除成功!' % ','.join(message)}
    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'app帐号 [%s] 数据删除失败!' % ','.join(message)}

    return jsonify(data)