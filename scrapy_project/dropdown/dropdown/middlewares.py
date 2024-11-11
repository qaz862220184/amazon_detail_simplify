# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

# from scrapy import signals

# useful for handling different item types with a single interface
from scrapy import signals
from common.core.downloader.cookies import ScrapyCookiesMiddleware
from common.exceptions.exception import RequestException
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from tool.response.verify_response import VerifyResponse
from scrapy.utils.project import get_project_settings
from tool.request.proxys.vps_proxies import VpsProxiesTactic


class DropdownProxyMiddleware:
    """
    代理中间件
    """
    def __init__(self):
        settings = get_project_settings()
        self.network_business_id = settings['BUSINESS_ID']

    def process_request(self, request, spider):
        country_code = spider.subtask_handle_data.get('country_code')
        area_type = spider.subtask.get('area_type')
        # 获取的道道来历线路id
        result = VpsProxiesTactic.change_vpn_line(self.network_business_id, country_code, area_type)
        network_line_id = result.get('network_line_id')
        spider.network_line_id = network_line_id
        request.meta.update({"network_line_id": network_line_id})
        uuid = result.get('uuid')
        spider.uuid = uuid

        request.meta.update({"current": str(network_line_id)})
        # TODO 在这里调用请求端口的方法
        proxies = VpsProxiesTactic.get_line_proxies(network_line_id)
        request.meta.update({"proxies": proxies})
        # request.meta['proxy'] = proxies


class DropdownCookiesMiddleware(ScrapyCookiesMiddleware):
    """
    cookie 中间件
    """
    # 必须的cookie
    must_cookie = []

    def init_cookies(self, request, spider):
        cookies = {}
        return cookies


class DropdownDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest

        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class DropdownRetryMiddleware(RetryMiddleware):

    def __init__(self, settings):
        super().__init__(settings)
        self.settings = settings

    def process_response(self, request, response, spider):
        """
        响应中间件
        """
        if request.meta.get("dont_retry", False):
            return response

        # 响应内容验证对象
        verify_response = VerifyResponse(
            response=response
        )

        if verify_response.status != 200:
            # 亚马逊返回请求状态错误
            # current_proxy = request.meta["current"]
            raise RequestException(f'Request status code is error [{response.status}]')

        if verify_response.is_dog_page() or verify_response.is_validate_captcha():
            # 出现狗页面 或者 出现验证码页面
            # current_proxy = request.meta["current"]
            raise RequestException(f'Trigger the anti-claw mechanism')

        return response

    def process_exception(self, request, exception, spider):
        """
        异常捕获
        """
        spider.add_exception(str(exception), type="system")
        if (
            isinstance(exception, self.EXCEPTIONS_TO_RETRY) and not request.meta.get("dont_retry", False)
        ):
            return self._retry(request, exception, spider)
