import logging
import ssl
import os
from logging.handlers import SMTPHandler, RotatingFileHandler

import rq
from flask import Flask, request, current_app
from flask_babel import Babel
from flask_bootstrap import Bootstrap
from flask_caching import Cache
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, configure_uploads, TEXT
from redis import Redis

from config import Config

logging.basicConfig(level=logging.INFO)

# 工厂模式创建app

# init db
db = SQLAlchemy()
# init migrate
migrate = Migrate()
# flask-login
login = LoginManager()
login.login_view = 'login'
# email
mail = Mail()
# moment
moment = Moment()
# bootstrap
bootstrap = Bootstrap()
# babel
babel = Babel()
# 忽略ssl验证
ssl._create_default_https_context = ssl._create_unverified_context

# flask-cache
cache = Cache(config={
    'CACHE_TYPE': Config.CACHE_TYPE,
    'CACHE_REDIS_HOST': Config.CACHE_REDIS_HOST,
    'CACHE_REDIS_PORT': Config.CACHE_REDIS_PORT,
    'CACHE_REDIS_PASSWORD': Config.CACHE_REDIS_PASSWORD,
    'CACHE_REDIS_DB': Config.CACHE_REDIS_DB
})


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)
    text = UploadSet("downloads", TEXT)
    configure_uploads(app, text)

    redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('lightreader-tasks', connection=redis)

    cache.init_app(app)

    from app.order import bp as order_bp

    app.register_blueprint(order_bp)

    from app.api import bp as api_bp

    app.register_blueprint(api_bp, url_prefix='/api')

    if not (app.debug or app.testing):
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr=app.config['MAIL_USERNAME'],
                toaddrs=app.config['ADMINS'],
                subject='Microblog Failure',
                credentials=auth,
                secure=secure
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        # log into the file
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler(
            filename=app.config['LOG_FILE'],
            maxBytes=10240,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: '
                                                    '%(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.ERROR)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Microblog startup')

    return app


# import create_db


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])


from app import models, routes
