# -*- coding: UTF-8 -*-
from tool.extract.review.extract_base import ReviewExtractBase
from common.helpers import get_dynamic_class
from common.exceptions.exception import SystemException


class UsExtract(ReviewExtractBase):
    """
    美国站点【其他和美国规则相似的可继承该类】
    """
    def _get_result_review_title_rule(self):
        return super(UsExtract, self)._get_result_review_title_rule()

    def _get_result_review_score_rule(self):
        return super(UsExtract, self)._get_result_review_score_rule()

    def _get_result_review_date_rule(self):
        return super(UsExtract, self)._get_result_review_date_rule()

    def _get_result_review_badge_rule(self):
        return super(UsExtract, self)._get_result_review_badge_rule()

    def _get_result_review_body_rule(self):
        return super(UsExtract, self)._get_result_review_body_rule()

    def _get_result_review_helpful_rule(self):
        return super(UsExtract, self)._get_result_review_helpful_rule()

    def _get_result_review_image_rule(self):
        return super(UsExtract, self)._get_result_review_image_rule()

    def _get_result_review_stats_rule(self):
        return super(UsExtract, self)._get_result_review_stats_rule()

    def _get_main_result_title_rule(self):
        return super(UsExtract, self)._get_main_result_title_rule()

    def _get_main_result_star_rule(self):
        return super(UsExtract, self)._get_main_result_star_rule()

    def _get_main_result_total_rule(self):
        return super(UsExtract, self)._get_main_result_total_rule()

    def _get_main_result_histogram_rule(self):
        return super(UsExtract, self)._get_main_result_histogram_rule()


class DeExtract(UsExtract):
    """
    德国站点
    """
    pass


class GbExtract(UsExtract):
    """
    英国站点
    """
    pass


class FrExtract(UsExtract):
    """
    法国站点
    """
    pass


class EsExtract(UsExtract):
    """
    西班牙站点
    """
    pass


class ItExtract(UsExtract):
    """
    意大利站点
    """
    pass


class NlExtract(UsExtract):
    """
    荷兰站点
    """
    pass


class PlExtract(UsExtract):
    """
    波兰站点
    """
    pass


class SeExtract(UsExtract):
    """
    瑞典站点
    """
    pass


class CaExtract(UsExtract):
    """
    加拿大站点【由于规则和欧洲站一致，所以继承于欧洲站点基类】
    """
    pass


class JpExtract(UsExtract):
    """
    日本站点【由于规则和欧洲站一致，所以继承于欧洲站点基类】
    """
    pass


class SgExtract(UsExtract):
    """
    新加坡站点【由于规则和欧洲站一致，所以继承于欧洲站点基类】
    """
    pass


class Extract:
    """
    提取类
    """
    def __init__(self, country, content):
        """
        初始化
        :param country:
        :param content:
        """

        class_str = f"tool.extract.review.review_extract.{country.capitalize()}Extract"
        class_obj = get_dynamic_class(class_str)
        if not class_obj:
            raise SystemException("The parse class does not exist" + class_str)
        self.extract_handle = class_obj(content)

    def get_result(self):
        """
        获取结果
        """
        return self.extract_handle.get_result()

    def get_main_result(self):
        """
        获取结果
        """
        return self.extract_handle.get_main_result()

    def __getattr__(self, item):
        """
        办法不存在时调用
        "param item:
        :return:
        """
        if getattr(self.extract_handle, item):
            return getattr(self.extract_handle, item)
