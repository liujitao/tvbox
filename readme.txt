一、安装方法
1. 数据库
安装
yum -y install mariadb-server mariadb

修改配置文件
/etc/my.cnf 增加
group_concat_max_len=200000

重启服务
systemctl enable mariadb && systemctl restart mariadb

建库和授权
mysql -u root -p
CREATE DATABASE IF NOT EXISTS `suntv` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
grant all privileges on suntv.* to suntv@'172.31.30.244' identified by 'TvM@suntv';

2. redis
安装
yum -y install redis

修改配置文件
/etc/redis.conf 增加密码
requirepass TvM@suntv 

重启服务
systemctl enable redis && systemctl restart redis 

3. 代码 
安装
yum -y install git

下载
git clone http://code.tvmining.com/angang/suntv /opt/suntv

4. python环境
安装
yum -y install python-pip python-virtualenv

建立虚拟环境
virtualenv /opt/suntv/.venv

进入虚拟环境
source /opt/suntv/.venv/bin/activate

安装模块
pip install pip --upgrade -i http://pypi.douban.com/simple
pip install gunicorn gevent apscheduler pytz flask flask_login flask_sqlalchemy flask_script flask_geoip flask_redis PyJWT mysql-python pypinyin requests -i https://pypi.douban.com/simple

5. 数据初始化
修改配置文件
config.py 修改以下内容
BOSS_CONFIG - domain - api 变更为本机公网ip
mysql 数据库url
redis 数据库url

运行
python manage.py deploy
建立默认管理员(admin / @admin)，默认产品包、频道、频道分类、国家地区

6. nginx uwsgi supervisor
安装
yum -y install nginx supervisor

配置
cp suntv_nginx.conf /etc/nginx/conf.d/suntv.conf
cp supervisord_gunicorn.ini /etc/supervisord.d/gunicorn.ini

重启服务
systemctl enable supervisord && systemctl restart supervisord
systemctl enable nginx && systemctl restart nginx 

二、使用方法
1. 直播节点 
根据实时情况填写，代码必须为英文大写，域名是流服务器配置的域名或者ip。
测速地址用于电视盒测速使用，配置时需先将测速文件上传到直播流服务器。
新建成功后，待新增频道处会出现需同步的频道数量，点击操作中的同步按钮写数据库，操作成功后已生效频道处会显示频道数量。
当直播流服务器频道发生变化时，待新增频道和待移除频道处会显示发生变化的频道数量，这时需要进行同步操作。

2. 频道（产品包使用）
当直播流服务器频道同步后，如果所有直播频道的合集多于或者少于当前产品包使用频道的数量时，会提示同步。
同步后，所有新增的产品包频道状态显示为新增，需要进行数据变更，包括繁体频道名称、顺序号、关联频道分类、关联产品包（如果没有建立，先不指定），状态需设置为启用。
排序号用于电视盒UI使用，同一频道分组的频道排序号最好不要重复。

3. 频道分类
所有新频道需要指派到频道分类中。可以在这里勾选频道，也可以在频道模块中指派每个频道对应的频道分类。
排序号用于电视盒UI使用，最好不要重复。

3. 产品包
数据初始化时，会建立默认产品包，这个用于试看用户，正常用户需要指定其他产品包。产品包可进行叠加指定，频道重复部分系统会自动取唯一。
产品包是根据频道分类分组频道的，如果频道分类未建立，或者频道分类中不包含频道，此处为空。

4. 客户信息
购买电视盒的客户信息，一个用户可购买多个电视盒。

5. 超级会员
后续增值功能。电视盒与会员卡绑定后，在有效期之内，直播与点播中的广告会自动取消，增加用户体验效果。
支持批量生成各时间区域的会员卡，绑定电视盒开始计时，截止至失效时间。

6. 合作商
电视盒关联合作商后，会在播放界面右上角显示合作商的logo

7. APP
android & ios 播放app应用的帐号。支持批量导入

8. 电视盒
硬件清单（电视盒）sn是电视盒唯一标识，用于播放认证使用，型号与产品包必须关联。可单一录入，也可以下载模板，批量导入。
电视盒初始状态为未开通，第一次登录时会将状态设置为开通状态。如果设置为停用状态，将不允放播放。
软件版本，访问时间，访问位置，访问直播节点在客户端每次认证时提交，用于记录用户最后一次播放状态。

9. 硬件型号
不同厂家生产的电视盒

10. 软件升级
每种电视盒对应的升级软件，用于升级与测试

11. 服务区域
用于查询直播服务器的覆盖范围

12. 文件上传
用于往boss系统上传 apk jpg png gif csv txt格式的文件。比如合作商的logo文件，用于升级的apk文件。

13. 按钮 
操作字段下一般包含3个按钮，‘眼晴’是查看功能，可以查看记录包含UUID的的所有信息；‘写字本’是编辑功能，用于修改记录；‘垃圾筒’是删除功能。
节点模块包含一个同步按钮，用于将直播流服务器的频道内容同步到BOSS数据库

表头一般包含以下按钮
‘文本’是新建功能，‘垃圾筒’是删除功能，‘闪电’是批量导入功能
频道模块包含一个同步按钮，用于将所有直播流节点导入的频道做合并处理，同步到产品包所用的频道表。

14. 搜索和排序
表头中带有放大镜图标的字段均支持模糊中英文搜索。
状态与会员只支持精确搜索。
会员： 会员，永久会员，30天会员，90天会员，1年会员，3年会员
状态： 未开通，已开通，已停用，已停用，禁用，启用，新增

15. 禁用与启用
带有禁用属性的记录均不会出现在下拉菜单中。
