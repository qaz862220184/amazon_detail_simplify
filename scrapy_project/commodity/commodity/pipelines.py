#!/usr/bin/python
# -*- coding: utf-8 -*-
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from common.core.mongodb.mongo import MongoDb
from common.utils.date_time import ScrapyDateTimeManage
from tool.delivery.site_date import Delivery
from abc import ABCMeta, abstractmethod
from common.helpers import get_dynamic_class, bool_to_int
from common.utils.distribution_lock import RedisLock
from datetime import datetime


def get_utc_time():
    """
    获取utc时间
    :return:
    """
    res = ScrapyDateTimeManage.date_time().date_time()
    return datetime.strptime(res, "%Y-%m-%d %H:%M:%S")


class CommodityPipeline:
    def __init__(self):
        self.lock_time = 30
        self.lock = RedisLock(
            lock_name='commodity',
            lock_timeout=self.lock_time
        )

    def process_item(self, item, spider):
        """
        :param item:
        :param spider:
        :return:
        """
        class_str = f"commodity.pipelines.{spider.name.capitalize()}PipelineHandle"
        # class_str = 'commodity.pipelines.CommodityPipelineHandle'
        class_obj = get_dynamic_class(class_str)
        if not class_obj:
            raise Exception(f"class does not exist:{class_str}")
        # 处理
        obj = class_obj(item, spider)

        # 加锁
        identifier = self.lock.acquire_lock(
            acquire_timeout=self.lock_time
        )
        try:
            if obj.handle():
                # 成功
                spider.set_execute_status(
                    status=spider.EXECUTE_STATUS_SUCCESS
                )
        except Exception as exception:
            # 发生错误
            raise exception
        finally:
            # 解锁
            self.lock.release_lock(
                identifier=identifier
            )


class BasePipelineHandle(metaclass=ABCMeta):

    table = ''

    def __init__(self, item, spider):
        """
        初始化
        :param item:
        :param spider:
        """
        self.item = item
        self.spider = spider

    @abstractmethod
    def handle(self):
        """
        处理函数
        :return:
        """
        pass


class GoodsTitlePipelineHandle:
    """
    商品详情扩展建立独立表
    """
    TYPE_COMMODITY_DETAIL = 3
    table = "detail_info_extend"

    def __init__(self, types=3):
        self.type = types
        self.extend = {}

    def append_extend(self, extend):
        """
        追加扩展信息
        :param extend: dict
        :return:
        """
        self.extend = extend
        return self

    def save(self, result):
        """
        保存数据
        :param result:
        :return:
        """
        if getattr(result, "inserted_id"):
            _id = result.inserted_id
            results = {
                # 'type': self.type,
                "basic_id": str(_id),
            }
            results.update(self.extend)
            MongoDb.table(self.table, "brand").insert_one(results)
            return True
        return False


class DetailSignPipelineHandle:
    """
    商品详情状态标识建立独立表
    """
    table = "detail_info_sign"

    def __init__(self):
        self.extend = {}

    def append_info(self, extend):
        """
        追加扩展信息
        :param extend: dict
        :return:
        """
        self.extend = extend
        return self

    def save(self, result):
        """
        保存数据
        :param result:
        :return:
        """
        if getattr(result, "inserted_id"):
            _id = result.inserted_id
            # 这里开始处理判断标识
            sign_list = self.get_sign_list(self.extend)
            results = {
                "basic_id": str(_id),
                "sub_task_id": self.extend.get("sub_task_id"),
            }
            for sign in sign_list:
                data = dict(results, **sign)
                MongoDb.table(self.table, "brand").insert_one(data)
            return True
        return False

    @classmethod
    def get_sign_list(cls, info):
        sign_list = []
        # 购物车
        cart_status = 1 if info.get("is_cart") else 0
        sign_list.append({"type": 1, "status": cart_status, "value": info.get("is_cart")})
        # amazon choice
        ac_status = 1 if info.get("is_amazon_choice") else 0
        sign_list.append({"type": 2, "status": ac_status, "value": info.get("amazon_choice_keywords")})
        # 划线价格
        price_status = 1 if info.get("original_price").get("discount_type") else 0
        sign_list.append({"type": 3, "status": price_status, "value": info.get("original_price")})
        # 优惠券
        coupon_status = 1 if info.get("is_coupon") else 0
        sign_list.append({"type": 4, "status": coupon_status, "value": info.get("coupon_discount")})
        return sign_list


class DetailPipelineHandle(BasePipelineHandle):
    """
    商品详情页数据
    """

    table = "detail_info_basic"
    image_table = "detail_image_result"

    def handle(self):
        """
        处理
        :return:
        """
        self.save_by_image()
        self.save_by_detail()
        return True

    def save_by_image(self):
        """
        保存商品图片信息
        """
        if "image_result" in self.item and self.item["image_result"]:
            # 处理图片
            image_result = self.item["image_result"]
            image_sql = {}

            if "item" in image_result and image_result["item"]:
                # 图片数据
                item = image_result["item"]
                image_sql = {
                    "alt_images": item["alt_images"],
                    "main_image": item["main_image"],
                    "sub_task_id": self.spider.sub_task_id,
                    "created_at": get_utc_time(),
                }

            if image_sql:
                # 看是否要添加_id
                MongoDb.table(self.image_table, "brand").insert_one(image_sql)

    def save_by_detail(self):
        """
        保存商品主体信息
        :return:
        """
        if "result" in self.item and self.item["result"]:
            # 处理主体信息
            result = self.item["result"]
            sql = {}
            extend_sql = {}
            sign_sql = {}
            if "item" in result and result["item"]:
                # 获取handle_data
                handle_data = self.spider.subtask_handle_data
                expected_execution_time = self.spider.subtask['created_at']
                item = result["item"]
                is_cart = bool_to_int(item["is_cart"])
                is_coupon = bool_to_int(item["is_coupon"])
                is_amazon_choice = bool_to_int(item["is_amazon_choice"])
                is_deal = bool_to_int(item["is_deal"])
                # 新增一个字段计算送达时间
                delivery_days = Delivery(handle_data["country_code"], item["delivery_date"]).get_delivery_days()
                # 将handle_data中的数据全部取出来
                temp = "handle_"
                handle_sql = {temp + str(key): val for key, val in handle_data.items()}
                sql = {
                    "country_code": handle_data["country_code"],
                    # "need_id": handle_data.get("need_id"),
                    # "shop_id": handle_data.get("shop_id"),
                    "asin": handle_data.get("asin"),

                    "brand": item["brand"],
                    "saving_percentage": item["saving_percentage"],
                    "price": item["price"],
                    "seller": item["seller"],
                    "manufacturer": item["manufacturer"],
                    # "used_coupon_price": item["used_coupon_price"],
                    "delivery_date": item["delivery_date"],
                    "delivery_days": delivery_days,
                    "is_deal": is_deal,
                    "deal_type": item["deal_type"],
                    "end_time": item["end_time"],
                    "stars": item["stars"],
                    "rating": item["rating"],
                    "sales_volume": item["sales_volume"],
                    "model_number": item["model_number"],
                    "seller_id": item["seller_id"],

                    "sub_task_id": self.spider.sub_task_id,
                    "created_at": get_utc_time(),
                    "expected_execution_time": expected_execution_time,
                }
                sql = dict(sql, **handle_sql)

                extend_sql = {
                    "title": item["title"],
                    "selling_points": item["selling_points"],
                    "product_overview": item["product_overview"],

                    # "category_info": item["category_info"],
                    # "best_seller_rank": item["best_seller_rank"],
                    # "stars": item["stars"],
                }

                sign_sql = {
                    "is_cart": is_cart,
                    "original_price": item["original_price"],
                    "is_coupon": is_coupon,
                    "coupon_discount": item["coupon_discount"],
                    "is_amazon_choice": is_amazon_choice,
                    "amazon_choice_keywords": item["amazon_choice_keywords"],
                    "sub_task_id": self.spider.sub_task_id,
                }

            if sql:
                self._save(sql, extend_sql, sign_sql, self.table)

    @classmethod
    def _save(cls, sqls, extend_sqls, sign_sql, table):
        """
        保存数据
        :param sqls:
        :param table:
        :return:
        """
        goods_titles = GoodsTitlePipelineHandle()
        detail_sign = DetailSignPipelineHandle()
        item = sqls
        result = MongoDb.table(table, "brand").insert_one(item)
        # 处理一下另一张表
        goods_titles.append_extend(extend_sqls)
        goods_titles.save(result)
        # 处理下标记表
        detail_sign.append_info(sign_sql)
        detail_sign.save(result)
        return True
