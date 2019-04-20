# -*- coding: utf-8 -*-
from flask import g, request, jsonify
from flask_httpauth import HTTPTokenAuth

from app import db
from app.api import bp
from app.api.errors import bad_request
from app.models import User

"""
-------------------------------------------------
   File Name：     auth
   Description :
   Author :       Administrator
   date：          2019/4/19 0019
-------------------------------------------------
   Change Activity:
                   2019/4/19 0019:
-------------------------------------------------
"""
token_auth = HTTPTokenAuth()


@token_auth.verify_token
def verify_token(token):
    g.current_user = User.check_token(token) if token else None

    return g.current_user is not None


@token_auth.error_handler
def token_auth_error():
    return bad_request(401, 'auth error')


@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    if ('name' and 'pwd') not in data:
        return bad_request(400, 'name  and pwd must be included')
    user = User.query.filter_by(name=data['name']).first()
    if user is not None:
        return bad_request(400, 'please use a different name')

    user = User(name=data['name'])
    user.set_password(data['pwd'])
    db.session.add(user)
    db.session.commit()
    token = user.get_token()
    return jsonify({
        'token': token,
        'name': data['name']
    })


@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    if ('name' and 'pwd') not in data:
        return bad_request(400, 'name  and pwd must be included')

    user = User.query.filter_by(name=data['name']).first()

    if user is None or not user.check_password(data['pwd']):
        return bad_request(400, 'login failed, wrong name or pwd')

    token = user.get_token()
    db.session.commit()
    return jsonify({
        'token': token,
        'name': user.name
    })


@bp.route('/logout', methods=['POST'])
@token_auth.login_required
def logout():
    g.current_user.revoke_token()
    db.session.commit()
    return jsonify({
        'code': 200,
        'msg': 'logout success'
    })
