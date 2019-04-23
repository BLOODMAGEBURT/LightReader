import logging

import rq
from flask import Flask, request
from flask_babel import Babel
from flask_bootstrap import Bootstrap
from flask_caching import Cache
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, configure_uploads, TEXT
from redis import Redis

from config import Config

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.config.from_object(Config)
login = LoginManager(app)
db = SQLAlchemy(app)
migrate = Migrate(app=app, db=db)
bootstrap = Bootstrap(app)
login.login_view = 'login'
text = UploadSet("downloads", TEXT)
configure_uploads(app, text)
moment = Moment(app)
babel = Babel(app)
redis = Redis.from_url(app.config['REDIS_URL'])
app.task_queue = rq.Queue('lightreader-tasks', connection=redis)

cache = Cache(app, config={
    'CACHE_TYPE': Config.CACHE_TYPE,
    'CACHE_REDIS_HOST': Config.CACHE_REDIS_HOST,
    'CACHE_REDIS_PORT': Config.CACHE_REDIS_PORT,
    'CACHE_REDIS_PASSWORD': Config.CACHE_REDIS_PASSWORD,
    'CACHE_REDIS_DB': Config.CACHE_REDIS_DB
})


def cache_key():
    key = request.path + '?' + request.url.rsplit('/', 1)[-1]
    return key


from app.order import bp as order_bp

app.register_blueprint(order_bp)

from app.api import bp as api_bp

app.register_blueprint(api_bp, url_prefix='/api')

from app import models, routes


# import create_db


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])
