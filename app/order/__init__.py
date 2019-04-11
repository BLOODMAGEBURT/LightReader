# -*- coding: utf-8 -*-
from flask import Blueprint

"""
-------------------------------------------------
   File Name：     __init__.py
   Description :
   Author :       Administrator
   date：          2019/4/11 0011
-------------------------------------------------
   Change Activity:
                   2019/4/11 0011:
-------------------------------------------------
"""
bp = Blueprint('order', __name__)

from app.order import routes
