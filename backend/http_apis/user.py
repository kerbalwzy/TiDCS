# -*- coding=utf-8 -*-
# @Author: wzy
# @Time: 2022/5/10
#
import jwt
from flask import current_app, g
from flask_restful import reqparse

from backend.consts import Users, RespCode
from backend.http_apis import httpApi, json_resp

login_param_parser = reqparse.RequestParser(trim=True)
login_param_parser.add_argument("account", type=str, required=True, location="json")
login_param_parser.add_argument("password", type=str, required=True, location="json")


@httpApi.route("/login", methods=["POST"], endpoint="用户登录")
def login():
    params = login_param_parser.parse_args()
    if not Users.get(params['account']):
        return json_resp(errcode=RespCode.UserNotFound, msg="用户不存在")
    if Users.get(params['account']) != params["password"]:
        return json_resp(errcode=RespCode.PasswordError, msg="密码错误")
    access_token = jwt.encode(payload={"account": params['account']},
                              key=current_app.config.get("SECRET_KEY")).decode('ascii')
    resp = json_resp(errcode=0, msg="success", data={
        "access_token": access_token, "account": params["account"]})
    resp.set_cookie('access_token', access_token, samesite="None", secure=True)
    return resp


@httpApi.route("/logout", methods=["GET"], endpoint="用户注销")
def logout():
    resp = json_resp(errcode=0, msg="success")
    resp.set_cookie("access_token", "")
    return resp


@httpApi.route("/profile", methods=["GET"], endpoint="获取用户信息")
def user_profile():
    return json_resp(errcode=0, msg="success", data={"account": g.user_account})


if __name__ == '__main__':
    pass
