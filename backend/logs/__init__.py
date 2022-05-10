# -*- coding:utf-8 -*-
# @Author: wzy
# @Time: 2021/7/20
# 日志配置初始化函数
__all__ = ["init_logger"]

import logging
from logging.handlers import RotatingFileHandler


def init_logger(app):
    formatter = logging.Formatter(
        fmt=app.config.get("LOG_FORMAT", "%(asctime)s %(levelname)0.4s %(filename)s:%(lineno)d %(message)s"),
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logging.basicConfig(
        level=app.config.get("LOG_LEVEL", "DEBUG"),
        format=app.config.get("LOG_FORMAT", "%(asctime)s %(levelname)0.4s %(filename)s:%(lineno)d %(message)s"),
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger()

    for handler_kind in app.config.get("LOG_HANDLERS", []):
        if handler_kind == "FILE":
            _log_file_path = app.config.get("LOG_FILE_PATH")
            assert _log_file_path is not None, ValueError("保存文件日志必须配置日志文件夹路径: LOG_FILE_PATH")
            _handler = RotatingFileHandler(filename=_log_file_path,
                                           maxBytes=app.config.get("LOG_FILE_SIZE", 1024 * 1024 * 10),
                                           backupCount=app.config.get("LOG_FILE_BACK_COUNT", 10),
                                           encoding='utf-8')
            _handler.setFormatter(formatter)
            logger.handlers.append(_handler)
    app.logger = logger
