import sys
sys.path.append('..')
sys.path.append('../..')
sys.path.append('../../..')
from ..items import CommodityItem
from tool.extract.detail.detail_extract import Extract
from common.base.scrapy_base import CommoditySpiderBase


class DetailSpider(CommoditySpiderBase):
    name = "detail"

    def __init__(self, params=None, *args, **kwargs):
        """
        初始化
        :param params:
        :param args:
        :param kwargs:
        """
        # params = 'eyJzdWJfdGFza19pZCI6ICI2NTlmOTY3MWRkMDUwMDAwYmQwMDY4ZGIiLCAidGFza19pZCI6ICI2NTlmOTZiNWRkMDUwMDAwYmQwMDY4ZGMiLCAidGltZSI6IDE3MDQ5MDQ5NzUuNzY3NSwgInNpZ24iOiAiN2QwMThiMDc4OGE1NWZkNTI3ZjJiODA3YWYwNGQ3ODMifQ=='
        super().__init__(params, *args, **kwargs)
        # 请求参数
        # 参数部分要另外处理
        handle_data = self.subtask_handle_data
        self.asin = handle_data.get("asin")
        if not self.asin:
            raise ValueError("The asin does not exist")

    def start_requests(self):
        yield self.form_request(
            url=self.get_request_url(),
            params={
                "keywords": f"{self.asin} a"
            }
        )

    def parse(self, response, **kwargs):
        # 开始解析
        content = response.text
        ex = Extract(self.subtask_handle_data.get("country_code"), content)
        item = CommodityItem()

        item["image_result"] = ex.get_image_result()
        item["result"] = ex.get_result()
        yield item

    def get_request_url(self):
        """
        获取请求url
        :return:
        """
        return f"https://{self.get_country_site()}/dp/{self.asin}"

    # def execute_success_call(self):
    #     pass
    #
    # def execute_error_call(self, exception):
    #     pass
