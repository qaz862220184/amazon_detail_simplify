#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
from abc import ABCMeta, abstractmethod
from lxml import etree
from common.exceptions.exception import XpathException
from common.helpers import get_list_value, value_of_empty


class DetailExtractBase(metaclass=ABCMeta):
    """
    详情页面提取父类
    """

    def __init__(self, content):
        # 初始化根
        if not content:
            raise XpathException('The extracted content cannot be empty')
        self._content = content
        self._struct = etree.HTML(content)
        # 详情页左边图片数据
        self._image_selector = None
        self._image_result = {}
        # 详情页中部数据
        self._result_selector = None
        self._result = {}

    def get_content(self):
        """
        内容
        """
        return self._content

    def get_struct(self):
        """
        根选择器
        """
        return self._struct

    # 获取详情页中的左边图片数据
    def get_image_result(self):
        """
            获取图片信息 image-result
        """
        result_selector = self.get_result_selector()
        if not self._image_result and value_of_empty(result_selector) is False:
            result = self._matching_rule(
                self._get_image_result_rule(),
                result_selector
            )
            result = result[0]
            # 主图
            main_image = self._get_value(self._get_image_result_main_image_rule(), result, 0)
            # 小图列表
            small_image_list = self._matching_rule(
                self._get_image_result_small_image_list_rule(),
                result
            )
            alt_images = []
            for small_image in small_image_list:
                image_url = self._get_value(self._get_image_result_small_image_rule(), small_image, 0)
                alt_images.append(image_url)

            item = {
                'main_image': main_image,
                'alt_images': alt_images,
            }

            self._image_result = {
                'item': item,
            }

        return self._image_result

    def get_image_selector(self):
        """
        获取result选择器
        """
        if self._image_selector is None:
            result_selector = self._struct.xpath(
                self._get_result_rule()
            )
            if result_selector:
                self._result_selector = result_selector[0]
            else:
                raise XpathException('result selector parse error!')
        return self._result_selector

    def _get_image_result_rule(self):
        """
        result第二层
        获取result-items规则【默认美国站点规则】
        :return:
        """
        return '//div[@id="leftCol"]'

    @abstractmethod
    def _get_image_result_main_image_rule(self):
        """
        获取result-items-main_image规则【默认美国站点规则】
        :return:
        """
        return '//div[@id="imgTagWrapperId"]/img/@src'

    @abstractmethod
    def _get_image_result_small_image_list_rule(self):
        """
        获取result-items-small_image_list规则【默认美国站点规则】
        :return:
        """
        return '//div[@id="altImages"]/ul/li[@class="a-spacing-small item"]'

    @abstractmethod
    def _get_image_result_small_image_rule(self):
        """
        获取result-items-small_image规则【默认美国站点规则】
        :return:
        """
        return './/img/@src'

    # 获取详情页中部数据信息
    def get_result(self):
        """
            获取result-items
        """
        result_selector = self.get_result_selector()
        if not self._result and value_of_empty(result_selector) is False:
            result = self._matching_rule(
                self._get_result_items_rule(),
                result_selector
            )
            result = result[0]
            # 接下来针对各个数据进行规则抓取
            # title
            title = self._get_value(self._get_result_items_title_rule(), result, 0)
            # original price --不做其他判断，取当前折扣形式和原价
            discount_type = self._get_value(self._get_result_items_discount_type_rule(), result, 0)
            discount_price = self._get_value(self._get_result_items_discount_price_rule(), result, 0)

            discount_type = discount_type.strip().replace(':', '') if discount_type else discount_type
            discount_price = discount_price.strip() if discount_price else discount_price
            original_price = {'discount_type': discount_type, 'before_discount_price': discount_price}
            # 获取折扣百分比 savings_percentage
            saving_percentage = self.get_result_items_saving_percentage(result)
            # price
            price = self.get_result_items_price(result)
            # stars
            stars = self.get_result_items_stars(result)
            # ratings
            ratings = self.get_result_items_ratings(result)
            # selling points 卖点的li列表
            selling_points = self.get_result_items_selling_points(result)
            # product overview 产品概述
            product_overview_list = self.get_product_overview(result)
            # best seller rank 热销排名
            best_seller_rank = self.get_result_items_best_seller_rank(result)
            # 榜单分类 category list
            category_list = self._matching_rule(self._get_result_items_category_list_rule(), result_selector)
            category_info = []
            if category_list:
                for category in category_list:
                    category_info.append(category.strip() if category else category)
            # 品牌
            brand = self.get_result_items_brand(result)
            # 页面卖家
            seller = self.get_result_items_seller(result)
            # 页面卖家id
            seller_id = self.get_result_items_seller_id(result)
            # 判断是否有页面购物车
            cart = self._get_value(self._get_result_items_cart_rule(), result, 0)
            if value_of_empty(cart) is False:
                is_cart = True
            else:
                is_cart = False
            # 生产厂家
            manufacturer = self.get_result_items_manufacturer(result)
            # 优惠券的判断
            coupon = self._get_value(self._get_result_items_coupon_rule(), result, 0)
            if value_of_empty(coupon) is False:
                is_coupon = True
            else:
                is_coupon = False
            # 优惠券的折扣和折扣后的价格
            coupon_discount = None
            used_coupon_price = None
            if is_coupon:
                coupon_discount = self.get_result_items_coupon_discount(result)
                if not coupon_discount:
                    is_coupon = False
                # used_coupon_price = self.get_used_coupon_price(price, coupon_discount)
            # 物流时效--delivery_date
            delivery_date = self.get_result_items_delivery_date(result)
            # amazon choice
            is_amazon_choice = self.get_result_items_amazon_choice(result)
            # amazon choice keywords
            amazon_choice_keywords = ''
            if is_amazon_choice:
                amazon_choice_keywords = self._get_value(self._get_result_items_amazon_choice_keywords_rule(), result, 0)
                amazon_choice_keywords = amazon_choice_keywords if amazon_choice_keywords else 'Overall Pick'
            # is_deal
            is_deal = self._get_value(self._get_result_items_deal_rule(), result, 0)
            deal_type = None
            end_time = None
            if is_deal:
                deal_type = self.get_deal_type(result)
                end_time = self._get_value(self.get_result_items_deal_end_time_rule(), result, 0)
            # 销量
            sales_volume = self._get_value(self.get_result_items_sales_volume_rule(), result, 0)
            # 型号
            model_number = self.get_result_item_model_number(result)

            item = {
                'title': title.strip() if title else title,
                'original_price': original_price,
                'saving_percentage': saving_percentage,
                'price': price.strip() if price else price,
                'stars': stars.strip() if stars else stars,
                'rating': ratings.strip() if ratings else ratings,
                'selling_points': selling_points,
                'product_overview': product_overview_list,
                'best_seller_rank': best_seller_rank,
                'category_info': category_info,
                'brand': brand,
                'seller': seller,
                'is_cart': is_cart,
                'manufacturer': manufacturer,
                'is_coupon': is_coupon,
                'coupon_discount': coupon_discount,
                # 'used_coupon_price': used_coupon_price,
                'delivery_date': delivery_date,
                'is_amazon_choice': is_amazon_choice,
                'amazon_choice_keywords': amazon_choice_keywords,
                'is_deal': is_deal,
                'deal_type': deal_type,
                'end_time': end_time,
                'sales_volume': sales_volume,
                'model_number': model_number,
                'seller_id': seller_id,
            }

            self._result = {
                'item': item,
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
                raise XpathException('result selector parse error!')
        return self._result_selector

    def _get_result_rule(self):
        """
        获取result规则
        result第一层
        """
        return '//div[@id="dp-container"]'

    def _get_result_items_rule(self):
        """
        result第二层
        获取result-items规则【默认美国站点规则】
        :return:
        """
        return '//div[@id="dp"]'

    def _get_product_overview_rule(self):
        """
        product overview产品概述
        :return:
        """
        return '//div[@id="productOverview_feature_div"]'

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
    def _get_result_items_title_rule(self):
        """
        获取result-items-title规则【默认美国站点规则】
        :return:
        """
        return '//span[@id="productTitle"]/text()'

    @abstractmethod
    def _get_result_items_list_price_rule(self):
        """
        获取result-items-list-price规则【默认美国站点规则】
        :return:
        """
        return '//span[contains(@class, "a-price a-text-price") and @data-a-strike="true"]/span/text()'

    @abstractmethod
    def _get_result_items_discount_type_rule(self):
        """
        获取result-items-discount-type规则【默认美国站点规则】
        :return:
        """
        return '//div[@id="centerCol"]//*[@class="a-size-small a-color-secondary aok-align-center basisPrice" or ' \
               '@class="a-color-secondary a-size-base a-text-right a-nowrap"]/text()'

    @abstractmethod
    def _get_result_items_discount_price_rule(self):
        """
        获取result-items-discount-price规则【默认美国站点规则】
        :return:
        """
        return '//div[@id="centerCol"]//span[contains(@class, "a-price a-text-price") and @data-a-strike="true"]/span/text()'

    @abstractmethod
    def _get_result_items_saving_percentage_rule(self):
        """
        获取result-items-saving-percentage规则【默认美国站点规则】
        :return:
        """
        return '//span[contains(@class, "savingsPercentage")]/text()'


    @abstractmethod
    def _get_result_items_price_rule(self):
        """
        获取result-items-price规则【默认美国站点规则】
        :return:
        """
        return '//span[contains(@class, "priceToPay") or contains(@class, "apexPriceToPay")]/span[@aria-hidden="true"]'

    @abstractmethod
    def _get_result_items_erp_rule(self):
        """
        获取result-items-erp规则【默认美国站点规则】
        :return:
        """
        return '//span[@class="a-price a-text-price"]/span/text()'

    @abstractmethod
    def _get_result_items_stars_rule(self):
        """
        获取result-items-stars规则【默认美国站点规则】
        :return:
        """
        return '//span[@id="acrPopover"]/@title'

    @abstractmethod
    def _get_result_items_ratings_rule(self):
        """
        获取result-items-ratings规则【默认美国站点规则】
        :return:
        """
        return '//span[@id="acrCustomerReviewText"]/text()'

    @abstractmethod
    def _get_result_items_selling_points_rule(self):
        """
        获取result-items-selling-points规则【默认美国站点规则】
        :return:
        """
        return '//div[@id="feature-bullets"]/ul/li'

    @abstractmethod
    def _get_result_items_feature_table_rule(self):
        """
        获取result-items-feature-table规则【默认美国站点规则】
        """
        return '//div[@id="productOverview_feature_div"]//table[@class="a-normal a-spacing-micro"]/tbody/tr'

    @abstractmethod
    def _get_result_items_best_seller_rank_rule(self):
        """
        获取result-items-best-seller-rank规则【默认美国站点规则】
        :return:
        """
        return '//div[@id="dp"]//a[contains(@href, "/gp/bestsellers/")]/..'

    @abstractmethod
    def _get_result_items_category_list_rule(self):
        """
        获取result-items-category-list规则【默认美国站点规则】
        :return:
        """
        return '//div[@id="wayfinding-breadcrumbs_feature_div"]/ul/li//a/text()'

    def _get_result_items_brand_rule(self):
        """
        获取result-items-brand规则【默认美国站点规则】
        :return:
        """
        return '//a[@id="bylineInfo"]/text()'

    @abstractmethod
    def _get_result_items_seller_rule_base(self):
        """
        获取result-items-seller规则【默认美国站点规则】
        :return:
        """
        return '//a[@id="sellerProfileTriggerId"]/text()'

    @abstractmethod
    def _get_result_items_seller_rule(self):
        """
        获取result-items-seller规则【默认美国站点规则】
        :return:
        """
        return '//*[@id="tabular-buybox"]//div[@class="tabular-buybox-text" and @tabular-attribute-name="Sold by"]/div/span//text()'

    @abstractmethod
    def _get_result_items_cart_rule(self):
        """
        获取result-items-cart规则【默认美国站点规则】
        :return:
        """
        return '//*[@id="add-to-cart-button"]'

    def _get_result_items_coupon_rule(self):
        """
        获取result-items-coupon规则【默认美国站点规则】
        :return:
        """
        return '//*[@id="promoPriceBlockMessage_feature_div"]//span[@class="promoPriceBlockMessage"]'

    def _get_result_items_coupon_discount_rule(self):
        """
        获取result-items-discount规则【默认美国站点规则】
        :return:
        """
        return '//*[@id="promoPriceBlockMessage_feature_div"]//*[contains(@id, "couponTextpctch")]/text()'

    def _get_result_items_free_delivery_date_rule(self):
        """
        获取result-items-delivery-date规则【默认美国站点规则】
        :return:
        """
        return '//span[@data-csa-c-content-id="DEXUnifiedCXPDM"]/@data-csa-c-delivery-time'

    def _get_result_items_fastest_delivery_date_rule(self):
        """
        获取result-items-delivery-date规则【默认美国站点规则】
        :return:
        """
        return '//span[@data-csa-c-content-id="DEXUnifiedCXSDM"]/@data-csa-c-delivery-time'

    def _get_result_items_amazon_choice_rule(self):
        """
        获取result-items-amazon-chois规则【默认美国站点规则】
        :return:
        """
        return '//*[@id="acBadge_feature_div"]/div'

    def _get_result_items_amazon_choice_keywords_rule(self):
        """
        获取result-items-amazon-chois-keywords规则【默认美国站点规则】
        :return:
        """
        return '//*[@id="acBadge_feature_div"]//span[@class="ac-keyword-link"]//text()'

    def _get_result_items_deal_rule(self):
        """
        获取result-items-amazon-deal规则【默认美国站点规则】
        :return:
        """
        return '//*[@id="dealBadgeSupportingText"]'

    def _get_result_items_light_deal_rule(self):
        """
        获取result-items-amazon-light-deal规则【默认美国站点规则】
        :return:
        """
        return '//*[@id="dealsAccordionCaption_feature_div"]'

    def get_result_items_deal_end_time_rule(self):
        """
        获取result-items-amazon-deal-end-time规则【默认美国站点规则】
        :return:
        """
        return '//*[@id="detailpage-dealBadge-countdown-timer"]/text()'

    def get_result_items_sales_volume_rule(self):
        """
        获取result-items-sales_volume规则【默认美国站点规则】
        :return:
        """
        return '//*[@id="socialProofingAsinFaceout_feature_div"]//span[@id="social-proofing-faceout-title-tk_bought"]/span/text()'

    @abstractmethod
    def _get_result_items_seller_id_rule(self):
        """
        获取result-items-seller规则【默认美国站点规则】
        :return:
        """
        return '//a[@id="sellerProfileTriggerId"]/@href'

    # 实现无法直接获取需要判断的内容
    def get_result_items_saving_percentage(self, result):
        saving_percentage = None
        percentage_info = self._get_value(self._get_result_items_saving_percentage_rule(), result, 0)
        if percentage_info:
            saving_percentage = percentage_info.replace('-', '')
        return saving_percentage

    def get_result_items_price(self, result):
        price = None
        price_info = self._matching_rule(
            self._get_result_items_price_rule(),
            result,
        )
        if price_info:
            # 如果有取第一个的值
            bsr_info = self._matching_rule(
                './/text()',
                price_info[0],
            )
            price = ''.join(bsr_info)
            price = price.replace(',', '')
        return price

    def get_result_items_selling_points(self, result):
        selling_points_list = self._matching_rule(
            self._get_result_items_selling_points_rule(),
            result
        )
        selling_points = []
        for points in selling_points_list:
            points_info = self._get_value('span/text()', points, 0)
            selling_points.append(points_info.strip() if points_info else points_info)
        return selling_points

    def get_product_overview(self, result):
        product_overview = self._matching_rule(
            self._get_product_overview_rule(),
            result
        )
        product_overview_list = []
        if product_overview:
            feature_table = self._matching_rule(
                self._get_result_items_feature_table_rule(),
                product_overview[0]
            )
            for feature in feature_table:
                feature_name_info = self._get_value('td[1]/span/text()', feature, 0)
                feature_value_info = self._get_value('td[2]/span/text()', feature, 0)
                product_overview_list.append({feature_name_info: feature_value_info})
        return product_overview_list

    def get_result_items_best_seller_rank(self, result):
        bsr_info = self._matching_rule(
            self._get_result_items_best_seller_rank_rule(),
            result,
        )
        best_seller_rank = []
        if bsr_info:
            for info in bsr_info:
                info_list = info.xpath('.//text()')
                rank_info = "".join(info_list)
                best_seller_rank.append(rank_info)
        return best_seller_rank

    def get_result_items_brand(self, result):
        brand_info = self._get_value(self._get_result_items_brand_rule(), result, 0)
        rule1 = re.findall(r'^Brand: (.*)$', brand_info)
        rule2 = re.findall(r'^Visit the (.*) Store$', brand_info.strip())
        if rule1:
            brand_info = rule1[0]
        elif rule2:
            brand_info = rule2[0]
        return brand_info

    def get_result_items_manufacturer(self, result):
        manufacturer = ''
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Manufacturer")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Manufacturer(\\s*:)*(\\s)*$', detail):
                item_element.append(item)
        if item_element:
            # siblings = item_element[0].getparent().getchildren()
            parent = item_element[0].getparent()
            parent_ele = parent
            while parent is not None:
                if parent.tag == 'tr':
                    break
                parent = parent.getparent()
            if parent is None:
                parent = parent_ele
            siblings = parent.iter()
            for sibling in siblings:
                if sibling != item_element:
                    manufacturer = sibling.text
                    manufacturer = manufacturer.replace('\u200e', '').strip()
        return manufacturer

    def get_result_items_coupon_discount(self, result):
        coupon_discount_info = self._matching_rule(
            self._get_result_items_coupon_discount_rule(),
            result,
        )
        if not coupon_discount_info:
            return ''
        coupon_discount_info = coupon_discount_info[0]
        coupon_discount = re.findall(r'Apply (.*) coupon', coupon_discount_info.strip())
        if coupon_discount:
            coupon_discount = coupon_discount[0]
        else:
            coupon_discount = ''
        return coupon_discount

    def get_used_coupon_price(self, price, coupon_discount):
        if not price:
            return price
        used_coupon_price = None
        pure_price = price.replace('$', '').strip()
        if '%' in coupon_discount:
            discount = coupon_discount.replace('%', '').strip()
            used_coupon_price = float(pure_price) * (1 - float(discount)/100)
            used_coupon_price = '$' + str(round(used_coupon_price, 2))
        elif '$' in coupon_discount:
            discount = coupon_discount.replace('$', '').strip()
            used_coupon_price = float(pure_price) - float(discount)
            used_coupon_price = '$' + str(round(used_coupon_price, 2))

        return used_coupon_price

    def get_result_items_delivery_date(self, result):
        # 更改新的规则，分别获取
        free_delivery_date = self._get_value(self._get_result_items_free_delivery_date_rule(), result, 0)
        fastest_delivery_date = self._get_value(self._get_result_items_fastest_delivery_date_rule(), result, 0)
        return {'free': free_delivery_date, 'fastest': fastest_delivery_date}

    def get_result_items_amazon_choice(self, result):
        amazon_choice = self._get_value(self._get_result_items_amazon_choice_rule(), result, 0)
        if value_of_empty(amazon_choice) is False:
            is_amazon_choice = True
        else:
            is_amazon_choice = False
        return is_amazon_choice

    def get_result_items_deal(self, result):
        deal = self._get_value(self._get_result_items_amazon_choice_rule(), result, 0)
        if value_of_empty(deal) is False:
            is_deal = True
        else:
            is_deal = False
        return is_deal

    def get_deal_type(self, result):
        """
        获取活动的类型
        """
        light_deal = self._get_value(self._get_result_items_light_deal_rule(), result, 0)
        if value_of_empty(light_deal) is False:
            deal_type = 'light_deal'
        else:
            deal_type = 'best_deal'

        return deal_type

    def get_result_items_stars(self, result):
        """
        获取评分
        """
        stars_info = self._get_value(self._get_result_items_stars_rule(), result, 0)
        if not stars_info:
            return None
        stars = stars_info.split(' ')[0]
        stars = stars.replace(',', '.')
        return stars

    def get_result_items_ratings(self, result):
        """
        获取评论数
        """
        rating_info = self._get_value(self._get_result_items_ratings_rule(), result, 0)
        if not rating_info:
            return None
        rating = rating_info.split(' ')[0]
        rating = rating.replace(',', '').replace('.', '').replace(' ', '')
        return rating

    def get_result_items_seller(self, result):
        """
        获取卖家
        """
        seller = self._get_value(self._get_result_items_seller_rule_base(), result, 0)
        if not seller:
            seller = self._get_value(self._get_result_items_seller_rule(), result, 0)
        return seller

    def get_result_item_model_number(self, result):
        """
        获取产品型号
        """
        model_number = None
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Item model number")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Item model number(\\s*:)*(\\s)*$', detail):
                item_element.append(item)
        if item_element:
            siblings = item_element[0].getparent().getchildren()
            for sibling in siblings:
                if sibling != item_element:
                    model_number = sibling.text
                    model_number = model_number.replace('\u200e', '').strip()
        return model_number

    def get_result_items_seller_id(self, result):
        """
        获取卖家id
        """
        href = self._get_value(self._get_result_items_seller_id_rule(), result, 0)
        if not href:
            return None
        seller_id = re.findall("seller=([0-9A-Za-z]+)&", href)
        seller_id = seller_id[0] if seller_id else None
        return seller_id
