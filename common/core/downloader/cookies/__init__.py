
from common.core.downloader.cookies.downloadermiddlewares.cookies import (
    CookiesMiddleware,
    get_request_cookies
)
from scrapy.exceptions import NotConfigured
from common.utils.distribution_lock import RedisLock
from common.utils.cache import Chcaed
from common.utils.sundry_utils import UrlParse


class BaseCookiesMiddleware(object):
    """
    cookies 基础中间件
    """

    must_cookie_name = []

    def __init__(self, settings):
        self.settings = settings
        if not self.settings.get('COOKIES_ENABLE'):
            raise NotConfigured
        self.domain = None
        self.extra_key = None
        # 锁
        self.lock_time = 30
        self.lock = RedisLock(
            lock_name='change_address',
            lock_timeout=self.lock_time,
        )

    def process_request(self, request, spider):
        """
        请求中间件
        :param request:
        :param spider:
        :return:
        """
        # domain
        url_parse = UrlParse(request.url)
        domain = url_parse.get_domain()
        if domain:
            self.domain = domain
        else:
            self.domain = request.url

        # current
        extra_key = request.meta['current']
        if not extra_key:
            extra_key = 'main'
        self.extra_key = extra_key

        # cookies
        cookies = self.get_cookies()
        if not cookies:
            self.init_cookies(
                request=request,
                spider=spider
            )
        else:
            self.send_cookies(
                cookies,
                request,
            )

    def process_response(self, request, response, spider):
        """
        响应中间件
        :param request:
        :param response:
        :param spider:
        :return:
        """
        return response

    def init_cookies(self, request, spider):
        """
        初始化cookies
        :param request:
        :param spider:
        :return:
        """
        pass

    def send_cookies(self, cookies, request):
        """
        保存cookies
        :param cookies:
        :param request:
        :return:
        """
        self.set_cookies(cookies)
        request.headers['cookie'] = cookies

    def delete_cookies(self, cookies):
        """
        删除cookies
        :param cookies:
        :return:
        """
        self._delete_cookies(cookies)

    def _get(self):
        """
        获取所有父类
        :return:
        """
        res = {}
        redis_key = self.domain + '_cookies'
        try:
            # 从redis服务器获取
            res = Chcaed.get(redis_key)
            if not res:
                res = {}
        except EOFError:
            pass
        return res

    def _get_key(self):
        """
        获取键
        :return:
        """
        return '_'.join(
            [self.domain, self.extra_key]
        )

    def get_cookies(self):
        """
        获取当前cookies
        :return:
        """
        all_cookies = self._get()
        key = self._get_key()
        if key in all_cookies:
            return all_cookies[key]
        else:
            return []

    def set_cookies(self, cookies):
        """
        设置cookies
        :param cookies:
        :return:
        """
        # 加锁
        identifier = self.lock.acquire_lock(
            acquire_timeout=self.lock_time
        )
        try:
            # 所有cookie
            all_cookies = self._get()
            all_cookies[self._get_key()] = cookies
            # 保存cookie
            self.save(all_cookies)
        except:
            pass
        finally:
            self.lock.release_lock(
                identifier=identifier
            )

    def save(self, cookies):
        """
        设置cookies
        :param cookies:
        :return:
        """
        redis_key = self.domain + '_cookies'
        return Chcaed.put(redis_key, cookies)

    def _delete_cookies(self, cookies):
        """
         删除cookies
        :param cookies:
        :return:
        """
        # 加锁
        identifier = self.lock.acquire_lock(
            acquire_timeout=self.lock_time
        )
        try:
            # 所有cookie
            all_cookies = self._get()
            all_cookies[self._get_key()] = cookies
            # 保存cookie
            self.save(all_cookies)
        except:
            pass
        finally:
            self.lock.release_lock(
                identifier=identifier
            )

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)
