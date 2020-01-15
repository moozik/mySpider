import requests
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
        
        self.main()

    def inputData(self):
        f = open('./filein.txt','r')
        row = f.readline()
        while row != '':
            yield row.strip().split("\t")
            row = f.readline()
        f.close()

    def writeData(self, dataList):
        f = open('./fileout.txt', 'a')
        for item in dataList:
            f.write('{},{},{},{},{},{},{},{},{}'.format(
                item['zoro_id'],
                item['rid'],
                item['zoro_price'],
                item['in_stock'],
                item['package'],
                item['amazon_id'],
                item['amazon_price'],
                item['new_price'],
                item['quant']
            ) + "\n")
        f.close()

    def zoro(self, sku):
        ret = self.zoroSession.get('https://www.zoro.com/product/?products={}'.format(sku))
        # print(ret.status_code, ret.text)
        ret = ret.json()
        return float(ret['products'][0]['price']), int(ret['products'][0]['validation']['minOrderQuantity'])
    
    def amazon(self, sku):
        priceList = []
        response = self.amazonSession.get('https://www.amazon.com/gp/offer-listing/{}/ref=olp_f_new?f_new=true'.format(sku))
        if response.status_code != 200:
            return False
        
        tree = etree.HTML(response.text)
        for priceColumn in tree.xpath('//div[contains(@class,"olpOffer")]/div[1]'):
            # price
            price = priceColumn.xpath('span/text()')
            if price == []:
                continue
            price = price[0].strip('$ ')
            # shippingPrice
            shippingPrice = priceColumn.xpath('p/span/span[@class="olpShippingPrice"]/text()')
            if shippingPrice == []:
                shippingPrice = 0
            else:
                shippingPrice = shippingPrice[0].strip('$ ')
            priceList.append(float(price) + float(shippingPrice))
        if priceList == []:
            return False
        else:
            return min(priceList)
    
    def zoroInstock(self,dataList):
        postData = str([x['zoro_id'] for x in dataList]).replace("'",'"')
        r = self.zoroSession.post('https://www.zoro.com/avl/', data = postData)
        if r.status_code != 200 or r.text.strip() == '':
            r = requests.post('https://www.zoro.com/avl/', data=postData)
        jsonList = r.json()
        for item in dataList:
            item['in_stock'] = float(jsonList[item['zoro_id']][2])
    
    def main(self):
        ret = []
        for item in self.inputData():
            zoro_id = item[0]
            rid = item[1]
            amazon_id = item[2]
            zoro_price, package = self.zoro(zoro_id)
            amazon_price = self.amazon(amazon_id)
            if amazon_price == False:
                amazon_price = zoro_price
            ret.append({
                'zoro_id': zoro_id,
                'rid': rid,
                'zoro_price': zoro_price,
                'in_stock': 0,
                'package': package,

                'amazon_id': amazon_id,
                'amazon_price': amazon_price,

                'new_price': (amazon_price + zoro_price)/2,
                'quant': 0
            })
            if len(ret) == 10:
                self.zoroInstock(ret)
                self.writeData(ret)
                ret = []
        self.zoroInstock(ret)
        self.writeData(ret)
        ret = []

if __name__ == '__main__':
    zoro_amazon()
