# -*- coding: utf-8 -*-
from flask import Blueprint
"""
-------------------------------------------------
   File Name：     __init__.py
   Description :
   Author :       Administrator
   date：          2019/6/4 0004
-------------------------------------------------
   Change Activity:
                   2019/6/4 0004:
-------------------------------------------------
"""
bp = Blueprint('main', __name__)

from app.main import routes