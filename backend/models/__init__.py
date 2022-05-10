# -*- coding:utf-8 -*-
# @Author: wzy
# @Time: 2021/7/20
# ORM
__all__ = ["db", "BaseModel", "init_db"]

from copy import deepcopy
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, DateTime, String, TEXT, Integer
from sqlalchemy.orm.attributes import flag_modified

from backend.utils.u_time import utc2cn

db = SQLAlchemy()


class BaseModel(db.Model):
    __abstract__ = True
    createTime = Column(DateTime, default=datetime.utcnow)
    updateTime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleteTime = Column(DateTime, default=None)

    @property
    def create_time_cn(self):
        return utc2cn(self.createTime).strftime("%Y-%m-%d %H:%M:%S") if self.createTime else ""

    @property
    def update_time_cn(self):
        return utc2cn(self.updateTime).strftime("%Y-%m-%d %H:%M:%S") if self.updateTime else ""

    @property
    def delete_time_cn(self):
        return utc2cn(self.deleteTime).strftime("%Y-%m-%d %H:%M:%S") if self.deleteTime else ""

    @classmethod
    def un_delete_query(cls):
        return cls.query.filter(cls.deleteTime.is_(None))

    def update_self(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
            if isinstance(v, list) or isinstance(v, dict):
                flag_modified(self, k)
        return self

    def to_dict(self):
        item = deepcopy(self.__dict__)
        item.pop("_sa_instance_state", None)
        item["createTime"] = self.create_time_cn
        item["updateTime"] = self.update_time_cn
        item["deleteTime"] = self.delete_time_cn
        return item


class Product(BaseModel):
    __tablename__ = "product"

    code = Column(String, primary_key=True, doc="产品型号")
    desc = Column(TEXT, doc="产品描述")
    price = Column(String, doc="产品单价")
    currency = Column(String, doc="价格币种")
    baseQty = Column(String, doc="基本单位")
    orderLimit = Column(Integer, doc="限购数量")
    inventory = Column(Integer, doc="库存数量")
    wantLimit = Column(Integer, doc="抢购上限，自定义")


def init_db(app):
    db.init_app(app)
