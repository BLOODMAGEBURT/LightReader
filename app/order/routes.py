# -*- coding: utf-8 -*-
from flask_login import current_user

from app.order import bp

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
def orders():
    return 'hi {}'.format(current_user.name)
