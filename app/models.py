from datetime import datetime

import redis
import rq
from flask import current_app
from flask_login import UserMixin, current_user
from rq.exceptions import NoSuchJobError
from werkzeug.security import check_password_hash, generate_password_hash

import app
from app import db, login


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    # email = db.Column(db.String(50),unique=True,nullable=False)
    password_hash = db.Column(db.String(128))
    can_download = db.Column(db.Boolean)  # 表示用户是否有下载权限，0表示没有，1表示有
    last_seen = db.Column(db.DateTime, default=datetime.now())
    user_ip = db.Column(db.String(20))
    user_agent = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean)  # 表示用户是否是管理员，0表示不是，1表示是
    font_size = db.Column(db.String(10))  # 用户设置的字体大小
    night_mode = db.Column(db.Boolean, default=0)  # 夜间模式，0表示关，1表示开

    tasks = db.relationship('Task', backref='user', lazy='dynamic')
    orders = db.relationship('Order', backref='user', lazy='dynamic')

    def __repr__(self):
        return '<User {%s}>' % self.name

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # 以下几个方法存在不明bug
    # def is_subscribing(self,book):
    #     return self.subscribing.filter(subscribe.c.book_id == book.id).count() > 0
    #
    # def subscribe(self,book):
    #     if not self.is_subscribing(book):
    #         self.subscribing.append(book)
    #
    # def un_subscribe(self,book):
    #     if self.is_subscribing(book):
    #         self.subscribing.remove(book)

    def launch_task(self, name, description, source_id, book_id):
        rq_job = current_app.task_queue.enqueue('app.tasks.' + name, current_user.id, source_id, book_id)
        task = Task(id=rq_job.get_id(), name=name, description=description, user=self)
        db.session.add(task)
        db.session.commit()
        return task

    def get_tasks_in_progress(self):
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self, complete=False).first()

    # 提单
    def submit_order(self):
        return '{} you submitted an order'.format(self.name)

    # 查单
    def get_orders(self):
        return self.orders


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('type.id'))
    type_name = db.Column(db.String(128), nullable=False)
    coupon_code = db.Column(db.String(10), nullable=False)
    coupon_num = db.Column(db.Integer, nullable=False)
    coupon_img = db.Column(db.String(128), nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    edit_time = db.Column(db.DateTime, default=datetime.utcnow)


class Type(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)
    orders = db.relationship('Order', backref='type', lazy="dynamic")
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class Subscribe(db.Model):
    __tablename__ = 'subscribe'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'))
    book_id = db.Column(db.String(128))
    book_name = db.Column(db.String(128))
    chapter = db.Column(db.String(128))
    source_id = db.Column(db.String(128))
    time = db.Column(db.DateTime, default=datetime.now)
    chapter_name = db.Column(db.String(128))

    user = db.relationship('User', backref=db.backref('subscribing', lazy='dynamic'))

    def __repr__(self):
        return '<User>{} subscribing <Book>{} reading <chapter>{}'.format(self.user_id, self.book_id, self.chapter)


class Download(db.Model):
    __tablename__ = 'download'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'))
    book_id = db.Column(db.String(128))
    book_name = db.Column(db.String(128))
    chapter = db.Column(db.Integer)
    source_id = db.Column(db.String(128))
    time = db.Column(db.DateTime, default=datetime.now())
    txt_name = db.Column(db.String(128))
    lock = db.Column(db.Boolean)  # 下载锁，1表示锁住，0表示开锁
    chapter_name = db.Column(db.String(128))

    user = db.relationship('User', backref=db.backref('downloaded', lazy='dynamic'))

    def __repr__(self):
        return '<User>{} download <book>{}'.format(self.user.name, self.book_name)


class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=app.redis)
        except(redis.exceptions.RedisError, NoSuchJobError) as e:
            print(e)
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100


class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.String(128))
    book_name = db.Column(db.String(128))
    chapter_index = db.Column(db.Integer)
    chapter_name = db.Column(db.String(128))
    source_id = db.Column(db.String(128))
    source_name = db.Column(db.String(128))
    time = db.Column(db.DateTime, default=datetime.now())
    is_subscribe = db.Column(db.Boolean)

    user = db.relationship('User', backref=db.backref('record', lazy='dynamic'))

    def __repr__(self):
        return '<User:{} read Book:{}>'.format(self.user.name, self.book_name)


@login.user_loader
def load_user(uid):
    user = User.query.get(int(uid))
    return user
