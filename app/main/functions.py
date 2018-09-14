# -*- coding: utf-8 -*-
from flask_login import login_required

# vip内容转换
@login_required
def vip_type_to_id(d):
    if d == u'永久会员':
        return ['0']
    elif d == u'30天会员':
        return ['1']
    elif d == u'90天会员':
        return ['2']
    elif d == u'1年会员':
        return ['3']
    elif d == u'3年会员':
        return ['4']
    elif d == u'会员':
        return ['1', '2', '3', '4', '0']
    else:
        return []

# 电视盒状态转换
@login_required
def stb_status_to_id(d):
    if d == u'未开通':
        return ['0']
    elif d == u'已开通':
        return ['1']
    elif d == u'已停用':
        return ['2']
    else:
        return []

# 启用状态转换
@login_required
def status_to_id(d):
    if d == u'禁用':
        return ['0']
    elif d == u'启用':
        return ['1']
    else:
        return []

# 产品包类型转换
@login_required
def category_to_id(d):
    if d == u'免费':
        return ['0']
    elif d == u'正式':
        return ['1']
    else:
        return []