# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field

class ZorosenItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    brand = Field()
    name = Field()
    zoro_sku = Field()
    mfr = Field()

    selling_price = Field()
    in_stock = Field()
    dcs = Field()
    minOrderQuantity = Field()

    image1 = Field()
    image2 = Field()
    details = Field()
    description = Field()
