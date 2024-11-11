# Scrapy settings for commodity project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "commodity"

SPIDER_MODULES = ["commodity.spiders"]
NEWSPIDER_MODULE = "commodity.spiders"

# 节点id
import sys

sys.path.append('../')
sys.path.append('../../')
from common.env import ENV
NODE_ID = ENV.find_env('NODE_ID')

# 代理切换频率，每*次切换一次代理
SWITCHING_FREQUENCY = 300

# 切换路径到根目录
import sys
sys.path.append("../")
sys.path.append("../../")
from common.helpers import get_absolute_path

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "commodity (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = True
COOKIES_PERSISTENCE_DIR = get_absolute_path('runtime/cookies')

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "commodity.middlewares.CommoditySpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html

RETRY_ENABLED = True
RETRY_TIMES = 2
RETRY_HTTP_CODES = [500, 502, 403, 503, 400]
DOWNLOADER_MIDDLEWARES = {
    # 需要取消系统重试中间件，否则会和自定义冲突，也就是两个只能选一个
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,

    # 自定义中间件
    'commodity.middlewares.CommodityProxyMiddleware': 98,
    'common.core.downloader.scrapy_pyppeteer.ChromeServerMiddleware': 99,
    'commodity.middlewares.CommodityCookiesMiddleware': 100,
    'commodity.middlewares.CommodityRetryMiddleware': 101,
    'commodity.middlewares.CommodityRefererMiddleware': 102,
    # selenium中间件
    'common.core.downloader.scrapy_pyppeteer.NewPyppeteerMiddleware': 800,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   "commodity.pipelines.CommodityPipeline": 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# 浏览器服务
CHROME_SERVER_EXECUTE_PATH = '/usr/bin/google-chrome'
CHROME_SERVER_PORT_RANGE = '5869-5899'
CHROME_SERVER_USER_DIR = get_absolute_path('runtime/ChromeUserData')
CHROME_SERVER_OPTIONS = []  # '--headless'
# 最大服务池，至少大于执行进程2个以上
CHROME_SERVER_MAX_POOL_COUNT = 8

# pyppeteer 参数
PYPPETEER_DRIVER_NAME = 'chrome'
GERAPY_PYPPETEER_HEADLESS = False
GERAPY_PYPPETEER_DUMPIO = True
GERAPY_PYPPETEER_AUTO_CLOSE = False
GERAPY_PYPPETEER_EXECUTABLE_PATH = '/usr/bin/google-chrome'

# 注册授权用户
from common.utils.jhvps.vpn_proxy_api import AuthAccount, VpsLineInit
AuthAccount().do_auth_account()
# 初始化vps线路
BUSINESS_ID = 1
COUNTRY = None
VpsLineInit.line_init(
    business_id=BUSINESS_ID,
    country=COUNTRY,
)
