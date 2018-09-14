# -*- coding: utf-8 -*-

from flask import request, render_template, session, redirect, url_for, jsonify, current_app, flash
from flask_login import login_required, login_user, logout_user, current_user

import json

from . import main
from .. import login_manager
from ..models import User

# 未认证处理
#@login_manager.unauthorized_handler
#def unauthorized_handler():
#    # session过期，用户请求跳转到登录页面
#    return redirect(url_for('main.login'))

# index页
@main.route('/', methods=['GET'])
def index():
    return redirect(url_for('main.login'))

@login_manager.user_loader
def load_user(user_uuid):
    return User.query.get(user_uuid)
    
# 用户登录
@main.route('/login', methods=['GET', 'POST'])
def login():
    # 获取请求参数
    username = request.form.get('username', None)
    password = request.form.get('password', None)

    if username and password:
        user = User.query.filter(User.name==username).first()
        # 验证用户
        if user and user.verify_password(password):
            login_user(user, remember=True)
            return redirect(request.args.get('next') or url_for('main.tvbox'))
        else:
            flash(u'用户名或者密码错误') 
            return render_template('login.html')

    return render_template('login.html')

@main.route('/modal/password/<id>', methods=['GET'])
@login_required
def modal_password(id):
    if id == 'add':
        return render_template('modal/password_add.html')
    elif id == 'show':
        return render_template('modal/password_show.html')
    elif id == 'edit':
        return render_template('modal/password_edit.html')
    elif id == 'delete':
        return render_template('modal/delete.html')

# 用户退出
@main.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(request.args.get('next') or url_for('main.login'))

# app
@main.route('/app', methods=['GET'])
@login_required
def app():
    return render_template('app.html')

@main.route('/modal/app/<id>', methods=['GET'])
@login_required
def modal_app(id):
    if id == 'add':
        return render_template('modal/app_add.html')
    elif id == 'show':
        return render_template('modal/app_show.html')
    elif id == 'edit':
        return render_template('modal/app_edit.html')
    elif id == 'import':
        return render_template('modal/app_import.html')
    elif id == 'delete':
        return render_template('modal/delete.html')

# 电视盒
@main.route('/tvbox', methods=['GET'])
@login_required
def tvbox():
    return render_template('tvbox.html')

@main.route('/modal/tvbox/<id>', methods=['GET'])
@login_required
def modal_tvbox(id):
    if id == 'add':
        return render_template('modal/tvbox_add.html')
    elif id == 'show':
        return render_template('modal/tvbox_show.html')
    elif id == 'edit':
        return render_template('modal/tvbox_edit.html')
    elif id == 'import':
        return render_template('modal/tvbox_import.html')
    elif id == 'delete':
        return render_template('modal/delete.html')

# 电视盒型号
@main.route('/tvbox_model', methods=['GET'])
@login_required
def tvbox_model():
    return render_template('tvbox_model.html')

@main.route('/modal/tvbox_model/<id>', methods=['GET'])
@login_required
def modal_tvbox_model(id):
    if id == 'add':
        return render_template('modal/tvbox_model_add.html')
    elif id == 'show':
        return render_template('modal/tvbox_model_show.html')
    elif id == 'edit':
        return render_template('modal/tvbox_model_edit.html')
    elif id == 'delete':
        return render_template('modal/delete.html') 

# 电视盒软件
@main.route('/tvbox_software', methods=['GET'])
@login_required
def tvbox_software():
    return render_template('tvbox_software.html')

@main.route('/modal/tvbox_software/<id>', methods=['GET'])
@login_required
def modal_tvbox_software(id):
    if id == 'add':
        return render_template('modal/tvbox_software_add.html')
    elif id == 'show':
        return render_template('modal/tvbox_software_show.html')
    elif id == 'edit':
        return render_template('modal/tvbox_software_edit.html')
    elif id == 'delete':
        return render_template('modal/delete.html')

# 升级分组
@main.route('/tvbox_grouping', methods=['GET'])
@login_required
def tvbox_grouping():
    return render_template('tvbox_grouping.html')

@main.route('/modal/tvbox_grouping/<id>', methods=['GET'])
@login_required
def modal_tvbox_grouping(id):
    if id == 'add':
        return render_template('modal/tvbox_grouping_add.html')
    elif id == 'show':
        return render_template('modal/tvbox_grouping_show.html')
    elif id == 'edit':
        return render_template('modal/tvbox_grouping_edit.html')
    elif id == 'delete':
        return render_template('modal/delete.html')

# 直播节点
@main.route('/live_node', methods=['GET'])
@login_required
def live_node():
    return render_template('live_node.html')

@main.route('/modal/live_node/<id>', methods=['GET'])
@login_required
def modal_live_node(id):
    if id == 'add':
        return render_template('modal/live_node_add.html')
    elif id == 'show':
        return render_template('modal/live_node_show.html')
    elif id == 'edit':
        return render_template('modal/live_node_edit.html')
    elif id == 'delete':
        return render_template('modal/delete.html')

# 频道分类
@main.route('/channel_category', methods=['GET'])
@login_required
def channel_category():
    return render_template('channel_category.html')

@main.route('/modal/channel_category/<id>', methods=['GET'])
@login_required
def modal_channel_category(id):
    if id == 'add':
        return render_template('modal/channel_category_add.html')
    elif id == 'show':
        return render_template('modal/channel_category_show.html')
    elif id == 'edit':
        return render_template('modal/channel_category_edit.html')
    elif id == 'delete':
        return render_template('modal/delete.html')

# 频道
@main.route('/channel', methods=['GET'])
@login_required
def channel():
    return render_template('channel.html')

@main.route('/modal/channel/<id>', methods=['GET'])
@login_required
def modal_channel(id):
    if id == 'add':
        return render_template('modal/channel_add.html')
    elif id == 'show':
        return render_template('modal/channel_show.html')
    elif id == 'edit':
        return render_template('modal/channel_edit.html')
    elif id == 'sort':
        return render_template('modal/channel_sort.html')
    elif id == 'delete':
        return render_template('modal/delete.html')

# 产品包
@main.route('/channel_product', methods=['GET'])
@login_required
def channel_product():
    return render_template('channel_product.html')

@main.route('/modal/channel_product/<id>', methods=['GET'])
@login_required
def modal_channel_product(id):
    if id == 'add':
        return render_template('modal/channel_product_add.html')
    elif id == 'show':
        return render_template('modal/channel_product_show.html')
    elif id == 'edit':
        return render_template('modal/channel_product_edit.html')
    elif id == 'delete':
        return render_template('modal/delete.html')

# 客户
@main.route('/customer', methods=['GET'])
@login_required
def customer():
    return render_template('customer.html')

@main.route('/modal/customer/<id>', methods=['GET'])
@login_required
def modal_customer(id):
    if id == 'add':
        return render_template('modal/customer_add.html')
    elif id == 'show':
        return render_template('modal/customer_show.html')
    elif id == 'edit':
        return render_template('modal/customer_edit.html')
    elif id == 'delete':
        return render_template('modal/delete.html')

# 会员
@main.route('/vip', methods=['GET'])
@login_required
def vip():
    return render_template('vip.html')

@main.route('/modal/vip/<id>', methods=['GET'])
@login_required
def modal_vip(id):
    if id == 'add':
        return render_template('modal/vip_add.html')
    elif id == 'show':
        return render_template('modal/vip_show.html')
    elif id == 'edit':
        return render_template('modal/vip_edit.html')
    elif id == 'delete':
        return render_template('modal/delete.html')

# 合作商
@main.route('/partner', methods=['GET'])
@login_required
def partner():
    return render_template('partner.html')

@main.route('/modal/partner/<id>', methods=['GET'])
@login_required
def modal_partner(id):
    if id == 'add':
        return render_template('modal/partner_add.html')
    elif id == 'show':
        return render_template('modal/partner_show.html')
    elif id == 'edit':
        return render_template('modal/partner_edit.html')
    elif id == 'delete':
        return render_template('modal/delete.html')

# 大洲
@main.route('/continent', methods=['GET'])
@login_required
def continent():
    return render_template('continent.html')

# 国家
@main.route('/country', methods=['GET'])
@login_required
def country():
    return render_template('country.html')

# 文件上传
@main.route('/file_upload', methods=['GET'])
@login_required
def file_upload():
    return render_template('file_upload.html')

@main.route('/modal/file_upload/<id>', methods=['GET'])
@login_required
def modal_file_upload(id):
    if id == 'import':
        return render_template('modal/file_import.html')
    elif id == 'delete':
        return render_template('modal/delete.html')

# 信息
@main.route('/modal/info', methods=['GET'])
@login_required
def modal_info():
    return render_template('info.html')