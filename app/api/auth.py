# -*- coding: utf-8 -*-
from flask import g
from flask_httpauth import HTTPTokenAuth

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
