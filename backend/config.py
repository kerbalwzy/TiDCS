# -*- coding:utf-8 -*-
# @Author: wzy
# 配置类
__all__ = ["Config"]

import os


class Config:
    DEBUG = os.environ.get("DEBUG", True)
    # 目录路径相关配置项
    PROJECT_DIR = os.path.dirname(__file__)
    STATIC_DIR = os.path.join(PROJECT_DIR, "data/")
    # 加密相关配置
    SECRET_KEY = os.environ.get("SECRET_KEY", "a8i21e#$RSD12")
    # MySQL相关配置项
    # 默认数据库连接
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://tidcs:tidcs123@127.0.0.1:3306/tidcs?charset=utf8mb4"
    SQLALCHEMY_POOL_RECYCLE = 60 * 30
    SQLALCHEMY_POOL_SIZE = 100
    SQLALCHEMY_MAX_OVERFLOW = 500
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    # 跨域相关配置
    CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "*")
    # 日志相关配置
    LOG_FORMAT = "%(asctime)s %(levelname)0.4s %(filename)s:%(lineno)d %(message)s"
    LOG_LEVEL = "DEBUG" if DEBUG else "INFO"
    LOG_HANDLERS = ["FILE"]
    LOG_FILE_PATH = os.path.join(PROJECT_DIR, "logs/log.txt")
    LOG_FILE_SIZE = 1204 * 1024 * 10
    LOG_FILE_BACK_COUNT = 10
    LOG_SCREEN_SHOT_DIR = os.path.join(PROJECT_DIR, "logs/screen_shot")

    # httpApi免登录请求路径
    LOGIN_WHITE_PATH = [
        "/tidcs/login"
    ]
