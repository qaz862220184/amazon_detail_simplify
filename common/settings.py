import pymysql
from urllib import parse
from common.helpers import get_absolute_path
from common.env import ENV
# mysqldb
DB_MYSQL_CONF = {
   "default": {
       # "host": "localhost",
       "host": "192.168.2.153",  # 183.90.82.115
       "user": "networkline",  # networkline
       "passwd": "btV3%^ts",  # btV3%^ts
       "db": "networkline",
       "charset": "utf8mb4",
       "port": 58699,  # 58699
       "prefix": 'jh_',
       "cursor_class": pymysql.cursors.DictCursor,
   },
}

# mongodbpython
DB_MONGODB_CONF = {
    # 线上
    "default": {
            "uri": "mongodb://common_service:{}@192.168.2.48:27017/?authMechanism=DEFAULT&authSource=common_service".format(parse.quote("juhui-common-service@juhui.com")),
            "database": "common_service",
            "prefix": 'jh_',
        },
    "task": {
            "uri": "mongodb://common_service:{}@192.168.2.48:27017/?authMechanism=DEFAULT&authSource=common_service".format(parse.quote("juhui-common-service@juhui.com")),
            "database": "common_service",
            "prefix": 'jh_',
        },
    "brand": {
            "uri": "mongodb://general_scraper:juhui-general-scraper.com@192.168.2.48:27017/?authMechanism=DEFAULT&authSource=general_scraper",
            "database": "general_scraper",
            "prefix": 'jh_',
        },
    # 本地
    # "default": {
    #     "uri": "mongodb://192.168.13.211:27017",
    #     "database": "common_service",
    #     "prefix": 'jh_',
    # },
    # "task": {
    #             "uri": "mongodb://192.168.13.211:27017",
    #             "database": "common_service",
    #             "prefix": 'jh_',
    #         },
    # "brand": {
    #             "uri": "mongodb://192.168.13.211:27017",
    #             "database": "general_scraper",
    #             "prefix": 'jh_',
    #         },
}

# redisdb
DB_REDIS_CONF = {
    "default": {
        "host": "127.0.0.1",
        "port": 6379,
        "db": 0,
        "max_connections": 10,
        "password": "",
        "connection_kwargs": {
            "decode_responses": True,
        },
    },
    "client": {
        "host": "192.168.2.16",
        "port": 6379,
        "db": 0,
        "max_connections": 10,
        "password": "5tG9!kL3",
        "connection_kwargs": {
            "decode_responses": True,
        },
    }
}

# cache
CACHE_CONF = {
    "driver": 'redis',
    "prefix": 'juhui_scrapy_cache',
}

# message
MESSAGE_CONF = {
    # 接口地址
    "api": 'http://192.168.2.50:9501/api/v1',
    # "api":'http://127.0.0.1:9501/api/v1',
    # 接口秘钥
    'apikey': 'hEI/qDhna7kL400WgZ91vDCPsbCPWCLLDwvxNrClmQg=',
    # 发送类型，分为：user（用户）、group（分组）
    "default_send_type": 'user',
    # 默认发送的用户id【多个请用英文逗号隔开】
    "default_user_id": '124',
    # 默认发送的分组id
    "default_group_id": '12',
    # 默认消息来源：1=运营系统,2=进销存
    "default_source": '1',
    # 默认发送者id
    "default_sender_id": '7',
}

# api
API_CONF = {
    # 接口秘钥
    'apikey': 'hEI/qDhna7kL400WgZ91vDCPsbCPWCLLDwvxNrClmQg=',
}

# 爬虫接口回调
CRAWL_RESULT_CALL_CONF = {
    # 测试环境
    '1': {
        'enable': True,
        'api': 'https://192.168.2.216/api/scrapy/crontab_task/callback',
    },
    # 正式环境
    '0': {
        'enable': True,
        'api': 'https://192.168.2.216/api/scrapy/crontab_task/callback',
    },
}


PROXY_POOL = {
    'api': 'http://192.168.2.204:5010',
}

REMOTE_FILE = {
    'api': 'http://192.168.2.47:92',
    'username': 'scrapy',
    'password': 'scrapy2023',
}

# 巡查频率
PATROL_FREQUENCY_CONFIG = {
    'api': 'https://192.168.2.216'
}

# 页面解析出错保存的页面路径
SPIDER_PAGE_DIR = get_absolute_path('runtime/page')
# VPN线路接口
VPN_LINE_PROXY = {
    'user_authentication_api': 'http://192.168.2.216/api/vpn/auth/authByUserClient',
    'program_authentication_api': 'http://192.168.2.216/api/vpn/auth/authByOtherClient',
    'get_all_line_api': 'http://192.168.2.216/api/vpn/networkLine/getAllLine',
    'change_line_api': 'http://192.168.2.216/api/vpn/networkLine/switchLine',
    'close_line_api': 'http://192.168.2.216/api/vpn/networkLine/closeLine',
    'get_vpn_api': 'http://192.168.2.216/api/vpn/networkLine/getVpn',
    'change_vpn_api': 'http://192.168.2.216/api/vpn/networkLine/switchVpn',
    'register_auth_api': 'http://192.168.2.216/api/vpn/auth/registerByOtherClient',
    'startup_cleaning_api': 'http://192.168.2.216/api/vpn/networkLine/startupCleaning',
}
# 代理中台地址
CENTRES = {
    'address': 'socks5://192.168.2.84',
    'api': 'http://192.168.2.84:8080/networkLine/server/getPort',
}
