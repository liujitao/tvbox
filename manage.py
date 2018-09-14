# -*- coding: utf-8 -*-

from app import create_app, db
from flask_script import Manager, Shell
import os

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)


def make_shell_context():
    return dict(app=app, db=db)

manager.add_command('shell', Shell(make_context=make_shell_context))


@manager.command 
def deploy(): 
    from app.models import User, Channel_category, Continent, Country, Channel, Channel_product, Stb_model
    from datetime import datetime
    import uuid, json

    db.create_all()

    '''
    # 建立管理员
    user = User(uuid=str(uuid.uuid1()), name='admin', cname=u'管理员', password='@admin', create_time=datetime.now())
    db.session.add(user)

    # 建立频道分类
    category = [
        ('yangshi', u'央视', u'央視', '1', '1'), 
        ('weishi', u'卫视', u'衛視', '2', '1'), 
        ('difang', u'地方', u'地方', '3', '1'), 
        ('gaoqing', u'高清', u'高清', '4', '1'),
        ('reimen', u'热门', u'熱門', '5', '1'), 
        ('haiwai', u'海外', u'海外', '6', '1'), 
        ('guoji', u'国际', u'國際', '7', '1'), 
        ('jiaoyu', u'教育', u'教育', '8', '1'),
        ('yueyu', u'粤语', u'粵語', '9', '1'),  
        ('yueyu', u'测试', u'測試', '10', '1'), 
        ('xuni', u'虚拟', u'虛擬', '11', '1'), 
        ('zhongyangguangbo', u'中央广播', u'中央廣播', '12', '1'),
        ('defangguangbo', u'地方广播', u'地方廣播', '13', '1'),
        ('wenyiguangbo', u'文艺广播', u'文藝廣播', '14', '1'), 
        ('yinyueguangbo', u'音乐广播', u'音樂廣播', '15', '1')
    ]

    channel_category = [ Channel_category(uuid=str(uuid.uuid1()), name=name, cname=cname, tname=tname, sort_id=sort_id, status=status, create_time=datetime.now())
        for name, cname, tname, sort_id, status in category ]
    db.session.add_all(channel_category)
    '''

    # 建立地区
    with open('continent.json') as f_continent:
        for cont in json.load(f_continent):
            continent = Continent(uuid=str(uuid.uuid1()), code=cont['code'], name=cont['name'], cname=cont['cname'])
            db.session.add(continent)

            with open('country.json') as f_country:
                country = [ Country(uuid=str(uuid.uuid1()), code=coun['country_code'], name=coun['country_name'], cname=coun['country_cname'], continents=continent)
                     for coun in json.load(f_country) if coun['continent_code'] == cont['code']]
                db.session.add_all(country)
            
            db.session.flush()

    '''
    # 建立频道
    channel = Channel(uuid=str(uuid.uuid1()), name='CCTV1', cname=u'央视综合', tname=u'央視綜合', sort_id='1', create_time=datetime.now())
    db.session.add(channel)

    # 建立默认产品包
    product = Channel_product(uuid=str(uuid.uuid1()), cname=u'_默认产品包_', description=u'仅包括少量频道用于试看', status='1', create_time=datetime.now())
    db.session.add(product)

    # 建立型号
    model = [ Stb_model(uuid=str(uuid.uuid1()), code=code, name=name, cname=name, create_time=datetime.now())
        for code, name, in [('PHD', 'suntv-hd box'), ('MTL', 'suntv-hd 3s')] ]
    db.session.add_all(model)
    '''
    
    db.session.commit()

if __name__ == '__main__':
    manager.run()
