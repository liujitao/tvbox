# -*- coding: utf-8 -*-
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_geoip import GeoIP
from flask_redis import FlaskRedis
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from config import config

RootLog = logging.getLogger()

db = SQLAlchemy()
redis_store = FlaskRedis(config_prefix='REDIS0')
redis_que_log = FlaskRedis(config_prefix='REDIS1')
geoip = GeoIP()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'main.index'
login_manager.refresh_view = 'main.index'
login_manager.needs_refresh_message = u'用户已经退出登录状态，请重新登录'
login_manager.login_message = u'用户尚未登录'


def create_app(config_name):
    app = Flask(__name__)
    
    # 默认配置    
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # mysql
    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
    app.config['LOG_NAME'] = 'logs/suntv.log'
    db.app = app
    db.init_app(app)

    # redis
    redis_store.init_app(app)
    redis_que_log.init_app(app)
    
    # geoip
    geoip.init_app(app)

    # 错误处理
    set_error_handlers(app)

    # 蓝图 
    register_blueprints(app)

    # 登录
    login_manager.init_app(app)

    # 记录日志
    setup_logging(app)

    # 定时任务
    from basefunc import Scheduler
    Scheduler.scheduler_tasks()

    return app


def setup_logging(app):
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s [in %(pathname)s:%(lineno)d]')  # 每行日志的前缀设置
    fileTimeHandler = TimedRotatingFileHandler(filename=app.config['LOG_NAME'], when='D', interval=1, backupCount=7)
    fileTimeHandler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO)
    RootLog.addHandler(fileTimeHandler)


def register_blueprints(app):
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .api1_0 import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api1.0')


def set_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('403.html'), 403

    @app.errorhandler(401)
    def gone(error):
        return render_template('401.html'), 401

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template('500.html'), 500
