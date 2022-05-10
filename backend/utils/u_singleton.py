# -*- coding:utf-8 -*-
# @Author: wzy
# @Time: 2020-9-22 09:35:57
# 线程安全单例模式类装饰器
__all__ = ["singleton_cls", "synchronized"]

import threading
from functools import wraps


# 线程安全函数装饰器
def synchronized(func):
    """
    Usage:
        @synchronized
        def test(*args, **kwargs):
            pass
    """
    func.__lock__ = threading.Lock()

    @wraps(func)
    def synced_func(*args, **kws):
        with func.__lock__:
            return func(*args, **kws)

    return synced_func


# 线程安全单例类装饰器
def singleton_cls(cls):
    """
    Usage:

    @singleton_cls
    class Test:
        pass

    """
    instances = {}

    @wraps(cls)
    @synchronized
    def get_instance(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        print(cls)
        instance = instances[cls]
        print(id(instance))
        return instance

    return get_instance


if __name__ == '__main__':
    pass
