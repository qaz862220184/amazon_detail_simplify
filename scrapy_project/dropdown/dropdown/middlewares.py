# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

# from scrapy import signals

# useful for handling different item types with a single interface
import requests
from tool.request.cookies.change_address import AmazonLocationSession
from common.exceptions.exception import RequestException, CookieException
from common.base.scrapy_base import CommoditySpiderBase
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from tool.response.verify_response import VerifyResponse
from scrapy.utils.project import get_project_settings
from tool.request.proxys.vps_proxies import VpsProxiesTactic
from common.core.downloader.cookies import BaseCookiesMiddleware
from scrapy.core.downloader.handlers.http import HTTPDownloadHandler
from scrapy.http import TextResponse as ScrapyResponse


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


class DropdownCookiesMiddleware(BaseCookiesMiddleware):
    """
    cookie 中间件
    """

    def init_cookies(self, request, spider):
        if isinstance(spider, CommoditySpiderBase):
            proxies = request.meta.get('proxies')
            amazon = AmazonLocationSession(
                country=spider.get_country('code'),
                zip_code=spider.subtask_handle_data.get('zip_code'),
                proxies=proxies,
            )
            cookies = amazon.change_address()
            if not cookies:
                network_line_id = request.meta.get("network_line_id")
                if network_line_id:
                    VpsProxiesTactic.change_vpn(0, network_line_id)
                raise CookieException('address is not change', error_type='address')
            self.send_cookies(
                cookies=cookies,
                request=request
            )


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


class DropdownSocks5Middleware(HTTPDownloadHandler):
    """
    将请求代理改成使用socks5
    """

    def process_request(self, request, spider):
        headers_dict = {k.decode(): v[0].decode() if v else '' for k, v in request.headers.items()}
        proxies = request.meta.get('proxy')
        proxies = {'https': proxies, 'http': proxies}
        response = requests.get(request.url, headers=headers_dict, proxies=proxies)
        response = ScrapyResponse(
            url=request.url,
            status=response.status_code,
            headers=request.headers,
            body=response.content,
            request=request,
        )

        return response
