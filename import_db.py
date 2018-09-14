#!/usr/bin/env python
# -*- coding: utf8 -*-

import MySQLdb
import uuid
from datetime import datetime

# 源数据库
src_conn= MySQLdb.connect(
    host='10.0.70.11',
    port = 3306,
    user='root',
    passwd='123456',
    db ='iptv',
    charset='utf8'
)

# 目的数据库
dst_conn= MySQLdb.connect(
    host='10.0.70.11',
    port = 3306,
    user='root',
    passwd='123456',
    db ='suntv',
    charset='utf8'
)

# 游标
src_cur = src_conn.cursor()
dst_cur = dst_conn.cursor()

'''
# 频道分类
categories = [
    (str(uuid.uuid1()), 'yangshi', u'央视', u'央視', '1', '1', datetime.now()), 
    (str(uuid.uuid1()), 'weishi', u'卫视', u'衛視', '2', '1', datetime.now()),
    (str(uuid.uuid1()), 'difang', u'地方', u'地方', '3', '1', datetime.now()), 
    (str(uuid.uuid1()), 'gaoqing', u'高清', u'高清', '4', '1', datetime.now()),
    (str(uuid.uuid1()), 'reimen', u'热门', u'熱門', '5', '1', datetime.now()), 
    (str(uuid.uuid1()), 'haiwai', u'海外', u'海外', '6', '1', datetime.now()),
    (str(uuid.uuid1()), 'guoji', u'国际', u'國際', '7', '1', datetime.now()), 
    (str(uuid.uuid1()), 'jiaoyu', u'教育', u'教育', '8', '1', datetime.now()),
    (str(uuid.uuid1()), 'yueyu', u'粤语', u'粵語', '9', '1', datetime.now()),  
    (str(uuid.uuid1()), 'yueyu', u'测试', u'測試', '10', '1', datetime.now()), 
    (str(uuid.uuid1()), 'xuni', u'虚拟', u'虛擬', '11', '1', datetime.now()), 
    (str(uuid.uuid1()), 'zhongyangguangbo', u'中央广播', u'中央廣播', '12', '1', datetime.now()),
    (str(uuid.uuid1()), 'defangguangbo', u'地方广播', u'地方廣播', '13', '1', datetime.now()),
    (str(uuid.uuid1()), 'wenyiguangbo', u'文艺广播', u'文藝廣播', '14', '1', datetime.now()), 
    (str(uuid.uuid1()), 'yinyueguangbo', u'音乐广播', u'音樂廣播', '15', '1', datetime.now())
]

query = dst_cur.executemany('insert into channel_category (uuid, name, cname, tname, sort_id, status, create_time) values (%s, %s, %s, %s, %s, %s, %s)', categories)
dst_conn.commit()

# 频道
query = src_cur.execute('select id, english_name, chinese_name, hongkong_name, order_no, busi_status from tb_channel where status="0"')
channels = [ (str(uuid.UUID(i[0])), i[1], i[2], i[3], str(i[4]), '1' if i[5]=='0' else '0', datetime.now()) for i in src_cur.fetchall()]
query = dst_cur.executemany('insert into channel (uuid, name, cname, tname, sort_id, status, create_time) values (%s, %s, %s, %s, %s, %s, %s)', channels)
dst_conn.commit()


# 频道关联分类
channel_link_category = []
query = dst_cur.execute('select uuid, cname from channel_category')
category = { category_cname: category_uuid for category_uuid,  category_cname in dst_cur.fetchall()}

query = src_cur.execute('select id, tags from tb_channel where status="0"')
for channel_uuid, channel_tags in src_cur.fetchall():
    if channel_tags and list(set(channel_tags.split(',')) & set(category.keys())):
        channel_link_category.extend(map(lambda x: (str(x), str(uuid.UUID(channel_uuid))), [category[i] for i in list(set(channel_tags.split(',')) & set(category.keys()))]))

query = dst_cur.executemany('insert into categories_channels (category_uuid, channel_uuid) values (%s, %s)', channel_link_category)
dst_conn.commit()

# 电视盒产品包 93个
query = src_cur.execute('select id, product_name, description, busi_status, create_date, update_date from tb_product where status="0"')
products = [(str(uuid.UUID(i[0])), i[1], i[2], '1', '1' if i[3]=='0' else '0', i[4], i[5]) for i in src_cur.fetchall()]

#print len(sorted([ i[0] for i in  products]))
query = dst_cur.executemany('insert into channel_product (uuid, cname, description, category, status, create_time, update_time) values (%s, %s, %s, %s, %s, %s, %s)', products)
dst_conn.commit()

# 电视盒产品包关联频道 (product_id, channel_uuid 定义反了需置换，并且有垃圾数据，关闭约束方可导入新库)
query = src_cur.execute('select id from tb_product where status="0"')
products = [i[0] for i in src_cur.fetchall()]

query = src_cur.execute('select product_id, channel_id from tb_product_channel where status="0"')
product_link_channel = [(str(uuid.UUID(product_id)), str(uuid.UUID(channel_id))) for channel_id, product_id in src_cur.fetchall()]

query = dst_cur.executemany('insert into products_channels (channel_uuid, product_uuid) values (%s, %s)', list(set(product_link_channel)))
dst_conn.commit()
'''
# 电视盒硬件
query = src_cur.execute('select code, platform, description from tb_terminal_type')
stbs = [(str(uuid.uuid1()), i[0], i[1], i[2], datetime.now()) for i in src_cur.fetchall()]
query = dst_cur.executemany('insert into stb_model (uuid, code, name, cname, create_time) values (%s, %s, %s, %s, %s)', stbs)
dst_conn.commit()

# 电视盒软件
query = dst_cur.execute('select uuid, code from stb_model')
models = {model_code:model_uuid for model_uuid, model_code in dst_cur.fetchall()}

query = src_cur.execute('select id, software_code, software_md5, software_size, version, update_url, type, busi_status, create_date from tb_client_software where status="0"')
softwares = [(str(uuid.UUID(id)), version, software_md5, software_size, update_url, '1' if type=='2' else '0', '1' if busi_status=='0' else '0', create_date, models[software_code] if software_code in models.keys() else None) \
    for id, software_code, software_md5, software_size, version, update_url, type, busi_status, create_date in src_cur.fetchall()]

query = dst_cur.executemany('insert into stb_software (uuid, version, md5, size, download_url, category, status, create_time, model_uuid) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)', softwares)
dst_conn.commit()
'''
# 电视盒分组
query = src_cur.execute('select id, name, description, create_date from tb_group where status="0"')
groupings = [(str(uuid.UUID(i[0])), i[1], i[2], i[3]) for i in src_cur.fetchall()]
query = dst_cur.executemany('insert into stb_grouping (uuid, cname, description, create_time) values (%s, %s, %s, %s)', groupings)
dst_conn.commit()

# 软件关联分组
software_link_grouping = []

# 正式组
query = src_cur.execute('select id, formal_group_id from tb_client_software where status="0" and formal_group_id <> ""')
for software_uuid, grouping_uuid in src_cur.fetchall():
    software_link_grouping.extend(map(lambda x: (str(uuid.UUID(software_uuid)), str(uuid.UUID(x))), grouping_uuid.split(',')))

# 测试组
query = src_cur.execute('select id, test_group_id from tb_client_software where status="0" and test_group_id <> ""')
for software_uuid, grouping_uuid in src_cur.fetchall():
    software_link_grouping.extend(map(lambda x: (str(uuid.UUID(software_uuid)), str(uuid.UUID(x))), grouping_uuid.split(',')))

query = dst_cur.executemany('insert into softwares_groupings (software_uuid, grouping_uuid) values (%s, %s)', software_link_grouping)
dst_conn.commit()

# 用户 (customer_type: 1 1年用户 2 vip 3 付费用户) (busi_status 1 2 3)
query = src_cur.execute('select id, customer_name, contact_email, contact_number, contact_address, description, create_date from tb_customer where status="0"') 

rows = []
for i in src_cur.fetchall():
    rows.append((str(uuid.UUID(i[0])), i[1], i[2], i[3], i[4], i[5], i[6]))
    if len(rows) == 1000:
        dst_cur.executemany('insert into customer (uuid, name, mail, phone, address, description, create_time) values (%s, %s, %s, %s, %s, %s, %s)', rows)
        dst_conn.commit()
        rows = []

dst_cur.executemany('insert into customer (uuid, name, mail, phone, address, description, create_time) values (%s, %s, %s, %s, %s, %s, %s)', rows)
dst_conn.commit()

# 电视盒  (busi_status: 0 开通  2 禁用)
query = src_cur.execute('select id, stb_no, create_date, busi_status from tb_stb where status="0"') 
rows = []
for i in src_cur.fetchall():
    rows.append((str(uuid.UUID(i[0])), i[1], i[2], '1' if i[3] == '0' else i[3]))
    if len(rows) == 5000:
        dst_cur.executemany('insert into stb (uuid, sn, create_time, status) values (%s, %s, %s, %s)', rows)
        dst_conn.commit()
        rows = []

dst_cur.executemany('insert into stb (uuid, sn, create_time, status) values (%s, %s, %s, %s)', rows)
dst_conn.commit()

# 电视盒关联用户
query = src_cur.execute('select stb_id, customer_id from tb_customer_stb where status="0"') 
rows = []
for stb_id, customer_id in src_cur.fetchall():
    rows.append((str(uuid.UUID(customer_id)), str(uuid.UUID(stb_id))))
    if len(rows) == 5000:
        print len(rows)
        dst_cur.executemany('update stb set customer_uuid=%s where uuid=%s', rows) 
        dst_conn.commit()
        rows = []

dst_cur.executemany('update stb set customer_uuid=%s where uuid=%s', rows) 
dst_conn.commit()

# 电视盒关联产品包
query = src_cur.execute('select s.stb_id, p.product_id from tb_customer_sid as c \
    right join tb_customer_stb as s on s.customer_id = c.customer_id \
    left join tb_sid_product as p on c.service_code_id = p.service_code_id \
    where s.status = "0" and c.status = "0" and p.status = "0"')
products = [(str(uuid.UUID(stb_id)), str(uuid.UUID(product_id))) for stb_id, product_id in src_cur.fetchall()]

rows = []
for product in list(set(products)):
    rows.append(product)
    if len(rows) == 5000:
        print len(rows)
        dst_cur.executemany('insert into stbs_products (stb_uuid, product_uuid) value (%s, %s)', rows) 
        dst_conn.commit()
        rows = []

dst_cur.executemany('insert into stbs_products (stb_uuid, product_uuid) value (%s, %s)', rows) 
dst_conn.commit()     

# 电视盒关联分组
query = src_cur.execute('select group_id, stb_id from tb_group_stb where status = "0"')
groups = [(str(uuid.UUID(group_id)), str(uuid.UUID(stb_id))) for group_id, stb_id in src_cur.fetchall()]

rows = []
for g in list(set(groups)):
    rows.append(g)
    if len(rows) == 5000:
        print len(rows)
        dst_cur.executemany('update stb set grouping_uuid=%s where uuid=%s', rows) 
        dst_conn.commit()
        rows = []

dst_cur.executemany('update stb set grouping_uuid= %s where uuid=%s', rows) 
dst_conn.commit() 

# 电视盒关联型号
query = src_cur.execute('select software_code, software_version, create_date, country, last_oper_date, account from tb_login_terminal')
rows = []
for i in src_cur.fetchall():
    rows.append((i[0], i[1], i[2], i[3], i[4], i[5]))
    if len(rows) == 5000:
        print len(rows)
        dst_cur.executemany('update stb set model=%s, version=%s, purchase_time=%s, access_location=%s, access_time=%s where sn=%s', rows)
        dst_conn.commit()
        rows = []    

dst_cur.executemany('update stb set model=%s, version=%s, purchase_time=%s, access_location=%s, access_time=%s where sn=%s', rows)
dst_conn.commit()

# 非app 537用户（不知道什么产品）
# tb_terminal_customer tb_terminal_product

# app产品包 29个
query = src_cur.execute('select id, package_name, create_date, update_date from tb_ge_product_package_info where status="0"')
products = [(str(uuid.UUID(i[0])), i[1], i[1], '1', '1', i[2], i[3]) for i in src_cur.fetchall()]

query = dst_cur.executemany('insert into channel_product (uuid, cname, description, category, status, create_time, update_time) values (%s, %s, %s, %s, %s, %s, %s)', products)
dst_conn.commit()

# app产品包关联频道
query = src_cur.execute('select pc.channel_id, ge.product_package_id from tb_ge_product_package_link as ge join tb_product_channel as pc on pc.product_id = ge.product_id')

product_link_channel = [ (str(uuid.UUID(channel_id)),str(uuid.UUID(product_id))) for channel_id, product_id in src_cur.fetchall()]

query = dst_cur.executemany('insert into products_channels (channel_uuid, product_uuid) values (%s, %s)', list(set(product_link_channel)))
dst_conn.commit()

# app用户
query = src_cur.execute('select id, email, password, nickname, activate, create_date from tb_gecustomer where status="0"') 
rows = []
for i in src_cur.fetchall():
    rows.append((str(uuid.UUID(i[0])), i[1], i[2], i[3], '1' if i[4] == '1' else '0', i[5]))
    if len(rows) == 1000:
        dst_cur.executemany('insert into app (uuid, app_id, password_hash, name, status, create_time) values (%s, %s, %s, %s, %s, %s)', rows)
        dst_conn.commit()
        rows = []

dst_cur.executemany('insert into app (uuid, app_id, password_hash, name, status, create_time) values (%s, %s, %s, %s, %s, %s)', rows)
dst_conn.commit()

# app用户关联app产品包
query = src_cur.execute('select ge.customer_id, p.product_id from tb_gesid_product_package as pg \
    join tb_gecustomer_sid as ge on ge.service_code_id = pg.service_code_id \
    join tb_ge_product_package_link as p on p.product_package_id = pg.product_package_id \
    where ge.status = "0" and pg.status = "0" and p.status = "0"')
products = [(str(uuid.UUID(customer_id)), str(uuid.UUID(product_id))) for customer_id, product_id in src_cur.fetchall()]

rows = []
for product in list(set(products)):
    rows.append(product)
    if len(rows) == 5000:
        print len(rows)
        dst_cur.executemany('insert into apps_products (app_uuid, product_uuid) value (%s, %s)', rows) 
        dst_conn.commit()
        rows = []

dst_cur.executemany('insert into apps_products (app_uuid, product_uuid) value (%s, %s)', rows) 
dst_conn.commit()

# app关联型号
query = src_cur.execute('select software_code, software_version, create_date, country, last_oper_date, account from tb_login_gecustomer')
rows = []
for i in src_cur.fetchall():
    rows.append((i[0], i[1], i[2], i[3], i[4], i[5]))
    if len(rows) == 5000:
        print len(rows)
        dst_cur.executemany('update app set model=%s, version=%s, first_time=%s, access_location=%s, access_time=%s where app_id=%s', rows)
        dst_conn.commit()
        rows = []    

dst_cur.executemany('update app set model=%s, version=%s, first_time=%s, access_location=%s, access_time=%s where app_id=%s', rows)
dst_conn.commit()
'''

src_cur.close()
src_conn.close()
dst_cur.close()
dst_conn.close()
