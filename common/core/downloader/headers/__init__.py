from common.core.downloader.headers.request_headers import  (
    RequestParam
)
from scrapy.http.headers import Headers



class HeaderMiddleware:
    def process_request(self, request, spider):
        """
        设置头部参数
        :param request:
        :param spider:
        :return:
        """
        headers = RequestParam.get_headers(
            request_url=request.url
        )
        request.headers = self.get_headers(
            headers=headers
        )

    @classmethod
    def get_headers(cls, headers):
        if isinstance(headers, Headers):
            return headers
        else:
            return Headers(headers)