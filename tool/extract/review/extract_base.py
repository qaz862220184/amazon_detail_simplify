# -*- coding: UTF-8 -*-
from abc import ABCMeta, abstractmethod
from lxml import etree
from common.exceptions.exception import XpathException
from common.helpers import get_list_value, value_of_empty


class ReviewExtractBase(metaclass=ABCMeta):
    """
    评论页面提取父类
    """

    def __init__(self, content):
        # 初始化根
        if not content:
            raise XpathException("The extracted content cannot be empty")
        self._content = content
        self._struct = etree.HTML(content)
        # 评论主体
        self._main_result_selector = None
        self._main_result = {}
        # 评论详情
        self._result_selector = None
        self._result = {}

    def get_content(self):
        """
        内容
        """
        return self._content

    def get_struct(self):
        """
        选择器
        """
        return self._struct

    # 获取评论主体部分
    def get_result(self):
        """
        获取result-items
        """
        result_selector = self.get_result_selector()
        if not self._result and value_of_empty(result_selector) is False:
            # 评论内容
            review_list = self._matching_rule('./div[@data-hook="review"]', result_selector)
            items = []
            sort = 0
            for review_info in review_list:
                # 排序
                sort += 1
                # 评论id
                review_id = self._get_value('./@id', review_info, 0)
                # 评论标题
                title = self._get_value(self._get_result_review_title_rule(), review_info, 0)
                # 评论星级
                score = self._get_value(self._get_result_review_score_rule(), review_info, 0)
                # 评论日期
                date = self._get_value(self._get_result_review_date_rule(), review_info, 0)
                # badge 标识
                badge = self._get_value(self._get_result_review_badge_rule(), review_info, 0)
                # 评论正文 - 这边取不到分段的数据
                # body = self._get_value(self._get_result_review_body_rule(), review_info, 0)
                body = self._matching_rule(self._get_result_review_body_rule(), review_info)
                # helpful 评价
                helpful = self._get_value(self._get_result_review_helpful_rule(), review_info, 0)
                # 评论图片 去除掉分辨率就可得到原图
                image_list = self._matching_rule(self._get_result_review_image_rule(), review_info)
                # 视频是blob的先放弃
                items.append({
                    "sort": sort,
                    "id": review_id,
                    'title': title,
                    "score": score,
                    "date": date,
                    "badge": badge,
                    "body": body,
                    "helpful": helpful,
                    "image_list": image_list,
                })

            # 评论统计
            stats = self._get_value(self._get_result_review_stats_rule(), result_selector, 0)
            self._result = {
                'items': items,
                'stats': stats.strip() if stats else stats,
            }

        return self._result

    def get_result_selector(self):
        """
        获取result选择器
        """
        if self._result_selector is None:
            result_selector = self._struct.xpath(
                self._get_result_rule()
            )
            if result_selector:
                self._result_selector = result_selector[0]
            else:
                raise XpathException("Result selector parse error!")
        return self._result_selector

    def _get_result_rule(self):
        """
        获取result的规则
        """
        return '//div[@id="cm_cr-review_list"]'

    def _get_value(self, rule, parent_node, key, default=None):
        """
        获取值
        :param rule: xpath规则
        :param parent_node: 父节点
        :param key:
        :param default:
        :return:
        """
        result = self._matching_rule(rule, parent_node)
        return get_list_value(result, key, default)

    def _matching_rule(self, rule, parent_node):
        """
        匹配规则
        :param rule: xpath规则
        :param parent_node: 父节点
        :return:
        """
        if isinstance(parent_node, etree._Element) is False:
            raise XpathException('ParentNode t is not of type [etree._Element]!')
        if not rule:
            raise XpathException('Rule cannot be empty!')
        result = None
        if isinstance(rule, list):
            for item in rule:
                result = parent_node.xpath(item)
                if result:
                    break
        else:
            result = parent_node.xpath(rule)
        return result

    # 具体的数据解析规则
    @abstractmethod
    def _get_result_review_title_rule(self):
        """
        获取result-review-title规则【默认美国站点规则】
        :return:
        """
        return './/*[@data-hook="review-title"]/span[2]/text()'

    @abstractmethod
    def _get_result_review_score_rule(self):
        """
        获取result-review-score 规则【默认美国站点规则】
        :return:
        """
        return './/*[@data-hook="review-title"]//span[@class="a-icon-alt"]/text()'

    @abstractmethod
    def _get_result_review_date_rule(self):
        """
        获取result-review-date 规则【默认美国站点规则】
        :return:
        """
        return './/span[@data-hook="review-date"]/text()'

    @abstractmethod
    def _get_result_review_badge_rule(self):
        """
        获取result-review-badge 规则【默认美国站点规则】
        :return:
        """
        return './/span[@data-hook="avp-badge"]/text()'

    @abstractmethod
    def _get_result_review_body_rule(self):
        """
        获取result-review-body 规则【默认美国站点规则】
        :return:
        """
        return './/span[@data-hook="review-body"]/span/text()'

    @abstractmethod
    def _get_result_review_helpful_rule(self):
        """
        获取result-review-helpful 规则【默认美国站点规则】
        :return:
        """
        return './/span[@data-hook="helpful-vote-statement"]/text()'

    @abstractmethod
    def _get_result_review_image_rule(self):
        """
        获取result-review-helpful 规则【默认美国站点规则】
        :return:
        """
        return './/div[@class="review-image-tile-section"]//img[@alt="Customer image"]/@src'

    @abstractmethod
    def _get_result_review_stats_rule(self):
        """
        获取result-review-stats 规则【默认美国站点规则】
        :return:
        """
        return '//div[@id="filter-info-section"]/div/text()'

    # 评论主体部分
    def get_main_result(self):
        """
        获取main-result
        """
        main_result_selector = self.get_main_result_selector()
        if not self._main_result and value_of_empty(main_result_selector) is False:
            # 商品标题
            product_title = self._get_value(self._get_main_result_title_rule(), main_result_selector, 0)
            # 商品星级
            product_star = self._get_value(self._get_main_result_star_rule(), main_result_selector, 0)
            # 评论总计
            review_total = self._get_value(self._get_main_result_total_rule(), main_result_selector, 0)
            # 评分分布
            histogram_list = self._matching_rule(self._get_main_result_histogram_rule(), main_result_selector)
            histogram_table = {}
            if histogram_list:
                for histogram in histogram_list:
                    data = self._matching_rule('./td/span[@class="a-size-base"]/a/text()', histogram)
                    histogram_table.update({data[0].strip(): data[1].strip()})

            items = {
                "product_title": product_title,
                "product_star": product_star,
                "review_total": review_total,
                "histogram_table": histogram_table,
            }

            self._main_result = {
                'items': items,
            }

        return self._main_result

    def get_main_result_selector(self):
        """
        获取result选择器
        """
        if self._main_result_selector is None:
            result_selector = self._struct.xpath(
                self._get_main_result_rule()
            )
            if result_selector:
                self._main_result_selector = result_selector[0]
            else:
                raise XpathException("Result selector parse error!")
        return self._main_result_selector

    def _get_main_result_rule(self):
        """
        获取main-result的规则
        """
        return '//div[@role="main"]//div[@id="cm_cr-product_info"]'

    @abstractmethod
    def _get_main_result_title_rule(self):
        """
        获取 main-result-title 规则
        """
        return './/div[@class="a-row product-title"]/h1/a/text()'

    @abstractmethod
    def _get_main_result_star_rule(self):
        """
        获取 main-result-star 规则
        """
        return './/span[@class="a-icon-alt"]/text()'

    @abstractmethod
    def _get_main_result_total_rule(self):
        """
        获取 main-result-total
        """
        return './/div[@data-hook="total-review-count"]/span/text()'

    @abstractmethod
    def _get_main_result_histogram_rule(self):
        """
        获取 main-result-histogram 规则
        """
        return '//table[@id="histogramTable"]//tr'
