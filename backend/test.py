# from utils.u_telegram import tg_bot_send_text
#
# tg_bot_send_text("测试消息")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from config import Config
from models import Product

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
session = sessionmaker(bind=engine)()

res = session.query(Product).all()
print(len(res))
