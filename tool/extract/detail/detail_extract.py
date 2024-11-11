#!/usr/bin/python
# -*- coding: utf-8 -*-
from tool.extract.detail.extract_base import DetailExtractBase
from common.helpers import get_dynamic_class
from common.exceptions.exception import SystemException
import re


class UsExtract(DetailExtractBase):
    """
    美国站点【其他和美国规则相似的可继承该类】
    """
    def _get_image_result_main_image_rule(self):
        return super(UsExtract, self)._get_image_result_main_image_rule()

    def _get_image_result_small_image_list_rule(self):
        return super(UsExtract, self)._get_image_result_small_image_list_rule()

    def _get_image_result_small_image_rule(self):
        return super(UsExtract, self)._get_image_result_small_image_rule()

    def _get_result_items_title_rule(self):
        return super(UsExtract, self)._get_result_items_title_rule()

    def _get_result_items_list_price_rule(self):
        return super(UsExtract, self)._get_result_items_list_price_rule()

    def _get_result_items_discount_type_rule(self):
        return super(UsExtract, self)._get_result_items_discount_type_rule()

    def _get_result_items_discount_price_rule(self):
        return super(UsExtract, self)._get_result_items_discount_price_rule()

    def _get_result_items_saving_percentage_rule(self):
        return super(UsExtract, self)._get_result_items_saving_percentage_rule()

    def _get_result_items_price_rule(self):
        return super(UsExtract, self)._get_result_items_price_rule()

    def _get_result_items_erp_rule(self):
        return super(UsExtract, self)._get_result_items_erp_rule()

    def _get_result_items_stars_rule(self):
        return super(UsExtract, self)._get_result_items_stars_rule()

    def _get_result_items_ratings_rule(self):
        return super(UsExtract, self)._get_result_items_ratings_rule()

    def _get_result_items_selling_points_rule(self):
        return super(UsExtract, self)._get_result_items_selling_points_rule()

    def _get_result_items_feature_table_rule(self):
        return super(UsExtract, self)._get_result_items_feature_table_rule()

    def _get_result_items_best_seller_rank_rule(self):
        return super(UsExtract, self)._get_result_items_best_seller_rank_rule()

    def _get_result_items_category_list_rule(self):
        return super(UsExtract, self)._get_result_items_category_list_rule()

    def _get_result_items_seller_rule_base(self):
        return super(UsExtract, self)._get_result_items_seller_rule_base()

    def _get_result_items_seller_rule(self):
        return super(UsExtract, self)._get_result_items_seller_rule()

    def _get_result_items_cart_rule(self):
        return super(UsExtract, self)._get_result_items_cart_rule()

    def _get_result_items_seller_id_rule(self):
        return super(UsExtract, self)._get_result_items_seller_id_rule()


class DeExtract(UsExtract):
    """
    德国站点
    """

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
            price = price.replace('.', '')
            price = price.replace(',', '.')
        return price

    def _get_result_items_seller_rule(self):
        return '//*[@id="merchantInfoFeature_feature_div"]//span[@class="a-size-small offer-display-feature-text-message"]//text()'

    def get_result_items_brand(self, result):
        brand_info = self._get_value(self._get_result_items_brand_rule(), result, 0)
        rule1 = re.findall(r'^Marke: (.*)$', brand_info)
        rule2 = re.findall(r'^Besuche den (.*)-Store$', brand_info.strip())
        if rule1:
            brand_info = rule1[0]
        elif rule2:
            brand_info = rule2[0]
        return brand_info

    def get_result_items_manufacturer(self, result):
        manufacturer = ''
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Hersteller")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Hersteller(\\s*:)*(\\s)*$', detail):
                item_element.append(item)
        if item_element:
            siblings = item_element[0].getparent().getchildren()
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
        coupon_discount = re.findall(r'(.*)-Coupon anwenden', coupon_discount_info.strip())
        if coupon_discount:
            coupon_discount = coupon_discount[0]
        else:
            coupon_discount = ''
        return coupon_discount

    def get_used_coupon_price(self, price, coupon_discount):
        if not price:
            return price
        used_coupon_price = None
        pure_price = price.replace('€', '').replace(',', '.').strip()
        if '%' in coupon_discount:
            discount = coupon_discount.replace('%', '').strip()
            used_coupon_price = float(pure_price) * (1 - float(discount)/100)
            used_coupon_price = '€' + str(round(used_coupon_price, 2))
        elif '€' in coupon_discount:
            discount = coupon_discount.replace('€', '').strip()
            used_coupon_price = float(pure_price) - float(discount)
            used_coupon_price = '€' + str(round(used_coupon_price, 2))

        return used_coupon_price

    def get_result_item_model_number(self, result):
        """
        获取产品型号
        """
        model_number = None
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Modellnummer")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Modellnummer(\\s*:)*(\\s)*$', detail):
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
                    model_number = sibling.text
                    model_number = model_number.replace('\u200e', '').strip()
        return model_number


class GbExtract(UsExtract):
    """
    英国站点
    """
    def _get_result_items_seller_rule(self):
        return '//*[@id="merchantInfoFeature_feature_div"]//span[@class="a-size-small offer-display-feature-text-message"]//text()'

    def get_result_items_coupon_discount(self, result):
        coupon_discount_info = self._matching_rule(
            self._get_result_items_coupon_discount_rule(),
            result,
        )
        if not coupon_discount_info:
            return ''
        coupon_discount_info = coupon_discount_info[0]
        coupon_discount = re.findall(r'Apply (.*) voucher', coupon_discount_info.strip())
        if coupon_discount:
            coupon_discount = coupon_discount[0]
        else:
            coupon_discount = ''
        return coupon_discount

    def get_used_coupon_price(self, price, coupon_discount):
        if not price:
            return price
        used_coupon_price = None
        pure_price = price.replace('£', '').strip()
        if '%' in coupon_discount:
            discount = coupon_discount.replace('%', '').strip()
            used_coupon_price = float(pure_price) * (1 - float(discount)/100)
            used_coupon_price = '£' + str(round(used_coupon_price, 2))
        elif '£' in coupon_discount:
            discount = coupon_discount.replace('£', '').strip()
            used_coupon_price = float(pure_price) - float(discount)
            used_coupon_price = '£' + str(round(used_coupon_price, 2))

        return used_coupon_price


class FrExtract(UsExtract):
    """
    法国站点
    """

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
            price = price.replace('.', '')
            price = price.replace(',', '.')
        return price

    def _get_result_items_seller_rule(self):
        return '//*[@id="merchantInfoFeature_feature_div"]//span[@class="a-size-small offer-display-feature-text-message"]//text()'

    def get_result_items_brand(self, result):
        brand_info = self._get_value(self._get_result_items_brand_rule(), result, 0)
        rule1 = re.findall(r'^Marque : (.*)$', brand_info)
        rule2 = re.findall(r'^Visiter la boutique (.*)$', brand_info.strip())
        if rule1:
            brand_info = rule1[0]
        elif rule2:
            brand_info = rule2[0]
        return brand_info

    def get_result_items_manufacturer(self, result):
        manufacturer = ''
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Fabricant")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Fabricant(\\s*:)*(\\s)*$', detail):
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
        coupon_discount = re.findall(r'Utiliser le coupon de (.*)', coupon_discount_info.strip())
        if coupon_discount:
            coupon_discount = coupon_discount[0]
        else:
            coupon_discount = ''
        return coupon_discount

    def get_used_coupon_price(self, price, coupon_discount):
        if not price:
            return price
        used_coupon_price = None
        pure_price = price.replace('€', '').replace(',', '.').strip()
        if '%' in coupon_discount:
            discount = coupon_discount.replace('%', '').strip()
            used_coupon_price = float(pure_price) * (1 - float(discount)/100)
            used_coupon_price = str(round(used_coupon_price, 2)) + '€'
        elif '€' in coupon_discount:
            discount = coupon_discount.replace('€', '').strip()
            used_coupon_price = float(pure_price) - float(discount)
            used_coupon_price = str(round(used_coupon_price, 2)) + '€'

        return used_coupon_price

    def get_result_item_model_number(self, result):
        """
        获取产品型号
        """
        model_number = None
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Numéro du modèle de l\'article")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Numéro du modèle de l\'article(\\s*:)*(\\s)*$', detail):
                item_element.append(item)
        if item_element:
            siblings = item_element[0].getparent().getchildren()
            for sibling in siblings:
                if sibling != item_element:
                    model_number = sibling.text
                    model_number = model_number.replace('\u200e', '').strip()
        return model_number


class EsExtract(UsExtract):
    """
    西班牙站点
    """

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
            price = price.replace('.', '')
            price = price.replace(',', '.')
        return price

    def _get_result_items_seller_rule(self):
        return '//*[@id="merchantInfoFeature_feature_div"]//span[@class="a-size-small offer-display-feature-text-message"]//text()'

    def get_result_items_brand(self, result):
        brand_info = self._get_value(self._get_result_items_brand_rule(), result, 0)
        rule1 = re.findall(r'^Marca: (.*)$', brand_info)
        rule2 = re.findall(r'^Visita la tienda de (.*)$', brand_info.strip())
        if rule1:
            brand_info = rule1[0]
        elif rule2:
            brand_info = rule2[0]
        return brand_info

    def get_result_items_manufacturer(self, result):
        manufacturer = ''
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Fabricante")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Fabricante(\\s*:)*(\\s)*$', detail):
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
        coupon_discount = re.findall(r'Aplicar cupón de (.*)', coupon_discount_info.strip())
        if coupon_discount:
            coupon_discount = coupon_discount[0]
        else:
            coupon_discount = ''
        return coupon_discount

    def get_used_coupon_price(self, price, coupon_discount):
        if not price:
            return price
        used_coupon_price = None
        pure_price = price.replace('€', '').replace(',', '.').strip()
        if '%' in coupon_discount:
            discount = coupon_discount.replace('%', '').strip()
            used_coupon_price = float(pure_price) * (1 - float(discount)/100)
            used_coupon_price = str(round(used_coupon_price, 2)) + '€'
        elif '€' in coupon_discount:
            discount = coupon_discount.replace('€', '').strip()
            used_coupon_price = float(pure_price) - float(discount)
            used_coupon_price = str(round(used_coupon_price, 2)) + '€'

        return used_coupon_price

    def get_result_item_model_number(self, result):
        """
        获取产品型号
        """
        model_number = None
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Número de producto")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Número de producto(\\s*:)*(\\s)*$', detail):
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
                    model_number = sibling.text
                    model_number = model_number.replace('\u200e', '').strip()
        return model_number


class ItExtract(UsExtract):
    """
    意大利站点
    """

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
            price = price.replace('.', '')
            price = price.replace(',', '.')
        return price

    def _get_result_items_seller_rule(self):
        return '//*[@id="merchantInfoFeature_feature_div"]//span[@class="a-size-small offer-display-feature-text-message"]//text()'

    def get_result_items_brand(self, result):
        brand_info = self._get_value(self._get_result_items_brand_rule(), result, 0)
        rule1 = re.findall(r'^Marca: (.*)$', brand_info)
        rule2 = re.findall(r'^Visita lo Store di (.*)$', brand_info.strip())
        if rule1:
            brand_info = rule1[0]
        elif rule2:
            brand_info = rule2[0]
        return brand_info

    def get_result_items_manufacturer(self, result):
        manufacturer = ''
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Produttore")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Produttore(\\s*:)*(\\s)*$', detail):
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
        coupon_discount = re.findall(r'Applica coupon (.*)', coupon_discount_info.strip())
        if coupon_discount:
            coupon_discount = coupon_discount[0]
        else:
            coupon_discount = ''
        return coupon_discount

    def get_used_coupon_price(self, price, coupon_discount):
        if not price:
            return price
        used_coupon_price = None
        pure_price = price.replace('€', '').replace(',', '.').strip()
        if '%' in coupon_discount:
            discount = coupon_discount.replace('%', '').strip()
            used_coupon_price = float(pure_price) * (1 - float(discount)/100)
            used_coupon_price = str(round(used_coupon_price, 2)) + '€'
        elif '€' in coupon_discount:
            discount = coupon_discount.replace('€', '').strip()
            used_coupon_price = float(pure_price) - float(discount)
            used_coupon_price = str(round(used_coupon_price, 2)) + '€'

        return used_coupon_price

    def get_result_item_model_number(self, result):
        """
        获取产品型号
        """
        model_number = None
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Numero articolo")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Numero articolo(\\s*:)*(\\s)*$', detail):
                item_element.append(item)
        if item_element:
            siblings = item_element[0].getparent().getchildren()
            for sibling in siblings:
                if sibling != item_element:
                    model_number = sibling.text
                    model_number = model_number.replace('\u200e', '').strip()
        return model_number


class PlExtract(UsExtract):
    """
    波兰站点, AC和优惠券未找到匹配项
    """

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
            price = price.replace('.', '')
            price = price.replace(',', '.')
        return price

    def _get_result_items_seller_rule(self):
        return '//*[@id="merchantInfoFeature_feature_div"]//span[@class="a-size-small offer-display-feature-text-message"]//text()'

    def get_result_items_brand(self, result):
        brand_info = self._get_value(self._get_result_items_brand_rule(), result, 0)
        rule1 = re.findall(r'^Marka: (.*)$', brand_info)
        rule2 = re.findall(r'^Odwiedź sklep (.*)$', brand_info.strip())
        if rule1:
            brand_info = rule1[0]
        elif rule2:
            brand_info = rule2[0]
        return brand_info

    def get_result_items_manufacturer(self, result):
        manufacturer = ''
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Producent")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Producent(\\s*:)*(\\s)*$', detail):
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

    def get_result_items_ratings(self, result):
        rating_info = self._get_value(self._get_result_items_ratings_rule(), result, 0)
        if not rating_info:
            return None
        rating = rating_info.split(' ')[-1]
        rating = rating.replace(',', '').replace('.', '').replace(' ', '')
        return rating

    def get_result_item_model_number(self, result):
        """
        获取产品型号
        """
        model_number = None
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Numer części")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Numer części(\\s*:)*(\\s)*$', detail):
                item_element.append(item)
        if item_element:
            siblings = item_element[0].getparent().getchildren()
            for sibling in siblings:
                if sibling != item_element:
                    model_number = sibling.text
                    model_number = model_number.replace('\u200e', '').strip()
        return model_number


class SeExtract(UsExtract):
    """
    瑞典站点
    """
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
            price = price.replace('.', '')
            price = price.replace(',', '.')
        return price

    def _get_result_items_seller_rule(self):
        return '//*[@id="merchantInfoFeature_feature_div"]//span[@class="a-size-small offer-display-feature-text-message"]//text()'

    def get_result_items_brand(self, result):
        brand_info = self._get_value(self._get_result_items_brand_rule(), result, 0)
        rule1 = re.findall(r'^Varumärke: (.*)$', brand_info)
        rule2 = re.findall(r'^Besök (.*) Store$', brand_info.strip())
        if rule1:
            brand_info = rule1[0]
        elif rule2:
            brand_info = rule2[0]
        return brand_info

    def get_result_items_manufacturer(self, result):
        manufacturer = ''
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Tillverkare")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Tillverkare(\\s*:)*(\\s)*$', detail):
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
        coupon_discount = re.findall(r'Använd (.*) kupong', coupon_discount_info.strip())
        if coupon_discount:
            coupon_discount = coupon_discount[0]
        else:
            coupon_discount = ''
        return coupon_discount

    def get_used_coupon_price(self, price, coupon_discount):
        if not price:
            return price
        used_coupon_price = None
        pure_price = price.replace('kr', '').replace(',', '.').strip()
        if '%' in coupon_discount:
            discount = coupon_discount.replace('%', '').strip()
            used_coupon_price = float(pure_price) * (1 - float(discount) / 100)
            used_coupon_price = str(round(used_coupon_price, 2)) + 'kr'
        elif 'kr' in coupon_discount:
            discount = coupon_discount.replace('kr', '').strip()
            used_coupon_price = float(pure_price) - float(discount)
            used_coupon_price = str(round(used_coupon_price, 2)) + 'kr'

        return used_coupon_price

    def get_result_item_model_number(self, result):
        """
        获取产品型号
        """
        model_number = None
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Artikelnummer")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Artikelnummer(\\s*:)*(\\s)*$', detail):
                item_element.append(item)
        if item_element:
            siblings = item_element[0].getparent().getchildren()
            for sibling in siblings:
                if sibling != item_element:
                    model_number = sibling.text
                    model_number = model_number.replace('\u200e', '').strip()
        return model_number


class CaExtract(UsExtract):
    """
    加拿大站点
    """
    pass


class JpExtract(UsExtract):
    """
    日本站点
    """
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

    def _get_result_items_seller_rule(self):
        return '//*[@id="merchantInfoFeature_feature_div"]//span[@class="a-size-small offer-display-feature-text-message"]//text()'

    def get_result_items_brand(self, result):
        brand_info = self._get_value(self._get_result_items_brand_rule(), result, 0)
        rule1 = re.findall(r'^ブランド: (.*)$', brand_info)
        rule2 = re.findall(r'^Philips(.*)のストアを表示$', brand_info.strip())
        if rule1:
            brand_info = rule1[0]
        elif rule2:
            brand_info = rule2[0]
        return brand_info

    def get_result_items_manufacturer(self, result):
        manufacturer = ''
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "メーカー")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*メーカー(\\s*:)*(\\s)*$', detail):
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
        coupon_discount = re.findall(r'(.*) OFFクーポンの適用', coupon_discount_info.strip())
        if coupon_discount:
            coupon_discount = coupon_discount[0]
        else:
            coupon_discount = ''
        return coupon_discount

    def get_used_coupon_price(self, price, coupon_discount):
        if not price:
            return price
        used_coupon_price = None
        # ¥ ￥
        pure_price = price.replace('￥', '').replace(',', '').strip()
        if '%' in coupon_discount:
            discount = coupon_discount.replace('%', '').strip()
            used_coupon_price = float(pure_price) * (1 - float(discount) / 100)
            used_coupon_price = '￥' + str(round(used_coupon_price, 2))
        elif '¥' in coupon_discount or '￥' in coupon_discount:
            discount = coupon_discount.replace('¥', '').replace('￥', '').strip()
            used_coupon_price = float(pure_price) - float(discount)
            used_coupon_price = '￥' + str(round(used_coupon_price, 2))

        return used_coupon_price

    def get_result_items_stars(self, result):
        """
        获取评分
        """
        stars_info = self._get_value(self._get_result_items_stars_rule(), result, 0)
        if not stars_info:
            return None
        stars = re.findall(r'5つ星のうち(.*)', stars_info)
        if stars:
            stars = stars[0]
            stars = stars.replace(',', '.')
        else:
            stars = None
        return stars

    def get_result_items_ratings(self, result):
        """
        获取评论数
        """
        rating_info = self._get_value(self._get_result_items_ratings_rule(), result, 0)
        if not rating_info:
            return None
        rating = re.findall(r'(.*)個の評価', rating_info)
        if rating:
            rating = rating[0]
            rating = rating.replace(',', '').replace('.', '').replace(' ', '')
        else:
            rating = None
        return rating

    def get_result_item_model_number(self, result):
        """
        获取产品型号
        """
        model_number = None
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "製品型番")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*製品型番(\\s*:)*(\\s)*$', detail):
                item_element.append(item)
        if item_element:
            siblings = item_element[0].getparent().getchildren()
            for sibling in siblings:
                if sibling != item_element:
                    model_number = sibling.text
                    model_number = model_number.replace('\u200e', '').strip()
        return model_number


class SgExtract(UsExtract):
    """
    新加坡站点
    """
    def _get_result_items_seller_rule(self):
        return '//*[@id="merchant-info"]/a/span/text()'

    def get_result_items_coupon_discount(self, result):
        coupon_discount_info = self._matching_rule(
            self._get_result_items_coupon_discount_rule(),
            result,
        )
        if not coupon_discount_info:
            return ''
        coupon_discount_info = coupon_discount_info[0]
        coupon_discount = re.findall(r'Apply (.*) voucher', coupon_discount_info.strip())
        if coupon_discount:
            coupon_discount = coupon_discount[0]
        else:
            coupon_discount = ''
        return coupon_discount

    def get_used_coupon_price(self, price, coupon_discount):
        if not price:
            return price
        used_coupon_price = None
        pure_price = price.replace('S$', '').replace(',', '.').strip()
        if '%' in coupon_discount:
            discount = coupon_discount.replace('%', '').strip()
            used_coupon_price = float(pure_price) * (1 - float(discount) / 100)
            used_coupon_price = 'S$' + str(round(used_coupon_price, 2))
        elif 'S$' in coupon_discount:
            discount = coupon_discount.replace('S$', '').strip()
            used_coupon_price = float(pure_price) - float(discount)
            used_coupon_price = 'S$' + str(round(used_coupon_price, 2))

        return used_coupon_price


# 其他暂未在数据库中收录的站点
class NlExtract(UsExtract):
    """
    荷兰站点
    """
    pass


class MxExtract(UsExtract):
    """
    墨西哥站点
    """

    def _get_result_items_seller_rule(self):
        return '//*[@id="merchantInfoFeature_feature_div"]//span[@class="a-size-small offer-display-feature-text-message"]//text()'

    def get_result_items_brand(self, result):
        brand_info = self._get_value(self._get_result_items_brand_rule(), result, 0)
        rule1 = re.findall(r'^Marca: (.*)$', brand_info)
        rule2 = re.findall(r'^Visita la tienda de (.*)$', brand_info.strip())
        if rule1:
            brand_info = rule1[0]
        elif rule2:
            brand_info = rule2[0]
        return brand_info

    def get_result_items_manufacturer(self, result):
        manufacturer = ''
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Fabricante")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Fabricante(\\s*:)*(\\s)*$', detail):
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
        coupon_discount = re.findall(r'Aplica el cupón de (.*)', coupon_discount_info.strip())
        if coupon_discount:
            coupon_discount = coupon_discount[0]
        else:
            coupon_discount = ''
        return coupon_discount

    def get_used_coupon_price(self, price, coupon_discount):
        if not price:
            return price
        used_coupon_price = None
        pure_price = price.replace('$', '').replace(',', '').strip()
        if '%' in coupon_discount:
            discount = coupon_discount.replace('%', '').strip()
            used_coupon_price = float(pure_price) * (1 - float(discount) / 100)
            used_coupon_price = '$' + str(round(used_coupon_price, 2))
        elif '$' in coupon_discount:
            discount = coupon_discount.replace('$', '').strip()
            used_coupon_price = float(pure_price) - float(discount)
            used_coupon_price = '$' + str(round(used_coupon_price, 2))

        return used_coupon_price

    def get_result_item_model_number(self, result):
        """
        获取产品型号
        """
        model_number = None
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Número de modelo del producto")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Número de modelo del producto(\\s*:)*(\\s)*$', detail):
                item_element.append(item)
        if item_element:
            siblings = item_element[0].getparent().getchildren()
            for sibling in siblings:
                if sibling != item_element:
                    model_number = sibling.text
                    model_number = model_number.replace('\u200e', '').strip()
        return model_number


class AuExtract(UsExtract):
    """
    澳大利亚站点
    """
    pass


class InExtract(UsExtract):
    """
    印度站点
    """
    def _get_result_items_seller_rule(self):
        return '//*[@id="merchant-info"]/a[1]/span/text()'

    def get_used_coupon_price(self, price, coupon_discount):
        if not price:
            return price
        used_coupon_price = None
        pure_price = price.replace('₹', '').replace(',', '').strip()
        if '%' in coupon_discount:
            discount = coupon_discount.replace('%', '').strip()
            used_coupon_price = float(pure_price) * (1 - float(discount) / 100)
            used_coupon_price = '₹' + str(round(used_coupon_price, 2))
        elif '₹' in coupon_discount:
            discount = coupon_discount.replace('₹', '').strip()
            used_coupon_price = float(pure_price) - float(discount)
            used_coupon_price = '₹' + str(round(used_coupon_price, 2))

        return used_coupon_price


class AeExtract(UsExtract):
    """
    阿联酋站点
    """

    def get_used_coupon_price(self, price, coupon_discount):
        if not price:
            return price
        used_coupon_price = None
        pure_price = price.replace('AED', '').replace(',', '').strip()
        if '%' in coupon_discount:
            discount = coupon_discount.replace('%', '').strip()
            used_coupon_price = float(pure_price) * (1 - float(discount) / 100)
            used_coupon_price = 'AED' + str(round(used_coupon_price, 2))
        elif 'AED' in coupon_discount:
            discount = coupon_discount.replace('AED', '').strip()
            used_coupon_price = float(pure_price) - float(discount)
            used_coupon_price = 'AED' + str(round(used_coupon_price, 2))

        return used_coupon_price


class SaExtract(UsExtract):
    """
    沙特阿拉伯站点
    """

    def _get_result_items_seller_rule(self):
        return '//*[@id="merchantInfoFeature_feature_div"]//span[@class="a-size-small offer-display-feature-text-message"]//text()'

    def get_result_items_brand(self, result):
        brand_info = self._get_value(self._get_result_items_brand_rule(), result, 0)
        # قم بزيارة متجر بلاك اند ديكر
        # قم بزيارة متجر اميناك
        rule1 = re.findall(r'^العلامة التجارية: (.*)$', brand_info)
        rule2 = re.findall(r'^قم بزيارة متجر (.*)$', brand_info.strip())
        if rule1:
            brand_info = rule1[0]
        elif rule2:
            brand_info = rule2[0]
        return brand_info

    def get_result_items_manufacturer(self, result):
        manufacturer = ''
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "الشركة المصنعة")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*الشركة المصنعة(\\s*:)*(\\s)*$', detail):
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
        coupon_discount = re.findall(r'تطبيق ‏(.*) كوبون', coupon_discount_info.strip())
        if coupon_discount:
            coupon_discount = coupon_discount[0]
        else:
            coupon_discount = ''
        return coupon_discount

    def get_used_coupon_price(self, price, coupon_discount):
        if not price:
            return price
        used_coupon_price = None
        pure_price = price.replace('ريال', '').replace(',', '').replace('\u200e', '').strip()
        if '%' in coupon_discount:
            discount = coupon_discount.replace('%', '').strip()
            used_coupon_price = float(pure_price) * (1 - float(discount) / 100)
            used_coupon_price = '$' + str(round(used_coupon_price, 2))
        elif 'ريال' in coupon_discount:
            discount = coupon_discount.replace('ريال', '').strip()
            used_coupon_price = float(pure_price) - float(discount)
            used_coupon_price = 'ريال' + str(round(used_coupon_price, 2))

        return used_coupon_price

    def get_result_item_model_number(self, result):
        """
        获取产品型号
        """
        model_number = None
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "رقم موديل السلعة")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*رقم موديل السلعة(\\s*:)*(\\s)*$', detail):
                item_element.append(item)
        if item_element:
            siblings = item_element[0].getparent().getchildren()
            for sibling in siblings:
                if sibling != item_element:
                    model_number = sibling.text
                    model_number = model_number.replace('\u200e', '').strip()
        return model_number


class EgExtract(SaExtract):
    """
    埃及站点， 数据库内暂时未有信息
    """

    def get_used_coupon_price(self, price, coupon_discount):
        if not price:
            return price
        used_coupon_price = None
        pure_price = price.replace('جنيه', '').replace(',', '').replace('\u200e', '').strip()
        if '%' in coupon_discount:
            discount = coupon_discount.replace('%', '').strip()
            used_coupon_price = float(pure_price) * (1 - float(discount) / 100)
            used_coupon_price = '$' + str(round(used_coupon_price, 2))
        elif 'جنيه' in coupon_discount:
            discount = coupon_discount.replace('جنيه', '').strip()
            used_coupon_price = float(pure_price) - float(discount)
            used_coupon_price = 'جنيه' + str(round(used_coupon_price, 2))

        return used_coupon_price


class TrExtract(UsExtract):
    """
    土尔其站点， 数据库内暂时未有信息
    """
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
            price = price.replace('.', '')
            price = price.replace(',', '.')
        return price

    def _get_result_items_seller_rule(self):
        return '//*[@id="tabular-buybox"]//div[@class="tabular-buybox-text" and @tabular-attribute-name="Satıcı"]/div/span//text()'

    def get_result_items_brand(self, result):
        brand_info = self._get_value(self._get_result_items_brand_rule(), result, 0)
        rule1 = re.findall(r'^Marka: (.*)$', brand_info)
        rule2 = re.findall(r'^(.*) Store’u ziyaret edin$', brand_info.strip())
        if rule1:
            brand_info = rule1[0]
        elif rule2:
            brand_info = rule2[0]
        return brand_info

    def get_result_items_manufacturer(self, result):
        manufacturer = ''
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Üretici")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Üretici(\\s*:)*(\\s)*$', detail):
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
        coupon_discount = re.findall(r'(.*) kuponunu uygula', coupon_discount_info.strip())
        if coupon_discount:
            coupon_discount = coupon_discount[0]
        else:
            coupon_discount = ''
        return coupon_discount

    def get_used_coupon_price(self, price, coupon_discount):
        if not price:
            return price
        used_coupon_price = None
        pure_price = price.replace('TL', '').replace(',', '.').strip()
        if '%' in coupon_discount:
            discount = coupon_discount.replace('%', '').strip()
            used_coupon_price = float(pure_price) * (1 - float(discount) / 100)
            used_coupon_price = str(round(used_coupon_price, 2)) + 'TL'
        elif 'TL' in coupon_discount:
            discount = coupon_discount.replace('TL', '').strip()
            used_coupon_price = float(pure_price) - float(discount)
            used_coupon_price = str(round(used_coupon_price, 2)) + 'TL'

        return used_coupon_price

    def get_result_item_model_number(self, result):
        """
        获取产品型号
        """
        model_number = None
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Ürün Model Numarası")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Ürün Model Numarası(\\s*:)*(\\s)*$', detail):
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
                    model_number = sibling.text
                    model_number = model_number.replace('\u200e', '').strip()
        return model_number


class BrExtract(UsExtract):
    """
    巴西站点
    """
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
            price = price.replace('.', '')
            price = price.replace(',', '.')
        return price

    def _get_result_items_seller_rule(self):
        return '//*[@id="merchantInfoFeature_feature_div"]//span[@class="a-size-small offer-display-feature-text-message"]//text()'

    def get_result_items_brand(self, result):
        brand_info = self._get_value(self._get_result_items_brand_rule(), result, 0)
        rule1 = re.findall(r'^Marca: (.*)$', brand_info)
        rule2 = re.findall(r'^Visita la tienda de (.*)$', brand_info.strip())
        if rule1:
            brand_info = rule1[0]
        elif rule2:
            brand_info = rule2[0]
        return brand_info

    def get_result_items_manufacturer(self, result):
        manufacturer = ''
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Fabricante")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Fabricante(\\s*:)*(\\s)*$', detail):
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
        coupon_discount = re.findall(r'Aplicar Cupom de (.*)', coupon_discount_info.strip())
        if coupon_discount:
            coupon_discount = coupon_discount[0]
        else:
            coupon_discount = ''
        return coupon_discount

    def get_used_coupon_price(self, price, coupon_discount):
        if not price:
            return price
        used_coupon_price = None
        pure_price = price.replace('R$', '').replace(',', '.').strip()
        if '%' in coupon_discount:
            discount = coupon_discount.replace('%', '').strip()
            used_coupon_price = float(pure_price) * (1 - float(discount) / 100)
            used_coupon_price = 'R$' + str(round(used_coupon_price, 2))
        elif 'R$' in coupon_discount:
            discount = coupon_discount.replace('R$', '').strip()
            used_coupon_price = float(pure_price) - float(discount)
            used_coupon_price = 'R$' + str(round(used_coupon_price, 2))

        return used_coupon_price

    def get_result_item_model_number(self, result):
        """
        获取产品型号
        """
        model_number = None
        item_element = []
        # 由于html页面可能存在特殊字符xpath无法识别，所以先获取所有符合规则的再通过正则去匹配
        base_item_element = result.xpath('//*[contains(text(), "Número do modelo")]')
        for item in base_item_element:
            detail = item.xpath('./text()')[0]
            detail = detail.replace('‏', '').replace('‎', '')
            if re.match('^\\s*Número do modelo(\\s*:)*(\\s)*$', detail):
                item_element.append(item)
        if item_element:
            siblings = item_element[0].getparent().getchildren()
            for sibling in siblings:
                if sibling != item_element:
                    model_number = sibling.text
                    model_number = model_number.replace('\u200e', '').strip()
        return model_number


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
        class_str = f'tool.extract.detail.detail_extract.{country.capitalize()}Extract'
        # tool.extract.detail.detail_extract.MxExtract
        class_obj = get_dynamic_class(class_str)
        if not class_obj:
            raise SystemException('The parse class does not exist:' + class_str)
        self.extract_handle = class_obj(content)

    def get_image_result(self):
        """
        获取图片结果
        :return:
        """
        return self.extract_handle.get_image_result()

    def get_result(self):
        """
        获取结果
        :return:
        """
        return self.extract_handle.get_result()

    def __getattr__(self, item):
        """
        方法不存在时调用
        :params item:
        :return:
        """
        if getattr(self.extract_handle, item):
            return getattr(self.extract_handle, item)
