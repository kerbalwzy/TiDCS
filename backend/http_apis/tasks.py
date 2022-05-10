# -*- coding:utf-8 -*-
# @Author: wzy
# @Time: 2021/7/22
# 创建任务的相关接口

from flask_restful import reqparse, inputs

task_base_parser = reqparse.RequestParser(trim=True)
task_base_parser.add_argument("seller_id", type=str, required=True, location="json")
task_base_parser.add_argument("callback_url", type=inputs.url, location="json")
