# -*- coding:utf-8 -*-
# @Author: wzy
#
from flask import Blueprint, Response, jsonify, make_response
from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook
from werkzeug.exceptions import HTTPException

httpApi = Blueprint("httpApi", __name__, url_prefix='/tidcs')


def json_resp(errcode: int, msg: str, data: object = None, status_code: int = 200, **kwargs) -> Response:
    """
    返回带特定HTTP状态码的Response对象， Content-Type默认为Application/json
    :param errcode: 自定义状态码
    :param msg: 结果描述信息
    :param data: 数据体
    :param status_code: http状态码
    :param kwargs, 更多不定长参数
    :return:
    """
    resp = jsonify(errcode=errcode, msg=msg, data=data, **kwargs)
    resp.status_code = status_code
    return resp


def excel_resp(wb: Workbook, filename: str) -> Response:
    data = save_virtual_workbook(wb)
    resp = make_response(data)
    resp.headers["Content-Type"] = "application/vnd.ms-excel"
    filename = filename.encode("utf-8").decode("latin1")
    resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return resp


# 加载跨域处理中间件， 为每个成功的响应头添加CORS-CONTROL的头部信息
@httpApi.after_request
def cors_header(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Max-Age"] = "86400"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "HEAD, GET, OPTIONS, POST, PUT, DELETE"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Content-Length, " \
                                                       "X-CSRF-Token,X-Requested-With, X-CustomHeader, Accept, " \
                                                       "Accept-Encoding, Accept-Language, Origin, Host," \
                                                       "Connection, DNT, Keep-Alive,User-Agent,If-Modified-Since," \
                                                       "Cache-Control, Pragma, access-token, Cookie, X-FileName"
    return response


# 加载JWT_TOKEN解析的中间件, 在每个请求前从cookie中获取access_token,并解析
@httpApi.before_request
def parser_jwt():
    # 除开跨域预检请求
    if request.method == 'OPTIONS' or request.method == "HEAD":
        return json_resp(errcode=0, msg="success")
    # 除开登录接口
    if request.path not in current_app.config.get("LOGIN_WHITE_PATH"):
        # 尝试从cookie或者header或者query_string中获取token字符串
        jwt_token = request.cookies.get("access_token") or \
                    request.headers.get("Access-Token") or \
                    request.args.get("access_token")
        if not jwt_token:
            return json_resp(errcode=RespCode.JwtInvalid, msg="JWT-Token-Invalid", status_code=403)
        try:
            payload = jwt.decode(jwt_token, current_app.config.get("SECRET_KEY"))
        except Exception:
            return json_resp(errcode=RespCode.JwtInvalid, msg="JWT-Token-Invalid", status_code=403)


# flask-restful参数验证异常处理
@httpApi.errorhandler(HTTPException)
def restful_params_validate_err(e):
    err_data = getattr(e, "data", False)
    err_msg = e.__str__()
    if err_data:
        err_msg_dict = err_data.get("message")
        err_msg = "\n".join(err_msg_dict.values())
    return json_resp(errcode=RespCode.ParamsError, msg=err_msg)


from .workers import *
from .products import *
from .auth import *
