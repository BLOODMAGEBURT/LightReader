# -*- coding: utf-8 -*-
import time
from functools import wraps

from flask import request
from werkzeug.contrib.cache import SimpleCache

"""
-------------------------------------------------
   File Name：     cache
   Description :  自定义的cache装饰器，后续使用redis-cache，不再使用这个了
   Author :       Administrator
   date：          2019/4/22 0022
-------------------------------------------------
   Change Activity:
                   2019/4/22 0022:
-------------------------------------------------
"""
cache = SimpleCache()


def cached(expire=3600, key='view_{}'):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = key.format(request.path)
            value = cache.get(cache_key)

            if value is None:
                value = func(*args, **kwargs)
                cache.set(cache_key, value, timeout=expire)
            return value

        return wrapper

    return decorator


def time_func(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        now = time.time()

        value = func(*args, **kwargs)

        print('time:{}'.format(time.time() - now))
        return value

    return wrapper


@time_func
def test(val=30000):
    for i in range(1, val):
        print(i)


if __name__ == '__main__':
    test(40000)
    # test()
