# -*- coding:utf-8 -*-
# @Author: wzy
# @Time: 2021/7/20
# 核心模块, 用户创建Flask App对象和Flask-SocketIo App对象, 并完成一些基本功能
__all__ = ["app", "socket_io", "init_socket_io", "ChromeExtWorker", "TaskBase"]

import gc
import time
import uuid
from datetime import datetime

from flask import Flask, current_app, request
from flask_socketio import SocketIO, emit

from backend.http_apis import httpApi
from backend.utils.u_time import utc2cn
from backend.vars import ChromeExtWorkerPool, SidNetDelayLastPintAt
from config import Config
from utils.u_singleton import synchronized

#
app = Flask(import_name=__name__)
app.config.from_object(Config)
app.register_blueprint(httpApi)
#
socket_io = SocketIO(app, cors_allowed_origins=Config.CORS_ALLOWED_ORIGINS)


def ping():
    while True:
        for sid in ChromeExtWorkerPool.keys():
            socket_io.emit("ping", to=sid)
            SidNetDelayLastPintAt[sid] = datetime.now().timestamp()
        socket_io.sleep(5)


def clear_expire_task():
    while True:
        expire_tasks = list()
        for worker in ChromeExtWorkerPool.values():
            for task in worker.tasks_pool.values():
                if int(time.time()) - task.start_at > 3600:
                    expire_tasks.append(task)
        for task in expire_tasks:
            task.ext_worker.do(command="task_finish", task_id=task.task_id)
            task.ext_worker.tasks_pool.pop(task.task_id, None)  #
            task.ext_worker = None
            del task
        # 调用垃圾回收
        gc.collect()
        socket_io.sleep(1800)


# 常驻后台的Ping事件
socket_io.start_background_task(ping)
# 常驻后台的内存回收事件
socket_io.start_background_task(clear_expire_task)


def init_socket_io():
    @socket_io.event
    @synchronized
    def connect():
        current_app.logger.debug("New Connect, SID={}".format(request.sid))

    @socket_io.event
    def disconnect():
        current_app.logger.debug("Disconnect, SID={}".format(request.sid))
        worker = ChromeExtWorkerPool.pop(request.sid, None)
        if worker:
            # 清除worker存储的任务, 解除引用关系, 避免循环引用
            for item in worker.tasks_pool.values():
                item.finish()

    @socket_io.event
    def pong():
        # current_app.logger.debug("Ping-Pong SID={}".format(request.sid))
        now_timestamp = datetime.now().timestamp()
        net_delay = int((now_timestamp - SidNetDelayLastPintAt[request.sid]) * 1000)
        #
        worker = ChromeExtWorkerPool.get(request.sid, None)
        if worker:
            worker.net_delay = net_delay

    @socket_io.event
    def worker_online(params):
        """
        插件客户端Worker上线通知
        """
        # current_app.logger.debug(
        #     "Worker Online, SID={}\n{}".format(request.sid, json.dumps(params, indent=True))
        # )
        params["sid"] = request.sid
        #
        worker = ChromeExtWorkerPool.get(params["sid"], None)
        if not worker:
            worker = ChromeExtWorker(**params)
            ChromeExtWorkerPool[worker.sid] = worker
        else:
            worker.errmsg = ""
            worker.last_online_at = utc2cn(datetime.utcnow())
        #
        emit("online_ok", {"msg": "插件客户端注册Worker成功!"}, to=worker.sid)
        # current_app.logger.debug("Workers {}".format(ChromeExtWorkerPool))

    @socket_io.event
    def worker_offline(params):
        """
        插件客户端下线通知,
        """
        # current_app.logger.debug(
        #     "Worker Offline, SID={}\n{}".format(request.sid, json.dumps(params, indent=True))
        # )
        worker = ChromeExtWorkerPool.pop(request.sid, None)
        if worker:
            # 清除worker存储的任务, 解除引用关系, 避免循环引用
            for item in worker.tasks_pool.values():
                item.finish()

    @socket_io.event
    def update_cart(params):
        worker = ChromeExtWorkerPool.get(request.sid, None)
        if worker:
            worker.cart = params

    @socket_io.event
    def worker_callback(params):
        """
        插件客户端的callback数据
        """
        # current_app.logger.debug(
        #     "Worker Callback, SID={}\n{}".format(request.sid, json.dumps(params, indent=True))
        # )
        worker = ChromeExtWorkerPool.get(request.sid, None)
        if worker:
            worker.callback(task_id=params["task_id"], params=params)

    @socket_io.event
    def auto_login_fail(params):
        pass


class ChromeExtWorker:
    """
    映射Chrome插件[客户端], 并不对应唯一的Tab实例;
    一个ChromeExtWorker可能对应了多个真实的Tab实例;
    一个TiUserId对应一个ChromeExtWorker
    一个Sid对应一个ChromeExtWorker
    当发送任务到Chrome插件时, 由Chrome插件的Background自动随机选择某个具体的Tab实例执行任务;
    """

    EVENT_TASK_EXEC = "task_exec"

    def __init__(
            self, sid: str, email: str, company_name: str, errmsg: str = ""

    ):
        """
        sid socket-io连接的session-id
        ti_user_id  已经登录的账号ID
        company_name 账号公司名称
        """
        self.sid = sid
        self.email = email
        self.company_name = company_name
        self.last_online_at = utc2cn(datetime.utcnow())  # 最后在线时间
        self.errmsg = errmsg
        self.last_ping_at = 0  # 最后ping的时间戳
        self.net_delay = 0  # 网络延迟, 毫秒
        self.tasks_pool = dict()  # {<str>: <TaskBase+>}
        self.cart = {}

    def status(self):
        item = dict()
        item["sid"] = self.sid
        item["email"] = self.email
        item["companyName"] = self.company_name
        item["errmsg"] = self.errmsg
        item["lastOnlineAt"] = self.last_online_at.strftime("%Y-%m-%d %H:%M:%S")
        item["netDelay"] = self.net_delay
        item["cart"] = self.cart
        return item

    def tasks_status(self):
        data = list()
        for item in self.tasks_pool.values():
            data.append(item.status())
        return data

    def do(self, command: str, params: dict = None, task_id: str = None, monopoly: bool = False, event: str = None):
        event = event or self.EVENT_TASK_EXEC
        socket_io.emit(event,
                       {
                           "company_name": self.company_name,
                           "task_id": task_id,
                           "monopoly": monopoly,
                           "cmd": command,
                           "params": params,
                       },
                       to=self.sid)

    def callback(self, task_id, params):
        task = self.tasks_pool.get(task_id)
        if task:
            task.do_callback(params)


class TaskBase:
    """
    任务基类, 所有创建的业务任务都应该继承与整个基类
    """
    CUSTOM_STEP_SLEEP = 5  # 自定义的callback_sleep的睡眠时间,单位 秒

    def __init__(self, worker: ChromeExtWorker, monopoly: bool = False):
        self.task_id = str(uuid.uuid4())
        self.monopoly = monopoly  # 是否为独占式任务
        self.steps = []
        self.current_step = 0
        self.ext_worker = worker
        self.ext_worker.tasks_pool[self.task_id] = self
        self.start_at = int(time.time())

    def status(self):
        item = dict()
        item["task_class"] = str(self.__class__)
        item["task_id"] = self.task_id
        item["steps"] = self.steps
        item["current_step"] = self.current_step
        return item

    def add_step(self, command: str, params: dict, callback_func: str = "do_next"):
        """
        添加执行步骤的描述数据集
        command: 插件要执行的命令
        params: 执行参数
        callback_func: 步骤执行成功后的回调函数
        """
        params["callback_func"] = callback_func
        self.steps.append({
            "task_id": self.task_id, "monopoly": self.monopoly,
            "command": command, "params": params
        })

    def do_callback(self, params: dict):
        """
        执行任务的callback函数, 默认的callback函数为do_next,
        如果调用的callback函数不是do_next,则也会在回调函数执行成功后再执行do_next
        """
        try:
            if params.get("exec_error"):
                raise RuntimeError(params["exec_error"])
            # 默认的回调函数是执行下一步
            callback_func_name = params.get("callback_func", "do_next")
            callback_func = getattr(self, callback_func_name, None)
            if not callback_func:
                raise RuntimeError("{} callback调用的函数{}未找到, 无法正常执行".format(
                    self.__class__, callback_func_name)
                )
            if not callable(callback_func):
                raise RuntimeError("{} callback调用的函数{}不是一个callable对象, 无法正常执行".format(
                    self.__class__, callback_func_name)
                )
            # 执行指定的callback函数
            callback_func(params.get("callback_params", None))
            # current_app.logger.debug(params)
        except Exception as e:
            current_app.logger.error(e, exc_info=True)
            # TODO 可以在这里添加自定义的外部通知功能，建议异步执行
            self.finish()  # 出现步骤执行异常, 直接结束任务
        else:
            # 当回调函数不为do_next时, 需要在执行完回调函数后, 继续执行do_next方法以调用下一步操作
            if callback_func_name != "do_next":
                self.do_next()

    def finish(self):
        #  结束任务, 从worker中删除本任务, 并解除引用关系
        self.ext_worker.do(command="task_finish", task_id=self.task_id)
        self.ext_worker.tasks_pool.pop(self.task_id, None)  #
        self.ext_worker = None
        current_app.logger.debug("任务:{}-{} 结束".format(self.__class__.__name__, self.task_id))

    def do_next(self, *args, **kwargs):
        """
        执行任务的下一步
        """
        self.current_step += 1
        if self.current_step < len(self.steps) + 1:
            current_app.logger.debug("任务:{}-{} 执行第{}步".format(self.__class__.__name__, self.task_id, self.current_step))
            self.ext_worker.do(**self.steps[self.current_step - 1])
        else:
            self.finish()

    def run(self):
        """
        启动任务, 实际上就是指定任务的第一步
        """
        self.do_next()
