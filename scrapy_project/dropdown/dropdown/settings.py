# Scrapy settings for dropdown project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "dropdown"

SPIDER_MODULES = ["dropdown.spiders"]
NEWSPIDER_MODULE = "dropdown.spiders"


# �л�·������Ŀ¼
import sys
sys.path.append("../")
sys.path.append("../..")
from common.helpers import get_absolute_path
from common.env import ENV

# �ڵ�id
NODE_ID = ENV.find_env('NODE_ID')
# from common.helpers import get_absolute_path

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = "dropdown (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 6

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = True
COOKIES_ENABLE = True
COOKIES_PERSISTENCE_DIR = get_absolute_path('runtime/cookies')
# COOKIES_ENABLED = True
# COOKIES_DEBUG = True
# COOKIES_PERSISTENCE = True
# COOKIES_PERSISTENCE_DIR = 'cookies'
# COOKIES_STORAGE = 'common.core.downloader.cookies.storage.in_memory.InMemoryStorage'

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    "dropdown.middlewares.DropdownSpiderMiddleware": 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html

RETRY_ENABLED = True
RETRY_TIMES = 2
RETRY_HTTP_CODES = [404, 500, 502, 403, 503, 400]
DOWNLOADER_MIDDLEWARES = {
    # ��Ҫȡ��ϵͳ�����м�����������Զ����ͻ��Ҳ��������ֻ��ѡһ��
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,

    # �Զ����м��
    'dropdown.middlewares.DropdownProxyMiddleware': 97,
    'dropdown.middlewares.DropdownCookiesMiddleware': 99,
    'dropdown.middlewares.DropdownRetryMiddleware': 100,
    'dropdown.middlewares.DropdownSocks5Middleware': 101,

}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   "dropdown.pipelines.DropdownPipeline": 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# # ���������
# CHROME_SERVER_EXECUTE_PATH = '/usr/bin/google-chrome'
# CHROME_SERVER_PORT_RANGE = '5869-5899'
# CHROME_SERVER_USER_DIR = get_absolute_path('runtime/ChromeUserData')
# CHROME_SERVER_OPTIONS = []  # '--headless'
# # ������أ����ٴ���ִ�н���2������
# CHROME_SERVER_MAX_POOL_COUNT = 8
#
# # pyppeteer ����
# PYPPETEER_DRIVER_NAME = 'chrome'
# GERAPY_PYPPETEER_HEADLESS = False
# GERAPY_PYPPETEER_DUMPIO = True
# GERAPY_PYPPETEER_AUTO_CLOSE = False
# GERAPY_PYPPETEER_EXECUTABLE_PATH = '/usr/bin/google-chrome'

# ע����Ȩ�û�
from common.utils.jhvps.vpn_proxy_api import AuthAccount, VpsLineInit
AuthAccount().do_auth_account()
# ��ʼ��vps��·
BUSINESS_ID = 1
COUNTRY = None
VpsLineInit.line_init(
    business_id=BUSINESS_ID,
    country=COUNTRY,
)
