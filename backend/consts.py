# -*- coding=utf-8 -*-
# @Author: wzy
# @Time: 2022/5/10
# 全局使用的变量在此处声明，请勿使用多进程模式开启进程

ChromeExtWorkerPool = dict()  # {<str>:<ChromeExtWorker>}
SidNetDelayLastPintAt = dict()  # {<str>:<float>}

Users = {
    # 账号 : 密码
    "test": "123123",
}


class RespCode:
    UserNotFound = 40401
    ProductNotFound = 40402

    PasswordError = 40001
    ParamsError = 40002

    JwtInvalid = 40301


if __name__ == '__main__':
    pass
