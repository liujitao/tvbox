# -*- coding: utf-8 -*-
from flask import request, jsonify, current_app
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

import os
import uuid
import hashlib
from datetime import datetime

from . import main
from ..models import db, File_upload

# 获取所有文件信息
@main.route('/api/file_upload/list', methods=['GET'])
@login_required
def get_file_list():
    # 获取请求参数
    draw = request.args['draw']
    start = request.args['start']
    length = request.args['length']
    search = request.args['search']
    order_name = request.args['order_name']
    order = request.args['order']
    
    # 查询
    query = File_upload.query \
        .with_entities(File_upload.uuid, File_upload.name, File_upload.url, File_upload.size, File_upload.md5, File_upload.create_time)

    # 搜索功能不提供

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
        'name': q.name,
        'url': q.url,
        'size': q.size,
        'md5': q.md5,
        'create_time': q.create_time
    } for q in query.items]

    return jsonify(
        {
            'draw': int(draw),
            'recordsTotal': total,
            'recordsFiltered': total,
            'data': data
        }
    )

# 上传文件
@main.route('/api/file_upload', methods=['POST'])
@login_required
def add_file():
    # 获取请求参数
    f = request.files['file']

    upload_path = current_app.config['UPLOAD_PATH']
    upload_size = current_app.config['UPLOAD_MAX_SIZE']
    upload_ext = current_app.config['UPLOAD_ALLOWED_EXTENSIONS']

    if f:
        f_ext = os.path.splitext(f.filename)[1]
        # 符合指定扩展名
        if not ( f_ext != '' and f_ext[1:] in upload_ext):
            return jsonify({'msg': u'不支持的文件类型，仅支持[ %s ]文件' % ','.join(upload_ext)})

        # 符合指定大小
        size = int(request.headers['Content-Length'])
        if size > upload_size:
            return jsonify({'msg': u'文件过大，仅支持[ %d ] MB' % upload_size /1024/1024})

        # 写本地文件
        path = os.path.join(upload_path, f.filename)
        f.save(path)
        
        if os.path.exists(path):
            # 写数据库
            upload = File_upload()
            upload.uuid = str(uuid.uuid1())
            upload.name = f.filename
            upload.url = request.url_root + 'static/upload/' + f.filename
            upload.size = os.path.getsize(path)
            upload.md5 = hashlib.md5(open(path, 'rb').read()).hexdigest()
            upload.create_time = datetime.now()
            db.session.add(upload)

            # 提交数据库
            try:
                db.session.commit()
                data = {'msg': u'文件 [%s] 上传成功!' % f.filename}
                return jsonify(data)

            except IntegrityError:
                db.session.rollback()
                os.remove(path)
                data = {'msg': u'文件 [%s] 上传失败!' % f.filename}
                return jsonify(data)
        else:
            return jsonify({'msg': u'文件写入失败'})

    else:
        return jsonify({'msg': u'文件上传失败'})

# 删除文件
@main.route('/api/file_upload', methods=['DELETE'])
@login_required
def delete_file():
    # 获取请求参数
    uuid = request.json['uuid']

    # 返回消息
    message = []

    # 删除信息
    for i in uuid:
        upload = File_upload.query.filter(File_upload.uuid == i).first()
        db.session.delete(upload)
        message.append(upload.name)

    # 提交数据库
    try:
        db.session.commit()
        data = {'msg': u'上传文件 [%s] 删除成功!' % ','.join(message)}

    except IntegrityError:
        db.session.rollback()
        data = {'msg': u'上传文件 [%s] 删除失败!' % ','.join(message)}

    return jsonify(data)
