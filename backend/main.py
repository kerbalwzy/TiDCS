# -*- coding:utf-8 -*-
# @Author: wzy
# @Time: 2021/5/15
#
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import app, socket_io, init_socket_io

# 初始化插件与中间件
from logs import init_logger
from models import init_db

init_db(app)
init_logger(app)
init_socket_io()


# TODO 请勿使用多进程启动！！！！！
def run(debug: bool = True):
    socket_io.run(app=app, host="0.0.0.0", port=43998, debug=debug)


if __name__ == '__main__':
    run()
