import sys
sys.path.append('..')
sys.path.append('../..')
sys.path.append('../../..')
from ..items import CommodityItem
from tool.extract.detail.detail_extract import Extract
import scrapy
from urllib.parse import urlencode


class DetailSpider(scrapy.Spider):
    name = "detail"

    def __init__(self, params=None, *args, **kwargs):
        """
        初始化
        :param params:
        :param args:
        :param kwargs:
        """
        super().__init__()
        # 请求参数
        self.asin = params.get("asin")
        self.country_code = params.get('country_code')
        self.zip_code = params.get('zip_code')
        self.country_site = params.get('country_site')
        if not self.asin:
            raise ValueError("The asin does not exist")

    def start_requests(self):
        params = {
            "keywords": f"{self.asin} a"
        }
        url = f'{self.get_request_url()}?{urlencode(params)}'
        yield scrapy.Request(
            url=url,

        )

    def parse(self, response, **kwargs):
        # 开始解析
        content = response.text
        ex = Extract(self.country_code, content)
        item = CommodityItem()

        item["image_result"] = ex.get_image_result()
        item["result"] = ex.get_result()
        yield item

    def get_request_url(self):
        """
        获取请求url
        :return:
        """
        return f"https://{self.country_site}/dp/{self.asin}"
