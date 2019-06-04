# -*- coding: utf-8 -*-
from flask import jsonify

from app import create_app

"""
-------------------------------------------------
   File Name：     errors
   Description :
   Author :       Administrator
   date：          2019/4/17 0017
-------------------------------------------------
   Change Activity:f
                   2019/4/17 0017:
-------------------------------------------------
"""
app = create_app()
app.app_context().push()


def bad_request(error_code, msg):
    return jsonify({
        'code': error_code,
        'msg': msg
    })


@app.errorhandler(404)
def not_found_error(error):
    return bad_request(404, 'resource not found')


@app.errorhandler(405)
def method_not_allowed(error):
    return bad_request(405, 'method not allowed')


@app.errorhandler(500)
def server_error(error):
    return bad_request(500, 'server internal error')
