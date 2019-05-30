# -*- coding: utf-8 -*-
from flask import request, g, jsonify

from app import db
from app import logging
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.models import Todo, TodoType

"""
-------------------------------------------------
   File Name：     todo
   Description :
   Author :       Administrator
   date：          2019/5/28 0028
-------------------------------------------------
   Change Activity:
                   2019/5/28 0028:
-------------------------------------------------
"""


@bp.route('/todo_types', methods=['GET'])
@token_auth.login_required
def get_todo_types():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 15, type=int), 100)
    query = TodoType.query.filter_by(is_deleted=False)
    return jsonify(TodoType.to_collections_dict(query, page, per_page, 'api.get_todo_types'))


@bp.route('/todo_types/<tid>', methods=['GET'])
@token_auth.login_required
def get_todo_type(tid):
    todo_type = TodoType.query.get_or_404(tid)
    return jsonify(todo_type.to_dict())


@bp.route('/todo_types', methods=['POST'])
@token_auth.login_required
def add_todo_types():
    data = request.get_json() or {}
    if 'type_name' not in data:
        return bad_request(400, 'type_name must be include')

    todo_type = TodoType.query.filter_by(type_name=data['type_name']).first()
    if todo_type is not None:
        return bad_request(400, 'please use a different type_name')
    todo_type = TodoType()
    todo_type.user = g.current_user
    todo_type.from_dict(data)
    db.session.add(todo_type)
    db.session.commit()
    return jsonify(todo_type.to_dict())


@bp.route('/todo_types', methods=['PUT'])
@token_auth.login_required
def edit_todo_types():
    data = request.get_json() or {}
    if ('type_name' or 'id') not in data:
        return bad_request(400, 'id , type_name  must be include')
    todo_type = TodoType.query.get_or_404(data['id'])
    todo_type.from_dict(data)
    db.session.commit()
    return jsonify(todo_type.to_dict())


@bp.route('/todo_types/<tid>', methods=['DELETE'])
@token_auth.login_required
def del_todo_types(tid):
    todo_type = TodoType.query.get_or_404(tid)
    todo_type.is_deleted = True
    db.session.commit()
    return jsonify(todo_type.to_dict())


@bp.route('/todo', methods=['GET'])
@token_auth.login_required
def get_todos():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 15, type=int), 100)
    query = Todo.query.filter_by(user=g.current_user)
    return jsonify(Todo.to_collections_dict(query, page, per_page, 'api.get_todos'))


@bp.route('/todo/<tid>', methods=['GET'])
@token_auth.login_required
def get_todo(tid):
    pass


@bp.route('/todo', methods=['POST'])
@token_auth.login_required
def add_todo():
    data = request.get_json() or {}
    if ('type_id' and 'title') not in data:
        return bad_request(400, 'type_id title must be included')
    todo = Todo()
    todo.user = g.current_user
    todo.from_dict(data)
    db.session.add(todo)
    db.session.commit()
    return jsonify(todo.to_dict())


@bp.route('/todo/<tid>', methods=['PUT'])
@token_auth.login_required
def edit_todo(tid):
    todo = Todo.query.get_or_404(tid)
    data = request.get_json() or {}

    if ('title ' and 'is_completed') not in data:
        return bad_request(400, 'title and is_completed must included')

    todo.from_dict(data)
    db.session.commit()
    return jsonify(todo.to_dict())


@bp.route('/todo/<tid>', methods=['DELETE'])
@token_auth.login_required
def del_todo(tid):
    todo = Todo.query.get_or_404(tid)
    todo.is_deleted = True
    db.session.commit()
    return jsonify(todo.to_dict())
