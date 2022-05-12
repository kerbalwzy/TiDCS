# -*- coding:utf-8 -*-
# @Author: wzy
# 核心模块, 用户创建Flask App对象和Flask-SocketIo App对象, 并完成一些基本功能
__all__ = ["app", "socket_io", "init_socket_io", "ChromeExtWorker"]

import gc
import math
import random
from datetime import datetime
from threading import Thread

from flask import Flask, current_app, request
from flask_socketio import SocketIO, emit
from sqlalchemy import or_

from backend.consts import ChromeExtWorkerPool, SidNetDelayLastPintAt
from backend.http_apis import httpApi
from backend.models import Product, db
from backend.utils.u_telegram import tg_bot_send_text
from backend.utils.u_time import utc2cn
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


# 定时自动垃圾回收
def clock_auto_gc():
    while True:
        # 调用垃圾回收, 每小时调用一次
        gc.collect()
        socket_io.sleep(3600)


# 平均随机分配任务
def random_dispatch_task(workers, tasks):
    res = {}
    while True:
        if len(tasks) == 0:
            break
        for item in workers:
            if len(tasks) == 0:
                break
            pop_index = random.randint(0, len(tasks) - 1)
            res.setdefault(item, []).append(tasks.pop(pop_index))
    return res


# 定时自动获取产品基本信息
def clock_spider_product_base():
    app.app_context().push()
    while True:
        db.session.commit()  # 需要显示commit以读取数据库的最新数据
        products = db.session.query(Product).filter(
            or_(Product.desc.is_(None), Product.desc == ""),
            Product.deleteTime.is_(None)
        ).all()
        # 平均随机分配给在线的各个客户端
        workers = ChromeExtWorkerPool.keys()
        all_tasks = [{"code": item.code} for item in products]
        if len(workers) == 0 or len(all_tasks) == 0:
            socket_io.sleep(25)  # 休眠
            continue
        current_app.logger.info(f"定时更新产品基本信息，需要更新的产品记录 {len(products)} 条")
        for sid, tasks in random_dispatch_task(workers=workers, tasks=all_tasks).items():
            for item in tasks:
                socket_io.emit("spider_product_base", item, to=sid)
                socket_io.sleep(1)
        # 休眠
        socket_io.sleep(25)


# 定时更新购物车信息
def clock_spider_ti_cart():
    while True:
        socket_io.emit("spider_cart")
        socket_io.sleep(10)


# 定时更新产品库存
def clock_spider_product_ivt():
    app.app_context().push()
    while True:
        db.session.commit()  # 需要显示commit以读取数据库的最新数据
        products = db.session.query(Product).filter(
            Product.orderLimit.isnot(None),
            Product.deleteTime.is_(None)
        ).all()
        workers = ChromeExtWorkerPool.keys()
        all_tasks = [item.code for item in products]
        if len(workers) == 0 or len(all_tasks) == 0:
            socket_io.sleep(10)  # 休眠
            continue
        current_app.logger.info(f"定时更新产品库存，需要更新的产品记录 {len(products)} 条")
        try:
            for sid, tasks in random_dispatch_task(workers=workers, tasks=all_tasks).items():
                # 每100条记录分配为一组任务
                group_limit = 500
                group_n = math.ceil(len(tasks) / group_limit)
                for i in range(group_n):
                    start = i * group_limit
                    end = (i + 1) * group_limit
                    group_tasks = tasks[start:end]
                    socket_io.emit("spider_product_ivt", {"codes": group_tasks}, to=sid)
                    socket_io.sleep(1)  # 休眠
        except Exception as e:
            current_app.logger.error(e)
        socket_io.sleep(10)  # 休眠


def init_socket_io():
    @socket_io.event
    @synchronized
    def connect():
        current_app.logger.debug("New Connect, SID={}".format(request.sid))

    @socket_io.event
    def disconnect():
        current_app.logger.debug("Disconnect, SID={}".format(request.sid))
        worker = ChromeExtWorkerPool.pop(request.sid, None)

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

    @socket_io.event
    def auto_login_fail(params):
        worker = ChromeExtWorkerPool.pop(request.sid, None)
        msg = f"Ti自动登录失败，账号:{worker.email}, 错误内容:{params['errmsg']}"
        current_app.logger.info(msg)
        #
        t = Thread(target=tg_bot_send_text, args=(f"{msg}, 请开发人员尽快排查问题",))
        t.setDaemon(True)
        t.start()

    @socket_io.event
    def update_cart(params):
        worker = ChromeExtWorkerPool.get(request.sid, None)
        if worker:
            worker.cart = params
            worker.last_online_at = utc2cn(datetime.utcnow())

    @socket_io.event
    def update_product_base(data):

        # 多线程更新数据
        def update_data(params):
            with app.app_context():
                product = db.session.query(Product).filter(Product.code == params["orderablePartNumber"]).first()
                if product:
                    product.desc = params["partDescription"]
                    product.price = params["price"]["basePrice"]
                    product.currency = params["price"]["currencyCode"]
                    product.baseQty = params["price"]["baseQty"]
                    product.orderLimit = params["orderLimit"]
                    db.session.add(product)
                try:
                    db.session.commit()
                except Exception as e:
                    current_app.logger.error(e)
                    db.session.rollback()

        t = Thread(target=update_data, args=(data,))
        t.setDaemon(True)
        t.start()

    @socket_io.event
    def update_product_ivt(data):
        if not data:
            return
        codes = []
        code2ivt = {}
        for k, v in data.items():
            codes.append(k)
            code2ivt[k] = v["currentInventory"]
        with app.app_context():
            products = db.session.query(Product).filter(
                Product.deleteTime.is_(None),
                Product.code.in_(codes)
            ).all()
            for item in products:
                item.inventory = code2ivt[item.code]
                item.updateTime = datetime.utcnow()
                db.session.add(item)
                # 尝试对有库存的，需要抢购的，并还未加入到过购物车的产品进行抢购操作
                if item.wantLimit > 0 and item.inventory > 0:
                    # 获取所有在线账号购物车内的产品
                    all_ti_cart_products = {}
                    for worker in ChromeExtWorkerPool.values():
                        ti_cart = worker.cart.get("Items") or []
                        for cart_products in ti_cart:
                            all_ti_cart_products[cart_products["OpnId"]] = True
                    if all_ti_cart_products.get(item.code):
                        # 购物车中已经存在的产品不重复抢购
                        current_app.logger.debug(f"跳过购物车已存在的产品记录:{item.code}")
                        continue
                    # 发起抢购任务
                    add_cart_count = item.wantLimit if item.wantLimit <= item.inventory else item.inventory
                    add_cart_count = add_cart_count if add_cart_count <= item.orderLimit else item.orderLimit
                    current_app.logger.debug(f"发起产品抢购任务:{item.code}")
                    socket_io.emit(
                        "ti_add_product2cart",
                        {"code": item.code, "quantity": add_cart_count, "currency": item.currency or "USD"},
                        to=request.sid,
                    )
            try:
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()

    @socket_io.event
    def add_product2cart_ok(data):
        worker = ChromeExtWorkerPool.pop(request.sid, None)
        msg = f"产品抢购成功，下单账号:{worker.email}, 产品型号:{data['code']}"
        current_app.logger.info(msg)
        #
        t = Thread(target=tg_bot_send_text, args=(f"{msg}, 请尽快进行后续的人工处理",))
        t.setDaemon(True)
        t.start()

    # 常驻后台的事件
    socket_io.start_background_task(ping)
    socket_io.start_background_task(clock_auto_gc)
    socket_io.start_background_task(clock_spider_product_base)
    socket_io.start_background_task(clock_spider_ti_cart)
    socket_io.start_background_task(clock_spider_product_ivt)


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
