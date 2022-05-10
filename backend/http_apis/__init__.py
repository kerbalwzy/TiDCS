# -*- coding:utf-8 -*-
# @Author: wzy
# @Time: 2021/7/20
#
from flask import Blueprint

httpApi = Blueprint("httpApi", __name__, url_prefix='/tidcs')

from .workers import *
from .tasks import *


