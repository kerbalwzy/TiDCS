# -*- coding:utf-8 -*-
# @Author: wzy
# 关于Worker相关信息的接口

from backend.consts import ChromeExtWorkerPool
from backend.http_apis import httpApi, json_resp


@httpApi.route("/workers", methods=["GET"], endpoint="获取在线的插件客户端信息")
def online_workers():
    workers = ChromeExtWorkerPool.values()
    data = [item.status() for item in workers]
    return json_resp(errcode=0, msg="success", data=data)
