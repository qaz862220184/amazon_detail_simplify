
from common.core.downloader.cookies.downloadermiddlewares.cookies import (
    CookiesMiddleware,
    get_request_cookies
)


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
