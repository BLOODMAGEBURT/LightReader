# -*- coding: utf-8 -*-
from flask import url_for
from app.order import bp
from flask_login import login_required, current_user
"""
-------------------------------------------------
   File Name：     routes
   Description :
   Author :       Administrator
   date：          2019/4/11 0011
-------------------------------------------------
   Change Activity:
                   2019/4/11 0011:
-------------------------------------------------
"""


@bp.route('/orders', methods=['GET', 'POST'])
@login_required
def orders():
    url_for()
    return 'hi {}'.format(current_user.name)
