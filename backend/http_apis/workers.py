# -*- coding:utf-8 -*-
# @Author: wzy
# 关于Worker相关信息的接口
from flask import jsonify
from flask_restful import reqparse

from backend.consts import ChromeExtWorkerPool
from backend.http_apis import httpApi, json_resp


@httpApi.route("/workers", methods=["GET"], endpoint="获取在线的插件客户端信息")
def online_workers():
    workers = ChromeExtWorkerPool.values()
    data = [item.status() for item in workers]
    return json_resp(errcode=0, msg="success", data=data)


get_cookies_parser = reqparse.RequestParser(trim=True)
get_cookies_parser.add_argument("email", type=str, location="args")


@httpApi.route("/cookies", methods=["GET"], endpoint="获取在线TI账号的Cookie信息")
def online_cookies():
    workers = ChromeExtWorkerPool.values()
    params = get_cookies_parser.parse_args()
    if params["email"]:
        data = {"email": params["email"]}
        for worker in workers:
            if worker.email == params["email"]:
                data["cookies_str"] = worker.status()["cookies_str"]
                data["cookies_list"] = worker.cookies
                return jsonify(data)
        return jsonify(data)
    else:
        data = list()
        for worker in workers:
            item = {
                "email": worker.email,
                "cookies_str": worker.status()["cookies_str"],
                "cookies_list": worker.cookies
            }
            data.append(item)
        return jsonify(data)
