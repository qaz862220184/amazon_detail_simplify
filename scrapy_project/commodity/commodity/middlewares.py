# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

# from scrapy import signals
# useful for handling different item types with a single interface
from tool.request.cookies.change_address import AmazonLocationSession
from tool.request.proxys.vps_proxies import VpsProxiesTactic
from scrapy.utils.project import get_project_settings
from common.core.downloader.headers.request_headers import RefererParam
from common.exceptions.exception import RequestException, CookieException
from common.core.downloader.scrapy_pyppeteer import PyppeteerCookiesMiddleware
from common.base.scrapy_base import CommoditySpiderBase
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from tool.response.verify_response import VerifyResponse
import nest_asyncio
nest_asyncio.apply()


class CommodityProxyMiddleware:
    """
    代理中间件
    """
    def __init__(self):
        settings = get_project_settings()
        self.node_id = settings["NODE_ID"]
        self.count = settings["SWITCHING_FREQUENCY"]
        self.network_business_id = settings['BUSINESS_ID']

    def process_request(self, request, spider):
        country_code = spider.subtask_handle_data.get('country_code')
        area_type = spider.subtask_handle_data.get('area_type')

        # 获取的道道来历线路id
        result = VpsProxiesTactic.change_vpn_line(self.network_business_id, country_code, area_type)
        network_line_id = result.get('network_line_id')
        spider.network_line_id = network_line_id
        request.meta.update({"network_line_id": network_line_id})
        uuid = result.get('uuid')
        spider.uuid = uuid
        # VPN代理切换方式
        VpsProxiesTactic.change_vpn(self.count, network_line_id)
        # cookie 使用线路id和邮编进行区分
        zip_code = spider.subtask_handle_data.get('zip_code')
        cookie_name = str(network_line_id) + '_' + str(zip_code)
        request.meta.update({"current": cookie_name})
        # TODO 在这里调用请求端口的方法
        proxies = VpsProxiesTactic.get_line_proxies(network_line_id)
        request.meta.update({"proxies": proxies})


class CommodityRefererMiddleware(object):
    """
    referer 中间件
    """
    def process_request(self, request, spider):
        country = spider.subtask_handle_data.get('country_code')
        keyword = spider.subtask_handle_data.get('asin')
        referer = RefererParam.get_referer(country, keyword)
        request.meta.update({'referer': referer})


class CommodityCookiesMiddleware(PyppeteerCookiesMiddleware):
    """
    cookie 中间件
    """

    def init_cookies(self, request, spider, storage):
        if isinstance(spider, CommoditySpiderBase):
            proxies = request.meta.get('proxies')
            amazon = AmazonLocationSession(
                domain=spider.get_country_site(),
                zip_code=spider.subtask_handle_data.get('zip_code'),
                language=spider.get_language(),
                chrome_executable_path=self.settings.get('CHROME_SERVER_EXECUTE_PATH'),
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
                storage=storage,
                request=request
            )


class CommodityRetryMiddleware(RetryMiddleware):

    def __init__(self, settings):
        super().__init__(settings)
        self.settings = settings
        self.node_id = settings["NODE_ID"]
        self.count = settings["SWITCHING_FREQUENCY"]

    def process_response(self, request, response, spider):
        """
        响应中间件
        """
        if request.meta.get("dont_retry", False):
            return response

        # 线路id
        network_line_id = request.meta.get("network_line_id")

        # 响应内容验证对象
        verify_response = VerifyResponse(
            response=response
        )

        if verify_response.status != 200:
            # 亚马逊返回请求状态错误
            VpsProxiesTactic.lock_to_change_vpn(network_line_id=network_line_id, change_type=2)
            if verify_response.status == 404:
                raise RequestException(f'The listing is not exist')
            raise RequestException(f'Request status code is error [{response.status}]')

        if verify_response.is_dog_page() or verify_response.is_validate_captcha():
            # 出现狗页面 或者 出现验证码页面
            VpsProxiesTactic.lock_to_change_vpn(network_line_id=network_line_id, change_type=2)
            raise RequestException(f'Trigger the anti-claw mechanism')

        # 判断是否为listing不存在的页面
        if verify_response.is_not_listing():
            # listing 不存在
            raise RequestException(f'The listing is not exist')

        if verify_response.is_error_page() or verify_response.is_blank_page():
            # 页面错误【浏览器无响应导致无内容 或 浏览器超时 或 空白页面】
            VpsProxiesTactic.lock_to_change_vpn(network_line_id=network_line_id, change_type=2)
            raise RequestException('the page response is error!')

        # 判断地址是否存在 subtask_handle_data
        if verify_response.is_not_address(spider.subtask_handle_data.get('country_code'),
                                          spider.subtask_handle_data.get('zip_code')):
            PyppeteerCookiesMiddleware.delete_cookies(
                cookies={},
                storage=request.meta['cookieStorageObj'],
            )
            raise CookieException('The address is lose, proxy is {}'.format(request.meta['current']),
                                  error_type='address')

        return response

    def process_exception(self, request, exception, spider):
        """
        异常捕获
        """
        spider.add_exception(str(exception), type='system')
        if (
            isinstance(exception, self.EXCEPTIONS_TO_RETRY) and not request.meta.get('dont_retry', False)
        ):
            return self._retry(request, exception, spider)
