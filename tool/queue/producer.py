# -*- coding: UTF-8 -*-
import redis
import json
from common.core.mongodb.mongo import MongoDb
from common.core.query.sub_meter import SubMeterQuery
import datetime


# redis池
# connect = redis.ConnectionPool(
#     host="192.168.2.16",
#     port=6379,
#     db=0,
#     max_connections=10,
#     password="5tG9!kL3",
#     decode_responses=True,
# )
connect = redis.ConnectionPool(
    host="127.0.0.1",
    port=6379,
    db=0,
    max_connections=10,
    decode_responses=True,
)
redis_client = redis.Redis(connection_pool=connect)


def create_redis_data():
    params = {
        'sign': 'sign',
        'action': 'action',
        'scrapy_sub_task_id': 'scrapy_sub_task_id',
        'timestamp': 'timestamp',
        'custom': 'custom',
    }
    detail = {
        'type': '1',
        'url': 'url',
        'params': params,
        'headers': {'Content-Type': 'application/json'},
        'verify': False
    }
    print(detail)
    redis_client.lpush('adv_scrapy', json.dumps(detail))


def create_redis_data_1():
    """
    关闭线路数据伪造
    """
    url = 'http://192.168.2.113/api/vpn/networkLine/closeLine'
    headers = {
            'content-type': 'application/json',
            'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0eXBlIjoib3RoZXIiLCJ1c2VyX2lkIjoxMDAyNDksInVzZXJuYW1lIjoicm9vdCIsImNvbXB1dGVyX25hbWUiOiJ1YnVudHUtYWR2LTg3IiwiY3JlYXRlX3RpbWUiOjE3MTg1ODYyNzEsImV4cGlyZWQiOjI1OTIwMDB9.sHt-oJHgo_1HDwhXhray0D2U1N4wnZlJd6KknCMpUlk'
        }
    params = {'network_line_use_id': 17506502}
    detail = {
        'type': 1,
        'url': url,
        'params': params,
        'headers': headers,
        'verify': False
    }
    redis_client.lpush('adv_scrapy', json.dumps(detail))


def create_redis_data_2():
    """
    关闭线路数据伪造
    """
    url = 'https://192.168.2.216/api/scrapy/advertising/retryTask'
    headers = {
            'content-type': 'application/json',
        }
    params = {'scrapy_sub_task_id': '663f326660667e55da1156fd', 'start_date_time': 1719814205.3135686, 'timestamp': 1719814229.8406408, 'sign': '550df02bcd9d6bffb6f948889809a135'}
    detail = {
        'type': 2,
        'url': url,
        'params': params,
        'headers': headers,
        'verify': False
    }
    redis_client.lpush('adv_scrapy', json.dumps(detail))


def create_redis_data_3():
    """
    关闭线路数据伪造
    """
    url = 'https://192.168.2.216/api/scrapy/advertising/callback'
    headers = {
            'content-type': 'application/json',
        }
    params = {'action': 'error', 'scrapy_sub_task_id': '663f326660667e55da1156fd', 'timestamp': 1719814230.6377912, 'custom': '{}', 'sign': '7f298dcd7511291010a76b79411f6ce4'}
    detail = {
        'type': 3,
        'url': url,
        'params': params,
        'headers': headers,
        'verify': False
    }
    redis_client.lpush('adv_scrapy', json.dumps(detail))


def create_redis_data_4():
    """
    关闭线路数据伪造
    """
    url = 'http://192.168.2.216/api/vpn/networkLine/getVpn'
    headers = {
            'content-type': 'application/json',
            'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0eXBlIjoib3RoZXIiLCJ1c2VyX2lkIjoxMDAyNDksInVzZXJuYW1lIjoicm9vdCIsImNvbXB1dGVyX25hbWUiOiJ1YnVudHUtYWR2LTg3IiwiY3JlYXRlX3RpbWUiOjE3MTg1ODYyNzEsImV4cGlyZWQiOjI1OTIwMDB9.sHt-oJHgo_1HDwhXhray0D2U1N4wnZlJd6KknCMpUlk'
        }
    params = {'network_line_id': 272, "type": 1}
    detail = {
        'type': 4,
        'url': url,
        'params': params,
        'headers': headers,
        'verify': False
    }
    redis_client.lpush('adv_scrapy', json.dumps(detail))


def push_spider_test():
    """
    测试scrapy-redis 分布式爬虫的任务投递
    """
    result = MongoDb.sub_table('scrapy_sub_task', SubMeterQuery.CYCLE_YEARLY).find(
        {"created_at": {"$gte": datetime.datetime(2024, 7, 9, 0, 0)}, "platform": 1, 'country_code': 'US'},
        # 'country_code': 'US'  "platform": 1, 'keyword': 'dyson charger',
    )
    tag = 0
    for data in result:
        tag += 1
        try:
            scrapy_sub_task_id = str(data['_id'])
            redis_client.lpush('adv_spider:start_urls', scrapy_sub_task_id)

            if tag > 100:
                break
        except:
            import traceback
            traceback.print_exc()
            pass


if __name__ == '__main__':
    # create_redis_data_1()
    # create_redis_data_2()
    # create_redis_data_3()
    # create_redis_data_4()
    push_spider_test()
