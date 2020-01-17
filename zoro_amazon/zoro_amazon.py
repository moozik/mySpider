import requests
import time
from lxml import etree

class zoro_amazon:

    def __init__(self):
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'
        self.zoroSession = requests.Session()
        self.zoroSession.headers = {
            'user-agent': ua
        }
        self.zoroSession.proxies = {
            'https': 'http://127.0.0.1:1080'
        }
        self.amazonSession = requests.Session()
        # https://www.amazon.com/gp/delivery/ajax/address-change.html
        self.amazonSession.headers = {
            'user-agent': ua,
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8'
        }
        # 设置邮编 91770 92620
        self.amazonSession.post(
            'https://www.amazon.com/gp/delivery/ajax/address-change.html',
            data = 'locationType=LOCATION_INPUT&zipCode=91770&storeContext=industrial&deviceType=web&pageType=OfferListing&actionSource=glow')
        self.filein = False
        self.fileout = False
        self.specalSeller = ['VPSupply']
        # 阈值
        self.writeLimit = 20
        # 延时
        self.sleepTime = 1
        self.main()

    def __del__(self):
        if self.filein != False:
            self.filein.close()
        # if self.fileout != False:
        #     self.fileout.close()
    
    # 读
    def inputData(self):
        if self.filein == False:
            print('open filein file')
            self.filein = open('./filein.txt', 'r')
        row = self.filein.readline()
        while row != '':
            yield row.strip().split("\t")
            row = self.filein.readline()
    # 写
    def writeData(self, dataList):
        print('open fileout file')
        fileout = open('./fileout.txt', 'a')
        for item in dataList:
            fileout.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                item['rid'],
                item['zoro_id'],
                item['amazon_id'],
                item['zoro_price'],
                item['in_stock'],
                item['package'],
                item['zoro_new_price'],
                item['amazon_price'],
                item['best_price'],
                item['quant'],
                item['amazon_seller'],
                item['debug']
            ) + "\n")
        fileout.close()
    # zoro爬虫
    def zoro(self, sku):
        ret = self.zoroSession.get('https://www.zoro.com/product/?products={}'.format(sku))
        # print(ret.status_code, ret.text)
        ret = ret.json()
        return float(ret['products'][0]['price']), int(ret['products'][0]['validation']['minOrderQuantity'])
    
    # amazon 爬虫
    def amazon(self, sku):
        priceList = []
        sellerList = []
        response = self.amazonSession.get('https://www.amazon.com/gp/offer-listing/{}/ref=olp_f_new?f_new=true'.format(sku))
        if response.status_code != 200:
            self.debug += 'amazon_get_error:' + str(response.status_code) + ';'
            return False, False
        
        tree = etree.HTML(response.text)
        tableList = tree.xpath('//div[contains(@class,"olpOffer")]')
        self.debug += 'amazon_count:' + str(len(tableList) - 1) + ';'
        for rowTree in tableList:
            # price
            price = rowTree.xpath('div[1]/span/text()')
            if price == []:
                continue
            price = price[0].strip('$ ').replace(',','')
            # shippingPrice
            shippingPrice = rowTree.xpath('div[1]/p/span/span[@class="olpShippingPrice"]/text()')
            if shippingPrice == []:
                shippingPrice = 0
            else:
                shippingPrice = shippingPrice[0].strip('$ ').replace(',','')
            priceList.append(float(price) + float(shippingPrice))
            # Seller Information
            sellerInfo = rowTree.xpath('div[4]/h3/span/a/text()')
            if sellerInfo == []:
                sellerList.append('')
            else:
                sellerInfo = sellerInfo[0].strip()
                sellerList.append(sellerInfo)
        
        if priceList == []:
            return False, False
        else:
            amazon_price = min(priceList)
            amazon_seller = sellerList[priceList.index(amazon_price)]
            # if amazon_seller in self.specalSeller:
                # self.debug += 'found specal seller;'
            # 返回最低价格和seller
            return amazon_price, amazon_seller
    
    # 获取zoro库存
    def zoroInstock(self,dataList):
        postData = str([x['zoro_id'] for x in dataList]).replace("'",'"')
        r = self.zoroSession.post('https://www.zoro.com/avl/', data = postData)
        if r.status_code != 200 or r.text.strip() == '':
            r = requests.post('https://www.zoro.com/avl/', data=postData)
        jsonList = r.json()
        for item in dataList:
            item['in_stock'] = float(jsonList[item['zoro_id']][2])
            # 当in_stock >= 2 时 quant = 1
            if item['in_stock'] >= 2:
                item['quant'] = 1

    # 主进程
    def main(self):
        ret = []
        count = 0
        for item in self.inputData():
            time.sleep(self.sleepTime)
            self.debug = ''
            count += 1
            print(count, item)
            zoro_id = item[0]
            rid = item[1]
            amazon_id = item[2]
            zoro_price, package = self.zoro(zoro_id)
            zoro_new_price = zoro_price * package * 1.35 + 5
            amazon_price, amazon_seller = self.amazon(amazon_id)
            # amazon价格为空 使用zoro价格
            if amazon_price == False:
                amazon_price = zoro_price
                self.debug += 'amazon_price=None;'
            # 命中特殊seller
            if amazon_seller in self.specalSeller:
                best_price = zoro_new_price
                self.debug += 'mode=specal;'
            else:
                # 1）H>G, 则 I列 取  H-0.5
                if amazon_price > zoro_new_price:
                    best_price = amazon_price - 0.5
                    self.debug += 'mode=1;'
                # 2）H≤G>DX1.8+5时， 则 I列 取  H-0.2
                if amazon_price <= zoro_new_price and zoro_new_price > (zoro_price * 1.8 + 5):
                    best_price = amazon_price - 0.2
                    self.debug += 'mode=2;'
                # 3）H<DX1.8+5时, 则 I 列 取 DX1.8+5
                if amazon_price < (zoro_price * 1.8 + 5):
                    best_price = zoro_price * 1.8 + 5
                    self.debug += 'mode=3;'
            ret.append({
                'rid': rid,

                'zoro_id': zoro_id,
                'amazon_id': amazon_id,
                'zoro_price': round(zoro_price, 2),
                'in_stock': 0,
                'package': package,
                # zoro new price
                'zoro_new_price': round(zoro_new_price, 2),
                # ASIN Price
                'amazon_price': round(amazon_price, 2),
                #比较后价格
                'best_price': round(best_price, 2),
                # 计算new price = zoro_price * 1.35 + 5
                'quant': 0,

                'amazon_seller':amazon_seller,
                'debug':self.debug
            })
            if len(ret) == self.writeLimit:
                print('len(ret) == ' + str(self.writeLimit))
                self.zoroInstock(ret)
                self.writeData(ret)
                ret = []
        self.zoroInstock(ret)
        self.writeData(ret)
        ret = []

if __name__ == '__main__':
    zoro_amazon()
