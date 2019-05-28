import base64
import os
from datetime import datetime, timedelta

import redis
import rq
from flask import current_app, url_for
from flask_login import UserMixin, current_user
from rq.exceptions import NoSuchJobError
from werkzeug.security import check_password_hash, generate_password_hash

import app
from app import db, login


class PaginateMixIn(object):
    @staticmethod
    def to_collections_dict(query, page, per_page, end_point, **kwargs):
        resources = query.paginate(page, per_page, False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self_url': url_for(end_point, page=page, per_page=per_page, **kwargs),
                'next_url': url_for(end_point, page=page + 1, per_page=per_page,
                                    **kwargs) if resources.has_next else None,
                'pre_url': url_for(end_point, page=page - 1, per_page=per_page,
                                   **kwargs) if resources.has_prev else None
            }
        }

        return data


class User(UserMixin, db.Model, PaginateMixIn):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    # email = db.Column(db.String(50),unique=True,nullable=False)
    password_hash = db.Column(db.String(128))
    can_download = db.Column(db.Boolean, default=0)  # 表示用户是否有下载权限，0表示没有，1表示有
    last_seen = db.Column(db.DateTime, default=datetime.now)
    user_ip = db.Column(db.String(20))
    user_agent = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=0)  # 表示用户是否是管理员，0表示不是，1表示是
    font_size = db.Column(db.String(10))  # 用户设置的字体大小
    night_mode = db.Column(db.Boolean, default=0)  # 夜间模式，0表示关，1表示开
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)
    tasks = db.relationship('Task', backref='user', lazy='dynamic')
    orders = db.relationship('Order', backref='user', lazy='dynamic')
    todo_types = db.relationship('TodoType', backref='user', lazy='dynamic')
    todo_list = db.relationship('Todo', backref='user', lazy='dynamic')

    def __repr__(self):
        return '<User {%s}>' % self.name

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    def submit_order(self, order):
        order.user = self
        db.session.add(order)
        return '{} you submitted an order, order id is :{}'.format(self.name, order.id)

    # 查单
    def get_orders(self, status):
        if status is not None:
            return self.orders.filter_by(status=status).all()

        # 其他的获取全部
        return self.orders

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        # db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user


class Order(db.Model, PaginateMixIn):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('type.id'))
    type_name = db.Column(db.String(128), nullable=False)
    coupon_num = db.Column(db.Integer, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    edit_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Integer, default=1)  # 1为未完成， 2 为已完成
    order_items = db.relationship('OrderItem', backref='order', lazy='dynamic')

    def to_dict(self):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name,
            'type_id': self.type_id,
            'type_name': self.type_name,
            'coupon_num': self.coupon_num,
            'create_time': self.create_time.isoformat() + 'Z',
            'edit_time': self.edit_time.isoformat() + "Z",
            'status': self.status,
            'order_items': [order_item.to_dict() for order_item in self.order_items]
        }
        return data

    def from_dict(self, data, include_items=True, is_update=False):
        for field in ['user_id', 'user_name', 'type_id', 'type_name', 'coupon_num']:
            if field in data:
                setattr(self, field, data[field])
        if include_items:
            # 循环添加子表
            for item in data['order_items']:
                order_item = OrderItem()
                item['order_id'] = self.id
                order_item.from_dict(item)

        if is_update:
            self.edit_time = datetime.utcnow()


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    coupon_code = db.Column(db.String(50), nullable=False)
    coupon_img = db.Column(db.String(128), nullable=False)

    def to_dict(self):
        data = {
            'id': self.id,
            'order_id': self.order_id,
            'coupon_code': self.coupon_code,
            'coupon_img': self.coupon_img
        }
        return data

    def from_dict(self, data):
        for field in ['order_id', 'coupon_code', 'coupon_img']:
            if field in data:
                setattr(self, field, data[field])


class Type(db.Model, PaginateMixIn):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)
    orders = db.relationship('Order', backref='type', lazy="dynamic")
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            'is_deleted': self.is_deleted,
            'create_time': self.create_time.isoformat() + 'Z',
            'orders': [order.to_dict() for order in self.orders]
        }
        return data

    def from_dict(self, data):
        if 'name' in data:
            setattr(self, 'name', data['name'])


class TodoType(db.Model, PaginateMixIn):
    __tablename__ = 'todo_type'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(50), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)
    todo_items = db.relationship('Todo', backref='type', lazy='dynamic')

    def to_dict(self):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'is_deleted': self.is_deleted
        }
        return data

    def from_dict(self, data):
        if 'name' in data:
            setattr(self, 'name', data['name'])


class Todo(db.Model, PaginateMixIn):
    id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey('todo_type.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(128), nullable=False)
    detail = db.Column(db.String(300))
    is_completed = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        data = {
            'id': self.id,
            'type_id': self.type_id,
            'user_id': self.user_id,
            'user_name': self.user.name,
            'title': self.title,
            'detail': self.detail,
            'is_completed': self.is_completed,
            'is_deleted': self.is_deleted,
            'create_time': self.create_time
        }

        return data

    def from_dict(self, todo_data):
        for field in ['type_id', 'title', 'detail', 'is_completed', 'is_deleted']:
            if field in todo_data:
                setattr(self, field, todo_data[field])


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
