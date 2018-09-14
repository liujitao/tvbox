# -*- coding: utf-8 -*-

from flask import request, jsonify, current_app
from flask_login import login_required

from sqlalchemy import or_, func, desc, distinct, cast, case
from sqlalchemy.dialects.mysql import INTEGER, CHAR
from sqlalchemy.exc import IntegrityError

from pypinyin import lazy_pinyin

from . import main
from ..models import *

# 电视盒型号
@main.route('/select/model', methods=['GET'])
@login_required
def select_model():
    if request.args.get('uuid', None):
        query = Stb_model.query.filter(Stb_model.uuid ==  request.args['uuid']).first()
        data = {'id': query.uuid, 'text': query.name}
    else:
        query = Stb_model.query.order_by(Stb_model.name).all()
        data = [{'id': q.uuid, 'text': q.name} for q in query]
    
    return jsonify(data)

# 电视盒分组
@main.route('/select/grouping', methods=['GET'])
@login_required
def select_grouping():
    if request.args.get('uuid', None):
        query = Stb_grouping.query.filter(Stb_grouping.uuid == request.args['uuid']).first()
        data = {'id': query.uuid, 'text': query.cname}
    else:
        query = Stb_grouping.query.order_by(Stb_grouping.cname).all()
        data = [{'id': q.uuid, 'text': q.cname} for q in query]

    if isinstance(data, list):
        # 中文拼音排序    
        return jsonify(sorted(data, key=lambda k: lazy_pinyin(k['text'])))
    else:
        return jsonify(data)

# 电视盒
@main.route('/select/tvbox', methods=['GET'])
@login_required
def select_tvbox():
    query = Stb.query

    # 过滤
    if request.args.get('category', None):
        # 过滤停用电视盒
        if request.args['category'] == 'enabled':
            query = query.filter(Stb.status !='2')

        # 过滤已关联用户电视盒
        if request.args['category'] == 'customer':
             query = query.filter(Stb.customer_uuid == None)

        # 过滤已关联vip电视盒
        if request.args['category'] == 'vip':
             query = query.filter(Stb.vip_uuid == None)

        # 过滤已关联合作商电视盒
        if request.args['category'] == 'partner':
             query = query.filter(Stb.partner_uuid == None)

    # 搜索
    if request.args.get('search', None):
        search = request.args['search']
        query = query.filter(Stb.sn.like('%'+search+'%'))

    # 型号
    if request.args.get('model', None):
        model = request.args['model']
        query = query.filter(Stb.model_uuid==model)

    # 指派sn
    if request.args.get('sn', None):
        query = query.filter(Stb.sn == request.args['sn']).first()
        return jsonify({'id': query.uuid, 'text': query.sn})

    # 指派uuid
    if request.args.get('uuid', None):
        query = query.filter(Stb.uuid == request.args['uuid']).first()
        return jsonify({'id': query.uuid, 'text': query.sn})

    query = query.order_by(Stb.sn).all()
    data = [{'id': q.uuid, 'text': q.sn} for q in query]

    return jsonify(data)

# 大洲
@main.route('/select/continent', methods=['GET'])
@login_required
def select_continent():
    if request.args.get('uuid', None):
        query = Continent.query.filter(Continent.uuid == request.args['uuid']).first()
        data = {'id': query.uuid, 'text': query.cname}
    else:
        query = Continent.query.order_by(Continent.cname).all()
        data = [{'id': q.uuid, 'text': q.cname} for q in query]
    
    if isinstance(data, list):
        # 中文拼音排序    
        return jsonify(sorted(data, key=lambda k: lazy_pinyin(k['text'])))
    else:
        return jsonify(data)

# 客户
@main.route('/select/customer', methods=['GET'])
@login_required
def select_customer():
    if request.args.get('uuid', None):
        query = Customer.query.filter(Customer.uuid == request.args['uuid']).first()
        data = {'id': query.uuid, 'text': query.name}

    elif request.args.get('search', None):
        search = request.args['search']
        query = Customer.query.filter(Customer.name.like('%'+search+'%')).order_by(Customer.name).all()
        data = [{'id': q.uuid, 'text': q.name} for q in query]
    
    else:
        query = Customer.query.order_by(Customer.name).all()
        data = [{'id': q.uuid, 'text': q.name} for q in query]

    return jsonify(data)

# 合作商
@main.route('/select/partner', methods=['GET'])
@login_required
def select_partner():
    if request.args.get('uuid', None):
        query = Partner.query.filter(Partner.uuid == request.args['uuid']).first()
        data = {'id': query.uuid, 'text': query.cname}

    elif request.args.get('search', None):
        search = request.args['search']
        query = Partner.query.filter(Partner.cname.like('%'+search+'%')).all()
        data = [{'id': q.uuid, 'text': q.cname} for q in query]
    
    else:
        query = Partner.query.order_by(Partner.cname).all()
        data = [{'id': q.uuid, 'text': q.cname} for q in query]

    if isinstance(data, list):
        # 中文拼音排序    
        return jsonify(sorted(data, key=lambda k: lazy_pinyin(k['text'])))
    else:
        return jsonify(data)

# 直播节点
@main.route('/select/live_node', methods=['GET'])
@login_required
def select_live_node():
    if request.args.get('uuid', None):
        query = Live_node.query.filter(Live_node.uuid == request.args['uuid']).first()
        data = {'id': query.uuid, 'text': query.cname}  
    else:
        query = Live_node.query.filter(Live_node.status == '1').all()
        data = [{'id': q.uuid, 'text': q.cname} for q in query]
    
    if isinstance(data, list):
        # 中文拼音排序    
        return jsonify(sorted(data, key=lambda k: lazy_pinyin(k['text'])))
    else:
        return jsonify(data)

# 电视盒关联客户
@main.route('/select/tvbox/customer', methods=['GET'])
@login_required
def select_tvbox_customer():
    if request.args.get('uuid', None):
        query = Stb.query \
            .join(Customer, Stb.customer_uuid==Customer.uuid) \
            .with_entities(Stb.uuid, Stb.customer_uuid.label('customer_id'), Customer.name.label('name')) \
            .filter(Stb.uuid==request.args['uuid']).first()

        data = {'customer_id': query.customer_id, 'name': query.name}
    else:
        query = Stb.query \
            .join(Customer, Stb.customer_uuid==Customer.uuid) \
            .with_entities(Stb.uuid, Stb.customer_uuid.label('customer_id'), Customer.name.label('name')).all()
        data = [{'id': q.uuid, 'text': q.cname} for q in query]
    
    if isinstance(data, list):
        # 中文拼音排序    
        return jsonify(sorted(data, key=lambda k: lazy_pinyin(k['text'])))
    else:
        return jsonify(data)

# 频道
@main.route('/select/channel', methods=['GET'])
@login_required
def select_channel():
    if request.args.get('uuid', None):
        query = Channel.query.filter(Channel.uuid == request.args['uuid']).first()
        data = {'id': query.uuid, 'text': query.cname}  
    else:
        query = Channel.query.filter(Channel.status == '1').all()
        # 字段cname取首字母
        data = [{'id': q.uuid, 'text': q.cname} for q in query]
   
    if isinstance(data, list):
        # 中文拼音排序    
        return jsonify(sorted(data, key=lambda k: lazy_pinyin(k['text'])))
    else:
        return jsonify(data)

# 频道分类
@main.route('/select/channel_category', methods=['GET'])
@login_required
def select_channel_category():
    if request.args.get('uuid', None):
        query = Channel_category.query.filter(Channel_category.uuid == request.args['uuid']).first()
        data = {'id': query.uuid, 'text': query.cname}  
    else:
        query = Channel_category.query.filter(Channel_category.status == '1').all()
        data = [{'id': q.uuid, 'text': q.cname} for q in query]
    
    if isinstance(data, list):
        # 中文拼音排序    
        return jsonify(sorted(data, key=lambda k: lazy_pinyin(k['text'])))
    else:
        return jsonify(data)

# 产品包
@main.route('/select/product', methods=['GET'])
@login_required
def select_product():
    if request.args.get('uuid', None):
        query = Channel_product.query.filter(Channel_product.uuid == request.args['uuid']).first()
        data = {'id': query.uuid, 'text': query.cname}
    else:
        query = Channel_product.query.filter(Channel_product.status == '1').all()
        data = [{'id': q.uuid, 'text': q.cname} for q in query]

    if isinstance(data, list):
        # 中文拼音排序    
        return jsonify(sorted(data, key=lambda k: lazy_pinyin(k['text'])))
    else:
        return jsonify(data)

# 产品包频道
@main.route('/select/product_channel', methods=['GET'])
@login_required
def select_product_channel():
    # 频道分类
    query_category = Channel_category.query \
        .with_entities(Channel_category.uuid, Channel_category.cname) \
        .filter(Channel_category.status == '1') \
        .order_by(Channel_category.sort_id) \
        .all()

    # 频道（开启状态）
    query_channel = Channel_category.query \
        .join(categories_channels).join(Channel) \
        .with_entities(Channel_category.uuid, Channel.uuid.label('channel_uuid'), Channel.cname.label('channel_cname')) \
        .filter(Channel.status == '1') \
        .all()

    data = []
    for q in query_category:
        channel = [{'id': c.channel_uuid, 'text': c.channel_cname} for c in query_channel if c.uuid == q.uuid]
        data.append({'tag': q.cname, 'channel': sorted(channel, key=lambda k: lazy_pinyin(k['text']))})
    
    return jsonify(data)

# 首字母分类频道
@main.route('/select/letter_channel', methods=['GET'])
@login_required
def select_letter_channel():
    # 频道 
    query_channel = Channel.query.filter(Channel.status == '1').all()
    data = []

    # 一般频道拼音首字母
    tag = sorted(list(set( \
        [lazy_pinyin(q.cname)[0][0].upper() for q in Channel.query.filter(Channel.status == '1').all() if q.name[0] not in ['a', 'v']]
    )))

    for t in tag:
        channel = [{'id': q.uuid, 'text': q.cname} for q in query_channel if q.name[0] not in ['a', 'v'] and lazy_pinyin(q.cname)[0][0].upper() == t]
        data.append({'tag': t, 'channel': sorted(channel, key=lambda k: lazy_pinyin(k['text']))})

    # 特殊频道代码首字母
    for t in ['a', 'v']:
        channel = [{'id': q.uuid, 'text': q.cname} for q in query_channel if q.name[0] == t]
        data.append({'tag': t, 'channel': sorted(channel, key=lambda k: lazy_pinyin(k['text']))})

    return jsonify(data)

# 排序频道
@main.route('/select/sortid_channel', methods=['GET'])
@login_required
def select_sortid_channel():
    data = [{'id': q.uuid, 'text': q.cname, 'sort_id': q.sort_id} \
        for q in Channel.query.order_by(cast(Channel.sort_id, INTEGER), Channel.name).all()]
    
    return jsonify(data)

# 上传子目录
@main.route('/select/upload_sub_path', methods=['GET'])
@login_required
def select_upload_sub_path():
    sub_path = current_app.config['UPLOAD_SUB_PATH']

    if request.args.get('id', None):
        data = [{'id': s['id'], 'text': s['name']} for s in sub_path if s['id'] == request.args['id']]
    else:
        data = [{'id': s['id'], 'text': s['name']} for s in sub_path]

    return jsonify(data)