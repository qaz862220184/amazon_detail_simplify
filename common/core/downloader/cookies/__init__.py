
from common.core.downloader.cookies.downloadermiddlewares.cookies import (
    CookiesMiddleware,
    get_request_cookies
)
from scrapy.exceptions import NotConfigured
from common.utils.distribution_lock import RedisLock
from common.utils.cache import Chcaed
from common.utils.sundry_utils import UrlParse


class ScrapyCookiesMiddleware(CookiesMiddleware):
    # 必须的cookie
    must_cookie = []

    def process_request(self, request, spider):
        """
        cookie请求中间件
        :param request:
        :param spider:
        :return:
        """
        if request.meta.get('dont_merge_cookies', False):
            return

        cookiejar_key = request.meta.get("cookiejar")
        jar = self.jars[cookiejar_key]
        if not self.__is_contain_cookies(jar, request):
            # 不存在cookie文件中，从新的地方获取
            init_cookies = self.init_cookies(request, spider)
            if init_cookies:
                request.cookies = init_cookies

        # 将cookie保存到请求头中
        cookies = get_request_cookies(jar, request)
        for cookie in cookies:
            jar.set_cookie_if_ok(cookie, request)

        self.jars[cookiejar_key] = jar
        # set Cookie header
        request.headers.pop('Cookie', None)
        jar.add_cookie_header(request)
        self._debug_cookie(request, spider)


    def init_cookies(self, request, spider):
        """
        :param request:
        :param spider:
        :return:
        """
        return

    def __is_contain_cookies(self, jar, request):
        """
        是否包含重要cookie【判断是不是第一次请求】
        """
        request_clone = request.copy()
        jar.add_cookie_header(request_clone)
        cookie = request_clone.headers.get('cookie')
        # 是否包含
        is_contain = False
        if cookie:
            cookies = cookie.decode('utf-8')
            cookies = dict([l.split("=", 1) for l in cookies.split("; ")])
            contain_count = 0
            for cookie_name in self.must_cookie:
                if cookie_name in cookies:
                    contain_count += 1
            is_contain = True if contain_count == len(self.must_cookie) else False
        return is_contain


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
            db='default',
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
        extra_key = request.meta.get('current')
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

    def delete_cookies(self, cookies, zip_code, network_line_id):
        """
        删除cookies
        :param cookies:
        :param zip_code:
        :param network_line_id:
        :return:
        """
        self._delete_cookies(cookies, zip_code, network_line_id)

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
        保存所有cookie
        :param cookies:
        :return:
        """
        redis_key = self.domain + '_cookies'
        return Chcaed.put(redis_key, cookies)

    def _delete_cookies(self, cookies, zip_code, network_line_id):
        """
        删除cookies
        :param cookies:
        :param zip_code:
        :param network_line_id:
        :return:
        """
        # 加锁
        identifier = self.lock.acquire_lock(
            acquire_timeout=self.lock_time
        )
        try:
            # 所有cookie
            key_name = '_'.join(
                [self.domain, network_line_id, zip_code]
            )
            all_cookies = self._get()
            all_cookies[key_name] = cookies
            # 保存cookie
            self.save(all_cookies)
        except:
            import traceback
            traceback.print_exc()
            pass
        finally:
            self.lock.release_lock(
                identifier=identifier
            )

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)
