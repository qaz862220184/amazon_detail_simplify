# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class CommodityItem(scrapy.Item):
    result = scrapy.Field()
    image_result = scrapy.Field()
