# -*- coding: utf-8 -*-
from flask import g
from flask import jsonify, request

from app import db
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
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
    page = request.args.get('page', default=1, type=int)
    per_page = min(request.args.get('per_page', default=15, type=int), 100)
    resource = Order.to_collections_dict(Order.query, page, per_page, 'api.get_orders')
    return jsonify(resource)


@bp.route('/orders/<oid>', methods=['GET'])
@token_auth.login_required
def get_order(oid):
    order = Order.query.get_or_404(oid)
    return jsonify(order.to_dict())


@bp.route('/orders', methods=['POST'])
@token_auth.login_required
def add_order():
    data = request.get_json() or {}
    if ('type_id' and 'type_name' and 'coupon_num' and 'order_items') not in data:
        return bad_request(400, 'type_id type_name, coupon_num, order_items must be included')

    # 判断非空
    if not data['order_items']:
        return bad_request(400, 'order_items can not be empty')

    data['user_id'] = g.current_user.id
    data['user_name'] = g.current_user.name
    order = Order()
    order.from_dict(data)
    db.session.add(order)
    db.session.commit()
    return jsonify(order.to_dict())


@bp.route('/orders/<oid>', methods=['PUT'])
@token_auth.login_required
def update_order(oid):
    pass


@bp.route('/orders/<oid>', methods=['DELETE'])
@token_auth.login_required
def del_order(oid):
    pass
