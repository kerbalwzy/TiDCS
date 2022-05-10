# -*- coding:utf-8 -*-
# @Author: wzy
# @Time: 2021/7/20
# 关于Worker相关信息的接口

from flask import jsonify

from backend.http_apis import httpApi
from backend.vars import ChromeExtWorkerPool


@httpApi.route("/workers", methods=["GET"], endpoint="获取在线的插件客户端信息")
def online_workers():
    workers = ChromeExtWorkerPool.values()
    data = [item.status() for item in workers]
    return jsonify(data)
