# -*- coding: utf-8 -*-

from flask import request, jsonify, render_template, redirect
from flask_login import login_required, logout_user
from werkzeug.security import check_password_hash

from sqlalchemy import or_, func, desc, distinct
from sqlalchemy.exc import IntegrityError

import uuid
from datetime import datetime

from . import main

from ..models import db, User

# 获取用户信息
@main.route('/api/user', methods=['GET'])
@login_required
def get_user():
    # 获取请求参数
    pass

# 新建用户信息
@main.route('/api/user', methods=['POST'])
@login_required
def add_user():
    # 获取请求参数
    pass

# 更新用户信息
@main.route('/api/user', methods=['PUT'])
@login_required
def update_user():
    # 获取请求参数
    uuid = request.json['uuid']
    old = request.json['old']
    new = request.json['new']

    # 用户
    user = User.query.filter(User.uuid == uuid).first()

    # 返回消息
    message = user.cname

    # 密码检测
    if check_password_hash(user.password_hash, old):
        user.password = new
    else:
        data = {'msg': u'用户 [%s] 旧密码错误!' % message}
        return jsonify(data)

    user.update_time = datetime.now()

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'用户 [%s] 数据更新成功，请退出重新登录' % message}
        return jsonify(data)

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'用户 [%s] 数据更新失败!' % message}
        return jsonify(data)

# 删除用户信息
@main.route('/api/user', methods=['DELETE'])
@login_required
def delete_user():
    # 获取请求参数
    pass