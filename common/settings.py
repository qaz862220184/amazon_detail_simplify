import pymysql
from urllib import parse
from common.helpers import get_absolute_path
# mysqldb
DB_MYSQL_CONF = {
   "default": {
       "host": "localhost",
       "user": "root",
       "passwd": "",
       "db": "amz_",
       "charset": "utf8mb4",
       "port": 3306,  # 58699
       "prefix": 'jh_',
       "cursor_class": pymysql.cursors.DictCursor,
   },
}

# mongodbpython
DB_MONGODB_CONF = {
    "default": {
        "uri": "mongodb://localhost:27017",
        "database": "common_service",
        "prefix": 'jh_',
    },
    "task": {
                "uri": "mongodb://localhost:27017",
                "database": "common_service",
                "prefix": 'jh_',
            },
    "brand": {
                "uri": "mongodb://localhost:27017",
                "database": "general_scraper",
                "prefix": 'jh_',
            },
}

# redisdb
DB_REDIS_CONF = {
    "default": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "max_connections": 10,
        "password": "",
        "connection_kwargs": {
            "decode_responses": True,
        },
    },
    "client": {
        "host": "localhost",
        "port": 6379,
        "db": 1,
        "max_connections": 10,
        "password": "",
        "connection_kwargs": {
            "decode_responses": True,
        },
    }
}

# cache
CACHE_CONF = {
    "driver": 'redis',
    "prefix": 'scrapy_cache',
}

# 页面解析出错保存的页面路径
SPIDER_PAGE_DIR = get_absolute_path('runtime/page')
