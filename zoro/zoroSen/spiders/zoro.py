import scrapy
import json
import os
import re
from scrapy.spiders import Spider
from scrapy.http import FormRequest
from scrapy.http import Request
from zoroSen.items import ZorosenItem
from lxml import html
#import usaddress
#import pdb
import tokenize
import token
import logging
from html import unescape
# from StringIO import StringIO
from io import StringIO
import requests


class ZoroSpider(scrapy.Spider):
	name = 'zoro'
	domain = 'https://www.zoro.com'
	start_urls = ['https://www.zoro.com/']
	allkind = [
		'/fall-protection-facility-traffic-safety-equipment/c/14/',
		'/gloves-eyewear-ear-protection-masks-clothing/c/13/',
		'/padlocks-lockouttagout-security-equipment/c/28/',
		'/signs-labels/c/29/',
		'/test-instruments-gauges/c/24/',
		'/abrasives-polishers/c/1/',
		'/cutting-holemaking-shaping-tools/c/2/',
		'/hand-tools/c/10/',
		'/knobs-handles-workholding-machine-tool-accessories/c/8/',
		'/power-tools-and-accessories/c/11/',

		'/raw-materials/c/37/',
		'/fans-hvac-equipment/c/30/',
		'/pipes-valves-fittings/c/33/',
		'/pumps/c/39/',
		'/toilets-sinks-faucets-plumbing-supplies/c/34/',
		'/carts-trucks-casters/c/16/',
		'/drum-dock-equipment/c/18/',
		'/mng-equipment-pulling-lifting-lowering-conveying/c/17/',
		'/storage-shelving-ladders-lifts/c/15/',
		'/electrical-supplies-generators/c/23/',
		'/lighting-flashlights-batteries/c/22/',
		'/adhesives-sealants/c/4/',
		'/fasteners/c/9/',
		'/tapes-electrical-duct-painters/c/5/',
		'/welding-soldering-equipment-supplies/c/6/',
		'/door-and-cabinet-hinges-hardware/c/27/',
		'/grounds-maintenance-outdoor-equipment/c/21/',
		'/janitorial-cleaning-supplies/c/25/',
		'/paint-coatings-supplies/c/26/',
		'/auto-truck-maintenance/c/36/',
		'/bearings-v-belts-power-transmission-equipment/c/31/',
		'/compressors-air-tanks-pneumatic-tools/c/12/',
		'/fluids-lubricants/c/3/',
		'/hydraulic-cylinders-equipment/c/32/',
		'/motors/c/38/',
		'/office-supplies-furniture-breakroom-supplies/c/19/',
		'/shipping-packing-supplies/c/20/',
		'/safety-security/',
		'/fall-protection-facility-traffic-safety-equipment/c/14/',
		'/gloves-eyewear-ear-protection-masks-clothing/c/13/',
		'/padlocks-lockouttagout-security-equipment/c/28/',
		'/signs-labels/c/29/',
		'/test-instruments-gauges/c/24/',
		'/tools-machining/',
		'/abrasives-polishers/c/1/',
		'/cutting-holemaking-shaping-tools/c/2/',
		'/hand-tools/c/10/',
		'/knobs-handles-workholding-machine-tool-accessories/c/8/',
		'/power-tools-and-accessories/c/11/',
		'/raw-materials/c/37/',
		'/plumbing-hvac/',
		'/fans-hvac-equipment/c/30/',
		'/pipes-valves-fittings/c/33/',
		'/pumps/c/39/',
		'/toilets-sinks-faucets-plumbing-supplies/c/34/',
		'/material-handling/',
		'/carts-trucks-casters/c/16/',
		'/drum-dock-equipment/c/18/',
		'/mng-equipment-pulling-lifting-lowering-conveying/c/17/',
		'/storage-shelving-ladders-lifts/c/15/',
		'/electrical-lighting/',
		'/electrical-supplies-generators/c/23/',
		'/lighting-flashlights-batteries/c/22/',
		'/adhesives-fasteners-welding/',
		'/adhesives-sealants/c/4/',
		'/fasteners/c/9/',
		'/tapes-electrical-duct-painters/c/5/',
		'/welding-soldering-equipment-supplies/c/6/',
		'/janitorial-grounds-maintenance/',
		'/door-and-cabinet-hinges-hardware/c/27/',
		'/grounds-maintenance-outdoor-equipment/c/21/',
		'/janitorial-cleaning-supplies/c/25/',
		'/paint-coatings-supplies/c/26/',
		'/power-transmission-pneumatics/',
		'/auto-truck-maintenance/c/36/',
		'/bearings-v-belts-power-transmission-equipment/c/31/',
		'/compressors-air-tanks-pneumatic-tools/c/12/',
		'/fluids-lubricants/c/3/',
		'/hydraulic-cylinders-equipment/c/32/',
		'/motors/c/38/',
		'/office-shipping/',
		'/office-supplies-furniture-breakroom-supplies/c/19/',
		'/shipping-packing-supplies/c/20/'
	]

	# https://www.zoro.com
	# 获取所有小分类
	def parse(self, response):

		#数据修复
		# for itemUrl in self.pages:
		# 	yield scrapy.Request(url=itemUrl, callback=self.parse_list)
		# return
		# kind_list = response.xpath('//div[@class="category-level-0-box-group"]//a/@href').extract()
		kind_list = response.xpath(
			'//li[@class="sub-menu__item"]//a/@href').extract()
		# i=0
		for kind in kind_list:
			# if kind in self.allkind and self.allkind.index(kind) < 10:
			# 	continue
			print('parse:', kind)
			kind = self.domain + kind
			yield scrapy.Request(url=kind, callback=self.parse_block)
			# i+=1	
			# 测试限流
			# if i == 20:
				# break
	# 小分类列表页
	# https://www.zoro.com/fall-protection-facility-traffic-safety-equipment/c/14/

	def parse_block(self, response):
		# block_list  = response.xpath('//div[contains(@class, "col-extra-padding")]//h4[@class="header"]//a/@href').extract()
		# block_list = response.xpath('//section[@class="l1-popular-categories"]/div/ul/li[last()]/a/@href').extract()
		block_list = response.xpath(
			'//*[@id="part_content"]/div/main/div/div/section/div/ul/li[1]/a/@href').extract()
		if len(block_list) == 0:
			block_list = response.xpath(
				'//div[@class="container cms-container"]/div/div/div/h4/a/@href').extract()
		for block in block_list:
			print('parse_block:', block)
			# if block.rstrip('/') not in self.catePage:
			# 	continue
			# print(block)
			#发现多层目录结构，开始套娃
			if int(re.findall('\d+', block)[0]) < 100:
				yield scrapy.Request(url=self.domain + block, callback=self.parse_block)
				continue
			block = self.domain + block.rstrip('/') + '/'
			yield scrapy.Request(url=block, callback=self.parse_category)
			# 测试限流
			# break
	# 小分类商品列表页
	# https://www.zoro.com/fall-protection/c/4463

	def parse_category(self, response):
		# limit = response.xpath('//div[@class="category-pagination"]/ul[last()]/li/a/text()').extract()[-1:][0]
		limitList = response.xpath(
			'//div[@class="category-pagination"]/ul/li/a/text()').extract()
		if len(limitList) == 0:
			limit = 1
		else:
			limit = [x for x in limitList if x.isnumeric()][-1:][0]
		for page in range(1, int(limit) + 1):
			listUrl = '{}?page={}'.format(response.url, page)
			# if listUrl not in self.pages:
			# 	continue
			# print(listUrl)
			yield scrapy.Request(url=listUrl, callback=self.parse_list)
			# 测试限流
			# if page > 1:
				# break

	# 列表页分页
	# https://www.zoro.com/fall-protection/c/4463/?page=2
	def parse_list(self, response):

		#data = response.body.decode('utf-8').split('id="search-raw-response" data-search-response="')[1].strip().split('"></div>')[0].strip()
		#data = unescape(data)#.replace('&quot;',"'").replace('amp;','')

		#variantList = [re.findall('^G\d+', x)[0] for x in data.split('variantid: ')[1:]]
		#slugList = [re.findall('^[\da-z\-]+', x)[0] for x in data.split('slug: ')[1:]]

		scriptCode = response.xpath('//body//script[1]/text()').extract_first()

		# 链接
		url = re.findall('"url": "(/[^/]+/i/G\d+/)"', scriptCode)
		# 仓库
		dropship = re.findall('"dropship": "([A-Z0-9]*?)"', scriptCode)
		brand = re.findall('"brand": "(.*?)"', scriptCode)
		price = re.findall('"price": "([\d\.]*?)"', scriptCode)
		# skuid
		variantid = re.findall('"id": "(G\d+)"', scriptCode)
		# 最少购买数量
		minOrderQuantity = re.findall('"minOrderQuantity": (\d+)', scriptCode)

		# name = re.findall('"name": "(.*?)"', scriptCode)
		mfr_no = re.findall('"mfrNo": "(.*?)"', scriptCode)
		if len(price) != len(url):
			print('price length erong:',response.url)
			logging.info(response.url)
			logging.info(scriptCode)
		ret = []
		# for variantid in variantList:
		for i in range(len(variantid)):
			# 第三方商品不抓取
			if dropship[i] == 'TP':
				continue
			ret.append([
				url[i],
				dropship[i],
				brand[i],
				price[i],
				variantid[i],
				mfr_no[i],
				minOrderQuantity[i]
			])
		if ret == []:
			return
		
		# 获取库存信息
		postData = str([x[4] for x in ret]).replace("'",'"')
		# avlResponse = scrapy.Request(url=self.domain + '/avl/', method="POST", formdata=postData)
		#jsonList = scrapy.http.JsonRequest(url='https://www.zoro.com/avl/',callback=self.parse_json, method="POST", body=postData)
		# avlResponse = scrapy.Request(url='https://www.zoro.com/avl/', method="POST", body=postData, headers={'Content-Type': 'application/json'})
		r = requests.post('https://www.zoro.com/avl/', data=postData)
		if r.status_code != 200 or r.text.strip() == '':
			r = requests.post('https://www.zoro.com/avl/', data=postData)
		jsonList = r.json()
		
		for item in ret:
			# 拼接商品详情页链接
			productUrl = self.domain + item[0]
			# productUrl = self.domain + '/i/' + variantid + '/'
			item.append(jsonList[item[4]][2])
			yield scrapy.Request(url=productUrl, callback=self.parse_product, meta={'o':item})
	
	# 商品详情页
	# G0024175 R
	# G5398662 TM
	# G4539202

	#价格下面带一句话的都不要
	#ZORO #: G2034477
	#ZORO #: G0714609
	# https://www.zoro.com/3m-protecta-shock-absorbing-lanyard-6-ft-310-lb-1340220/i/G3695133/
	def parse_product(self, response):
		try:
			# 价格下带有标识的商品忽略
			# product_warning = response.xpath('//*[@id="part_content"]/div/div[1]/div[4]/p').extract_first()
			# if product_warning != None:
			# 	return
			item = ZorosenItem()
			# item['brand'] = self.validate(response.xpath(
			# 	'//a[@data-za="product-brand-name"]/text()').extract_first())
			item['brand'] = response.meta['o'][2]
			item['name'] = self.validate(response.xpath(
				'//*[@id="part_content"]/div/div[1]/div[2]/h1/text()').extract_first())
			if item['name'] == '':
				print('empty name:', response.url)
				return
			item['dcs'] = response.meta['o'][7]
			item['minOrderQuantity'] = response.meta['o'][6]
			item['zoro_sku'] = response.meta['o'][4]
			if item['zoro_sku'] == '':
				print('empty zoro_sku:', response.url)
				return
			# item['mfr'] = self.validate(response.xpath(
			# 	'//*[@id="part_content"]/div/div[1]/ul/li[2]/span/text()').extract_first())
			item['mfr'] = response.meta['o'][5]
			# item['selling_price'] = self.validate(response.xpath(
			# 	'//*[@id="part_content"]/div/div[1]/div[4]/h3/span/text()').extract_first())
			item['selling_price'] = response.meta['o'][3]
			if item['selling_price'] == '':
				print('empty selling_price:', response.url)
				return
			
			# "dropship": 
			# TP = Drop ship 第三方仓库
			# ST = In stock
			details = response.xpath(
				'//ul[@class="product-details__list"]/li//text()').extract()
			item['details'] = '; '.join([details[x]+details[x+1] for x in range(0, len(details), 2)])

			# script
			scriptCode = response.xpath('//body//script[1]/text()').extract_first()

			# item['in_stock'] = scriptCode.split('"dropship": "')[1].split('"')[0].strip()
			item['in_stock'] = response.meta['o'][1]
			# TP代表第三方仓库，排除不要
			# if item['in_stock'] == 'TP':
			# 	return
			# "supplierLeadTime":
			# item['shipping_time'] = scriptCode.split(
			# 	'"supplierLeadTime":')[1].split(',')[0].strip(']} ')

			# item['shipping_time'] = self.validate(response.xpath(
			# 	'//div[@class="product-lead-time"]//text()').extract_first())

			# item['shipping_free'] = self.validate(
			# 		''.join(response.xpath('//div[@class="product-free-shipping"]//text()').extract()
			# 		)
			# 	)
			image = [x.split("'")[0] for x in scriptCode.split("'imageName': '")[1:]]

			item['image1'] = ''
			item['image2'] = ''

			if len(image) == 1:
				item['image1'] = image[0]
			elif len(image) > 1:
				item['image1'] = image[0]
				item['image2'] = image[1]
			
			item['description'] = self.validate(
				response.xpath('//*[@id="description"]/div[1]/div[2]/span//text()').extract_first()
			)
			yield item
		except:
			#print('!!!error page:',response.url)
			logging.info(response.url)
			print(response.url)

	def validate(self, item):
		try:
			return item.strip().replace('  ', '').replace('\r', '').replace('\n', '')\
				.replace(chr(8482),'').replace(chr(2122),'').replace(chr(174),'').replace(chr(8217),'')
		except:
			return ''
