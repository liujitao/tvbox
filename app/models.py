# -*- coding: utf-8 -*-
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib

# 电视盒-产品包 多对多表
stbs_products = db.Table('stbs_products',
    db.Column('stb_uuid', db.String(40), db.ForeignKey('stb.uuid'), index=True, nullable=False), 
    db.Column('product_uuid', db.ForeignKey('channel_product.uuid'), index=True, nullable=False)
)

# app-产品包 多对多表
apps_products = db.Table('apps_products',
    db.Column('app_uuid', db.String(40), db.ForeignKey('app.uuid'), index=True, nullable=False), 
    db.Column('product_uuid', db.ForeignKey('channel_product.uuid'), index=True, nullable=False)
)

# 产品包-频道 多对多表
products_channels = db.Table('products_channels',
    db.Column('product_uuid', db.String(40), db.ForeignKey('channel_product.uuid'), index=True, nullable=False),
    db.Column('channel_uuid', db.String(40), db.ForeignKey('channel.uuid'), index=True, nullable=False)
)

# 频道分类-频道 多对多表
categories_channels = db.Table('categories_channels',
    db.Column('category_uuid', db.String(40), db.ForeignKey('channel_category.uuid'), index=True, nullable=False),
    db.Column('channel_uuid', db.String(40), db.ForeignKey('channel.uuid'), index=True, nullable=False)
)

# 大洲-直播节点 多对多表
continents_nodes = db.Table('continents_nodes',
    db.Column('continent_uuid', db.String(40), db.ForeignKey('continent.uuid'), index=True, nullable=False),
    db.Column('node_uuid', db.String(40), db.ForeignKey('live_node.uuid'), index=True, nullable=False)
)

# 升级分组-软件 多对多表
softwares_groupings = db.Table('softwares_groupings',
    db.Column('software_uuid', db.String(40), db.ForeignKey('stb_software.uuid'), index=True, nullable=False),
    db.Column('grouping_uuid', db.String(40), db.ForeignKey('stb_grouping.uuid'), index=True, nullable=False)
)

# 用户
class User(db.Model):
    __tablename__ = 'user'
    uuid = db.Column(db.String(40), index=True, primary_key=True)
    name = db.Column(db.String(40), index=True, nullable=False, unique=True)
    cname = db.Column(db.String(40))
    password_hash = db.Column(db.String(128))
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.uuid)

    @property
    def password(self):
        raise AttributeError(u'密码不可读')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

# 合作伙伴
class Partner(db.Model):
    __tablename__ = 'partner'
    uuid = db.Column(db.String(40), index=True, primary_key=True)
    name = db.Column(db.String(40), index=True, nullable=False, unique=True)
    cname = db.Column(db.String(40))
    logo_url = db.Column(db.String(255))
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    stbs = db.relationship('Stb', backref='partners', lazy='dynamic')

# 客户
class Customer(db.Model):
    __tablename__ = 'customer'
    uuid = db.Column(db.String(40), index=True, primary_key=True)
    name = db.Column(db.String(40), index=True)
    mail = db.Column(db.String(40))
    phone = db.Column(db.String(255))
    address = db.Column(db.String(255))
    description = db.Column(db.String(255))
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    stbs = db.relationship('Stb', backref='customers', lazy='dynamic')

# 会员码
class Vip(db.Model):
    __tablename__ = 'vip'
    uuid = db.Column(db.String(40), index=True, primary_key=True)
    category = db.Column(db.String(1), index=True, nullable=False, default='1')  # 会员类型
    effect_time = db.Column(db.DateTime)
    expire_time = db.Column(db.DateTime)
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    stbs = db.relationship('Stb', backref='vips', uselist=False)

# app应用
class App(db.Model):
    __tablename__ = 'app'
    uuid = db.Column(db.String(40), index=True, primary_key=True)             
    sn = db.Column(db.String(40))                                                       # 临时序列号                    
    #app_id = db.Column(db.String(40), index=True, nullable=False, unique=True)          # 登录id(邮箱)
    app_id = db.Column(db.String(40), index=True)                                       # 登录id(邮箱)
    password_hash = db.Column(db.String(128), nullable=False)                           # 用户密码
    name = db.Column(db.String(40))                                                     # 名称
    model = db.Column(db.String(40))                                                    # app型号
    version = db.Column(db.String(40))                                                  # app版本
    status = db.Column(db.String(1), index=True, nullable=False, default=0)             # 启用状态
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    first_time = db.Column(db.DateTime)                                                 # 开通时间
    access_location = db.Column(db.String(40))                                          # 最后访问位置 （登录时触发更新）
    access_ip = db.Column(db.String(20))                                                # 最后访问位置（登录时触发更新）
    access_time = db.Column(db.DateTime)                                                # 最后访问时间（登录时触发更新）
    live_node_uuid = db.Column(db.String(40), db.ForeignKey('live_node.uuid'))          # 外键，最后访问直播节点（登录时触发更新）
    products = db.relationship('Channel_product', secondary=apps_products, backref=db.backref('apps', lazy='dynamic'), lazy='dynamic') # 多对多

    @property
    def password(self):
        raise AttributeError(u'密码不可读')

    # 为兼容旧boss，以下加密验证改为md5方式
    @password.setter
    def password(self, password):
        #self.password_hash = generate_password_hash(password)
        self.password_hash = hashlib.md5(password.strip().encode()).hexdigest()

    def verify_password(self, password):
        #return check_password_hash(self.password_hash, password)
        return True if self.password_hash == hashlib.md5(password.strip().encode()).hexdigest() else False

# 电视盒
class Stb(db.Model):
    __tablename__ = 'stb'
    uuid = db.Column(db.String(40), index=True, primary_key=True)
    #sn = db.Column(db.String(40), index=True, nullable=False, unique=True)              # 序列号
    sn = db.Column(db.String(40), index=True)              # 序列号
    model = db.Column(db.String(40))                                                    # 型号（登录时触发更新）
    version = db.Column(db.String(40))                                                  # 软件版本（登录时触发更新）
    status = db.Column(db.String(1), index=True, nullable=False, default=0)             # 启用状态 0 未开通 1 开通 2 禁用
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    purchase_time = db.Column(db.DateTime)                                              # 开通时间
    customer_uuid = db.Column(db.String(40), db.ForeignKey('customer.uuid'))      # 买家外键
    partner_uuid = db.Column(db.String(40), db.ForeignKey('partner.uuid'))        # 合作商外键
    vip_uuid = db.Column(db.String(40), db.ForeignKey('vip.uuid'))               # vip外键
    grouping_uuid = db.Column(db.String(40), db.ForeignKey('stb_grouping.uuid')) # 升级分组外键
    access_location = db.Column(db.String(40))                                       # 最后访问位置（登录时触发更新）
    access_ip = db.Column(db.String(20))                                             # 最后访问位置（登录时触发更新）
    access_time = db.Column(db.DateTime)                                             # 最后访问时间（登录时触发更新）
    live_node_uuid = db.Column(db.String(40), db.ForeignKey('live_node.uuid'))       # 外键，最后访问直播节点（登录时触发更新）
    products = db.relationship('Channel_product', secondary=stbs_products, backref=db.backref('stbs', lazy='dynamic'), lazy='dynamic') # 多对多

# 电视盒硬件类型
class Stb_model(db.Model):
    __table_name__ = 'stb_model'
    uuid = db.Column(db.String(40), index=True, primary_key=True)
    code = db.Column(db.String(40), index=True)
    name = db.Column(db.String(40), index=True, nullable=False)
    cname = db.Column(db.String(40))
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    softwares = db.relationship('Stb_software', backref='stb_models', lazy='dynamic', cascade='all, delete-orphan') # 一对多关系, 支持级联删除

# 电视盒硬件软件
class Stb_software(db.Model):
    __tablename__ = 'stb_software'
    uuid = db.Column(db.String(40), index=True, primary_key=True)
    download_url = db.Column(db.String(255), index=True, nullable=False)
    version = db.Column(db.String(40))
    md5 = db.Column(db.String(40))
    size = db.Column(db.Integer)
    category = db.Column(db.String(1), default=0)           # 版本类型,0测试, 1正式
    status = db.Column(db.String(1), index=True, default=0)             # 发布状态,0停用, 1启用
    force_update = db.Column(db.String(1), default=0)       # 强制升级
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    model_uuid = db.Column(db.String(40), db.ForeignKey('stb_model.uuid', onupdate='CASCADE', ondelete='CASCADE'))  # 型号外键

# 电视盒升级分组
class Stb_grouping(db.Model):
    __tablename__ = 'stb_grouping'
    uuid = db.Column(db.String(40), index=True, primary_key=True)
    cname = db.Column(db.String(40), nullable=False, index=True)
    description = db.Column(db.String(255))
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    stbs = db.relationship('Stb', backref='stb_groupings', lazy='dynamic')
    softwares = db.relationship('Stb_software', secondary=softwares_groupings, backref=db.backref('groupings', lazy='dynamic'), lazy='dynamic') # 多对多

# 电视盒日志
class Stb_upload(db.Model):
    __tablename__ = 'stb_upload'
    uuid = db.Column(db.String(40), index=True, primary_key=True)
    sn = db.Column(db.String(40), nullable=False, index=True)
    access_ip = db.Column(db.String(40))
    access_location = db.Column(db.String(40))
    access_live_node = db.Column(db.String(40))
    access_time = db.Column(db.DateTime)
    speed = db.Column(db.String(40))
    variance = db.Column(db.String(10))

# 国家
class Country(db.Model):
    __tablename__ = 'country'
    uuid = db.Column(db.String(40), index=True, primary_key=True)
    code = db.Column(db.String(40), index=True, nullable=False)
    name = db.Column(db.String(40))
    cname = db.Column(db.String(40))
    continent_uuid = db.Column(db.String(40), db.ForeignKey('continent.uuid'))  # 大洲外键

# 大洲
class Continent(db.Model):
    __tablename__ = 'continent'
    uuid = db.Column(db.String(40), index=True, primary_key=True)
    code = db.Column(db.String(40), nullable=False, index=True)
    name = db.Column(db.String(40))
    cname = db.Column(db.String(40))
    countries = db.relationship('Country', backref='continents', lazy='dynamic')
    nodes = db.relationship('Live_node', secondary=continents_nodes, backref=db.backref('continents', lazy='dynamic'), lazy='dynamic') # 多对多关系

# 直播节点
class Live_node(db.Model):
    __tablename__ = 'live_node'
    uuid = db.Column(db.String(40), index=True, primary_key=True)
    code = db.Column(db.String(40), index=True, nullable=False)
    cname = db.Column(db.String(40), nullable=False)
    alias = db.Column(db.String(40), nullable=False)
    rate = db.Column(db.String(40), nullable=False)
    domain = db.Column(db.String(255), nullable=False)
    speed_test_url = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(1), default='1')                               # 启用状态
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    stbs = db.relationship('Stb', backref='live_node', uselist=False)           # 一对一关系
    channels = db.relationship('Live_channel', backref='nodes', lazy='dynamic', cascade='all, delete-orphan')   # 一对多关系, 支持级联删除

# 直播节点频道
class Live_channel(db.Model):
    __tablename__ = 'live_channel'
    uuid = db.Column(db.String(40), index=True, primary_key=True)
    name = db.Column(db.String(40), nullable=False, index=True)     # 英文频道名
    cname = db.Column(db.String(40), nullable=False)                # 简体频道名
    api = db.Column(db.Text, nullable=False)                        # api接口
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    node_uuid = db.Column(db.String(40), db.ForeignKey('live_node.uuid', onupdate='CASCADE', ondelete='CASCADE'))  # 节点外键

# 产品包
class Channel_product(db.Model):
    __tablename__ = 'channel_product'
    uuid = db.Column(db.String(40), index=True, primary_key=True)
    cname = db.Column(db.String(40), nullable=False, unique=True)
    category = db.Column(db.String(1), default=0)                       # 版本类型,0免费,1正式
    status = db.Column(db.String(1), index=True, default='1')                       # 启用状态
    description = db.Column(db.String(255))
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    channels = db.relationship('Channel', secondary=products_channels, backref=db.backref('products', lazy='dynamic'), lazy='dynamic')  # 多对多关系

# 产品包频道
class Channel(db.Model):
    __tablename__ = 'channel'
    uuid = db.Column(db.String(40), index=True, primary_key=True)
    name = db.Column(db.String(40), nullable=False, index=True)     # 字母频道名
    cname = db.Column(db.String(40), nullable=False)                # 简体频道名
    tname = db.Column(db.String(40))                                # 繁体频道名
    sort_id = db.Column(db.String(4), index=True, nullable=False)               # 排版顺序
    status = db.Column(db.String(1), index=True, default='1')                   # 启用状态
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)

# 频道分类
class Channel_category(db.Model):
    __tablename__ = 'channel_category'
    uuid = db.Column(db.String(40), index=True, primary_key=True, nullable=False)
    name = db.Column(db.String(40), index=True, nullable=False)                 # 字母分类名
    cname = db.Column(db.String(40), nullable=False)                # 简体分类名
    tname = db.Column(db.String(40))                                # 繁体分类名
    sort_id = db.Column(db.String(4), index=True, nullable=False)   # 排版顺序
    status = db.Column(db.String(1), index=True, default='1')       # 启用状态
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    channels = db.relationship('Channel', secondary=categories_channels, backref=db.backref('categories', lazy='dynamic'), lazy='dynamic')  # 多对多关系

# 频道节目单
class Current_epg(db.Model):
    __tablename__ = 'current_epg'
    uuid = db.Column(db.String(40), index=True, primary_key=True, nullable=False)
    name = db.Column(db.String(40), nullable=False, index=True)  # 英文频道名
    cname = db.Column(db.String(40), nullable=False)  # 简体频道名
    tname = db.Column(db.String(40))   # 繁体频道名
    tags = db.Column(db.String(10),  nullable=False)  # 频道分类中文名称
    title = db.Column(db.String(100), nullable=False)  # 节目标题
    start_time = db.Column(db.Integer, nullable=False)  # 节目开始时间
    end_time = db.Column(db.Integer, nullable=False)  # 节目结束时间

# 文件上传
class File_upload(db.Model):
    __tablename__ = 'file_upload'
    uuid = db.Column(db.String(40), index=True, primary_key=True, nullable=False)
    name = db.Column(db.String(128), index=True, nullable=False)
    url = db.Column(db.String(128), nullable=False)
    size = db.Column(db.String(40), nullable=False)
    md5 = db.Column(db.String(40), nullable=False)
    create_time = db.Column(db.DateTime)