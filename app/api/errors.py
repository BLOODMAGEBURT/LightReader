# -*- coding: utf-8 -*-
from flask import jsonify

from app import app

"""
-------------------------------------------------
   File Name：     errors
   Description :
   Author :       Administrator
   date：          2019/4/17 0017
-------------------------------------------------
   Change Activity:
                   2019/4/17 0017:
-------------------------------------------------
"""


def bad_request(error_code, msg):
    return jsonify(error_code, msg)


@app.errorhandler(404)
def not_found_error():
    return bad_request(404, 'resource not found')


@app.errorhandler(500)
def server_error():
    return bad_request(500, 'server internal error')
