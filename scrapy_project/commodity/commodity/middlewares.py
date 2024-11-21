# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import logging
import random

import requests
from tool.request.cookies.change_address import AmazonLocationSession
from common.core.downloader.cookies import BaseCookiesMiddleware
from common.exceptions.exception import RequestException, CookieException
from common.core.downloader.headers.request_headers import RefererParam
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from tool.response.verify_response import VerifyResponse
from common.base.scrapy_base import CommoditySpiderBase
from scrapy.utils.project import get_project_settings
from scrapy.core.downloader.handlers.http import HTTPDownloadHandler
from scrapy.http import TextResponse as ScrapyResponse
from tool.request.proxys.vps_proxies import VpsProxiesTactic
from fake_useragent import UserAgent

logger = logging.getLogger()
ua = UserAgent()


class CommodityProxyMiddleware(object):
    """
    代理中间件
    """
    def __init__(self):
        settings = get_project_settings()
        self.network_business_id = settings['BUSINESS_ID']

    def process_request(self, request, spider):
        country_code = spider.subtask_handle_data.get('country_code')
        area_type = spider.subtask_handle_data.get('area_type')

        # 获取得到线路id
        result = VpsProxiesTactic.change_vpn_line(self.network_business_id, country_code, area_type)
        network_line_id = result.get('network_line_id')
        spider.network_line_id = network_line_id
        request.meta.update({"network_line_id": network_line_id})
        uuid = result.get('uuid')
        spider.uuid = uuid
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
        logger.debug('advertising.middlewares.AdvertisingRefererMiddleware is start!!!')
        country = spider.subtask_handle_data.get('country_code')
        keyword = spider.subtask_handle_data.get('asin')
        referer = RefererParam.get_referer(country, keyword)
        request.meta.update({'referer': referer})
        logger.debug('advertising.middlewares.AdvertisingRefererMiddleware is done!!!')


class CommodityCookiesMiddleware(BaseCookiesMiddleware):

    def init_cookies(self, request, spider):
        print('commodity.middlewares.CommodityCookiesMiddleware is start!!!')
        if isinstance(spider, CommoditySpiderBase):
            proxies = request.meta.get('proxies')
            proxies = {'http': proxies}
            amazon = AmazonLocationSession(
                country=spider.subtask_handle_data.get('country_code'),
                zip_code=spider.subtask_handle_data.get('zip_code'),
                proxies=proxies,
            )
            cookies = amazon.change_address()
            request.meta.update({'cookies_jar': amazon})
            if not cookies:
                raise CookieException('address is not change', error_type='address')
            self.send_cookies(
                cookies=cookies,
                request=request
            )
        print('commodity.middlewares.CommodityCookiesMiddleware is done!!!')


class CommodityHeadersMiddleware(object):
    """
    请求头中间件
    """

    def process_request(self, request, spider):
        logger.debug('Commodity.middlewares.CommodityHeadersMiddleware is start!!!')
        request.headers.update({
                                   'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.7'})
        request.headers.update({'accept-language': 'en-US,en;q=0.9'})
        request.headers.update({'priority': 'u=0, i'})
        request.headers.update({'sec-fetch-dest': 'document'})
        request.headers.update({'sec-fetch-mode': 'navigate'})
        request.headers.update({'sec-fetch-site': 'none'})
        request.headers.update({'sec-fetch-user': '?1'})
        request.headers.update({'upgrade-insecure-requests': '1'})
        # 添加网络连接情况试一下
        request.headers.update({'downlink': random.randint(5, 20)})
        request.headers.update({'rtt': random.randint(50, 300)})
        request.headers.update({'ect': '4g'})
        request.headers.update({'Connection': 'keep-alive'})
        # 这里改成使用随机的ua
        request.headers.update({'user-agent': ua.chrome})
        logger.debug('Commodity.middlewares.CommodityHeadersMiddleware is done!!!')


class CommodityRetryMiddleware(RetryMiddleware):

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
            if verify_response.status == 404:
                raise RequestException(f'The listing is not exist')
            raise RequestException(f'Request status code is error [{response.status}]')

        if verify_response.is_dog_page() or verify_response.is_validate_captcha():
            # 出现狗页面 或者 出现验证码页面
            reason = 'browser error:' + verify_response.content
            spider.add_exception(reason, 'request')
            retry_request = self._retry(request, reason, spider)
            if retry_request:
                response = retry_request
            else:
                BaseCookiesMiddleware(self.settings).delete_cookies(
                    cookies=None,
                    domain=spider.get_country_site(),
                    zip_code=spider.subtask_handle_data.get('zip_code'),
                    network_line_id=spider.network_line_id,
                )
                raise RequestException(f'Trigger the anti-claw mechanism')

        # 判断是否为listing不存在的页面
        if verify_response.is_not_listing():
            # listing 不存在
            raise RequestException(f'The listing is not exist')

        if verify_response.is_error_page() or verify_response.is_blank_page():
            # 页面错误【浏览器无响应导致无内容 或 浏览器超时 或 空白页面】
            raise RequestException('the page response is error!')

        # 判断地址是否存在 subtask_handle_data
        if verify_response.is_not_address(spider.subtask_handle_data.get('country_code'),
                                          spider.subtask_handle_data.get('zip_code')):
            BaseCookiesMiddleware(self.settings).delete_cookies(
                cookies=None,
                domain=spider.get_country_site(),
                zip_code=spider.subtask_handle_data.get('zip_code'),
                network_line_id=spider.network_line_id,
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


class CommoditySocks5Middleware(HTTPDownloadHandler):
    """
    将请求代理改成使用socks5
    """
    def process_request(self, request, spider):
        headers_dict = {k.decode(): v[0].decode() if v else '' for k, v in request.headers.items()}
        proxies = request.meta.get('proxies')
        proxies = {'https': proxies, 'http': proxies}
        logger.error(f'socks5 proxy is {proxies}')
        response = requests.get(request.url, headers=headers_dict, proxies=proxies)
        logger.error('*'*200)
        logger.error(request.url)
        logger.error(headers_dict)
        logger.error(proxies)
        response = ScrapyResponse(
            url=request.url,
            status=response.status_code,
            headers=request.headers,
            body=response.content,
            request=request
        )
        return response
