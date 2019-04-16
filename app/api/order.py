# -*- coding: utf-8 -*-
from app.api import bp
from flask import jsonify
from app.models import Order
"""
-------------------------------------------------
   File Name：     order
   Description :
   Author :       Administrator
   date：          2019/4/16 0016
-------------------------------------------------
   Change Activity:
                   2019/4/16 0016:
-------------------------------------------------
"""


@bp.route('/orders', methods=['GET'])
def get_orders():

    pass


@bp.route('/orders/<oid>', methods=['GET'])
def get_order(oid):
    pass


@bp.route('/orders', methods=['POST'])
def add_order():
    pass


@bp.route('/orders/<oid>', methods=['PUT'])
def update_order(oid):
    pass


@bp.route('/orders/<oid>', methods=['DELETE'])
def del_order(oid):
    pass
