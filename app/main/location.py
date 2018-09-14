# -*- coding: utf-8 -*-

from flask import request, jsonify, render_template
from flask_login import login_required

from sqlalchemy import or_, func, desc, distinct, cast, case
from sqlalchemy.dialects.mysql import INTEGER, CHAR
from sqlalchemy.exc import IntegrityError

from datetime import datetime

from . import main
from .functions import *
from .selects import *

from ..models import Live_node, continents_nodes, Continent, Country

# 获取所有大洲信息
@main.route('/api/continent/list', methods=['GET'])
@login_required
def get_continent_list():
    # 获取请求参数
    draw = request.args['draw']
    start = request.args['start']
    length = request.args['length']
    search = request.args['search']
    order_name = request.args['order_name']
    order = request.args['order']

    # 子查询 - 每个大洲的直播节点数量
    query_node = Continent.query \
        .join(continents_nodes).join(Live_node) \
        .with_entities(Continent.uuid) \
        .add_columns(func.group_concat(Live_node.cname).label('node')) \
        .group_by(Continent.uuid) \
        .subquery()

    # 子查询 - 每个大洲的国家数量
    query_country = Continent.query \
        .outerjoin(Country, Country.continent_uuid==Continent.uuid) \
        .with_entities(Continent.uuid) \
        .add_columns(func.count(Country.uuid).label('country')) \
        .group_by(Continent.uuid) \
        .subquery()

    # 联合查询
    query = Continent.query \
        .outerjoin(query_node, Continent.uuid == query_node.c.uuid) \
        .outerjoin(query_country, Continent.uuid == query_country.c.uuid) \
        .with_entities(Continent.uuid, Continent.code, Continent.name, Continent.cname) \
        .add_columns(query_node.c.node, query_country.c.country)

    # 搜索

    # 排序
    if order == 'asc':
        if order_name == 'sort_id':
            query = query.order_by(cast(Continent.sort_id, INTEGER))
        elif order_name == 'cname':
            query = query.order_by(cast(Continent.cname, CHAR(charset='gbk')))
        else:
            query = query.order_by(order_name)
    else:
        if order_name == 'sort_id':
            query = query.order_by(desc(cast(Continent.sort_id, INTEGER)))
        elif order_name == 'cname':
            query = query.order_by(desc(cast(Continent.cname, CHAR(charset='gbk'))))
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
        'node': q.node,
        'country': q.country,
    } for q in query.items]

    return jsonify(
        {
            'draw': int(draw),
            'recordsTotal': total,
            'recordsFiltered': total,
            'data': data
        }
    )

# 获取所有国家信息
@main.route('/api/country/list', methods=['GET'])
@login_required
def get_country_list():
    # 获取请求参数
    draw = request.args['draw']
    start = request.args['start']
    length = request.args['length']
    search = request.args['search']
    order_name = request.args['order_name']
    order = request.args['order']

    # 子查询 - 每个大洲指派的直播节点
    query_continent = Continent.query \
        .join(continents_nodes).join(Live_node) \
        .with_entities(Continent.uuid) \
        .add_columns(func.group_concat(Live_node.cname).label('node')) \
        .group_by(Continent.uuid) \
        .subquery()

    # 联合查询
    query = Country.query \
        .outerjoin(Continent, Continent.uuid==Country.continent_uuid) \
        .outerjoin(query_continent, query_continent.c.uuid==Continent.uuid) \
        .with_entities(Country.uuid.label('country_uuid'), Country.code.label('country_code'), Country.name.label('country_name'), Country.cname.label('country_cname'), \
            Continent.code.label('continent_code'), Continent.name.label('continent_name'), Continent.cname.label('continent_cname')) \
        .add_columns(query_continent.c.node) \

    # 搜索
    if search:
        query = query \
            .filter(or_(
                Country.code.like('%' + search + '%'),
                Country.name.like('%' + search + '%'),
                Country.cname.like('%' + search + '%'),
                Continent.code.like('%' + search + '%'),
                Continent.name.like('%' + search + '%'),
                Continent.cname.like('%' + search + '%')))

    # 排序
    if order == 'asc':
        if order_name == 'sort_id':
            query = query.order_by(cast(Continent.sort_id, INTEGER))
        elif order_name == 'continent_name':
            query = query.order_by(cast(Continent.cname, CHAR(charset='gbk')))
        elif order_name == 'country_cname':
            query = query.order_by(cast(Country.cname, CHAR(charset='gbk')))
        else:
            query = query.order_by(order_name)
    else:
        if order_name == 'sort_id':
            query = query.order_by(desc(cast(Continent.sort_id, INTEGER)))
        elif order_name == 'continent_name':
            query = query.order_by(desc(cast(Continent.cname, CHAR(charset='gbk'))))
        elif order_name == 'country_cname':
            query = query.order_by(desc(cast(Country.cname, CHAR(charset='gbk'))))
        else:
            query = query.order_by(desc(order_name))

    # 记录总数
    total = query.count()

    # 分页
    query = query.paginate(int(start) / int(length) + 1, int(length), False)

    # 返回datatable数据
    data = [{
        'country_uuid': q.country_uuid,
        'country_code': q.country_code,
        'country_name': q.country_name,
        'country_cname': q.country_cname,
        'continent_code': q.continent_code,
        'continent_name': q.continent_name,
        'continent_cname': q.continent_cname,
        'node': q.node,
    } for q in query.items]

    return jsonify(
        {
            'draw': int(draw),
            'recordsTotal': total,
            'recordsFiltered': total,
            'data': data
        }
    )
