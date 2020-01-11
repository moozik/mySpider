# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import csv
import time
import datetime
from scrapy import signals
from scrapy.exporters import CsvItemExporter

class ZorosenPipeline(object):
    def __init__(self):
        self.files = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        file = open('{}_{}.csv'.format(
            spider.name,
            #datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d')
            time.strftime("%Y%m%d%H%M%S", time.localtime())
            )
            , 'w+b')
        self.files[spider] = file
        self.exporter = CsvItemExporter(file)
        self.exporter.fields_to_export = ['brand',
        'name',
        'zoro_sku',
        'mfr',
        'selling_price',
        'in_stock',
        'dcs',
        'minOrderQuantity',
        'image1',
        'image2',
        'details',
        'description']
        self.exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        file = self.files.pop(spider)
        file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item
