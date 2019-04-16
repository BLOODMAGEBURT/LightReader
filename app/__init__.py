import rq
from flask import Flask, request
from flask_babel import Babel
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, configure_uploads, TEXT
from redis import Redis

from config import Config

# class MySQLAlchemy(SQLAlchemy):
#     def create_session(self, options):
#         options['autoflush'] = False
#         return SignallingSession(self, **options)


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

from app.order import bp as order_bp

app.register_blueprint(order_bp)

from app.api import bp as api_bp

app.register_blueprint(api_bp, url_prefix='/api')

from app import models, routes


# import create_db


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])
