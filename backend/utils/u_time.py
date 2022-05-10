# -*- coding:utf-8 -*-
# @Author: wzy
# @Time: 2020/11/25 14:17
__all__ = ["UTC", "CNZ", "utc2cn"]

from datetime import timezone, timedelta, datetime

# UTC时间
UTC = timezone.utc
# 北京时间
CNZ = timezone(timedelta(hours=8))


# 协调世界时间（UTC）转 北京时间
def utc2cn(_datetime: datetime):
    return _datetime.replace(tzinfo=UTC).astimezone(CNZ)
