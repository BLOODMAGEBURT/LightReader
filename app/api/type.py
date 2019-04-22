# -*- coding: utf-8 -*-
import logging

from flask import request, jsonify

from app import db, cache, cache_key
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.models import Type

"""
-------------------------------------------------
   File Name：     type
   Description :
   Author :       Administrator
   date：          2019/4/17 0017
-------------------------------------------------
   Change Activity:
                   2019/4/17 0017:
-------------------------------------------------
"""


@bp.route('/types', methods=['GET'])
@token_auth.login_required
@cache.cached(timeout=300, key_prefix=cache_key)
def get_types():
    page = request.args.get('page', default=1, type=int)
    per_page = min(request.args.get('per_page', default=15, type=int), 100)
    logging.info('request_path:{}'.format(request.path))
    logging.info('request_url:{}'.format(request.url))
    query = Type.query.filter_by(is_deleted=False)
    return jsonify(Type.to_collections_dict(query, page, per_page, 'api.get_types'))


@bp.route('/types/<tid>', methods=['GET'])
@token_auth.login_required
@cache.memoize(timeout=300)
def get_type(tid):
    logging.info('request_path:{}'.format(request.path))
    order_type = Type.query.get_or_404(tid)

    return jsonify(order_type.to_dict())


@bp.route('/types', methods=['POST'])
@token_auth.login_required
def add_type():
    data = request.get_json() or {}
    if 'name' not in data:
        return bad_request(400, 'name must be included')

    if Type.query.filter_by(name=data['name']).first() is not None:
        return bad_request(400, 'please use a different name')

    order_type = Type()
    order_type.from_dict(data)
    db.session.add(order_type)
    db.session.commit()
    return jsonify(order_type.to_dict())


@bp.route('/types/<tid>', methods=['PUT'])
@token_auth.login_required
def update_type(tid):
    order_type = Type.query.get_or_404(tid)

    data = request.get_json() or {}
    if ('id ' and 'name') not in data:
        return bad_request(400, 'id and name must included')
    order_type.from_dict(data)
    db.session.commit()
    return jsonify(order_type.to_dict())


@bp.route('/types/<tid>', methods=['DELETE'])
@token_auth.login_required
def del_type(tid):
    order_type = Type.query.get_or_404(tid)
    order_type.is_deleted = True
    db.session.commit()
    return jsonify({
        'code': 200,
        'msg': 'success deleted'
    })
