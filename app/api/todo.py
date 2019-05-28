# -*- coding: utf-8 -*-
from flask import request, g, jsonify

from app import db
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


@bp.route('/todo_types/{id}', methods=['GET'])
@token_auth.login_required
def get_todo_type(id):
    pass


@bp.route('/todo_types', methods=['POST'])
@token_auth.login_required
def add_todo_types():
    data = request.get_json() or {}
    if 'name' not in data:
        return bad_request(400, 'name must be include')

    todo_type = TodoType.query.filter_by(name=data['name']).first()
    if todo_type is not None:
        return bad_request(400, 'please use a different name')
    todo_type = TodoType()
    todo_type.user = g.current_user
    todo_type.from_dict(data)
    db.session.add(todo_type)
    db.session.commit()
    return jsonify(todo_type.to_dict())


@bp.route('/todo_types', methods=['PUT'])
@token_auth.login_required
def edit_todo_types():
    pass


@bp.route('/todo_types/{id}', methods=['DELETE'])
@token_auth.login_required
def del_todo_types(id):
    pass


@bp.route('/todo', methods=['GET'])
@token_auth.login_required
def get_todos():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 15, type=int), 100)
    query = Todo.query.filter_by(user=g.current_user)
    return jsonify(Todo.to_collections_dict(query, page, per_page, 'api.get_todos'))


@bp.route('/todo/{is}', methods=['GET'])
@token_auth.login_required
def get_todo(id):
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


@bp.route('/todo/{id}', methods=['PUT'])
@token_auth.login_required
def edit_todo(id):
    pass


@bp.route('/todo/{id}', methods=['DELETE'])
@token_auth.login_required
def del_todo(id):
    pass
