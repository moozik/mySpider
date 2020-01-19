import requests
import time
from lxml import etree
import helper

class zoro_amazon:

    def __init__(self):
        self.config()
        self.filein = open('./filein_10000.txt', 'r')  # filein_10000.txt
        self.fileout = False
        self.specalSeller = ['VPSupply']
        self.amazonProxy = []
        # 阈值
        self.writeLimit = 10
        # 延时
        self.sleepTime = 5
        self.main()

    def __del__(self):
        if self.filein != False:
            self.filein.close()
        # if self.fileout != False:
        #     self.fileout.close()
    
    def config(self):
        self.zoroSession = requests.Session()
        self.zoroSession.headers = {
            'User-Agent': helper.get_user_agent()
        }
        self.zoroSession.proxies = {
           'https': 'http://127.0.0.1:1080'
        }
        self.aSession = requests.Session()
        # https://www.amazon.com/gp/delivery/ajax/address-change.html
        self.aSession.headers = {
            'user-agent': helper.get_user_agent(),
            'accecp': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'accept-encoding': 'gzip, deflate, br',
            'referer': 'https://www.amazon.com/dp/B00YSRG3K2/'
        }
        # 设置邮编 91770 92620
        self.USzipcode = '92620'
        self.aSession.post(
            'https://www.amazon.com/gp/delivery/ajax/address-change.html',
            data='locationType=LOCATION_INPUT&zipCode=' + self.USzipcode + '&storeContext=industrial&deviceType=web&pageType=OfferListing&actionSource=glow',
            headers={'content-type': 'application/x-www-form-urlencoded;charset=UTF-8'})
        self.aSession.cookies.set('skin', 'noskin')
        self.aSession.cookies.set(
            'cdn-session', 'AK-5e5ac67bed838d072293bb7470707953')
        self.aSession.cookies.set(
            'csm-hit', 'tb:s-R3KDF4Q21GW4P18K12G8|1579336506593&t:1579336507469&adb:adblk_yes')
        # tb:K26VQTG66CA8BAPPF0HX+s-6TST51X5TYE05BXPCCE1|1579336490948&t:1579336490948&adb:adblk_yes
        # tb:s-R3KDF4Q21GW4P18K12G8|1579336506593&t:1579336507469&adb:adblk_yes

    def amazonGet(self, url):
        # if self.amazonProxy == []:
        #     self.amazonProxy = helper.get_proxy_list()
        # if self.amazonProxy == []:
        #     print('proxy get error')
        #     exit()
        headers = {
            'user-agent': helper.get_user_agent(),
        }
        return self.aSession.get(url, headers=headers)

    def writePageLog(self, name, data):
        f = open(name,'wb')
        f.write(data)
        f.close()

    # 读
    def inputData(self):
        if self.filein == False:
            print('open filein file')
            self.filein = open('./filein.txt', 'r')
        row = self.filein.readline()
        flag = False
        while row.strip() != '':
            # yield row.strip().split("\t")
            tmp = row.strip().split("\t")
            
            if tmp[0] == 'G8494491':
                flag = True
            if flag == False:
                row = self.filein.readline()
                continue

            # 列数为2是异常状态
            if len(tmp) == 2:
                print(','.join(tmp),'error')
                continue
            yield tmp
            row = self.filein.readline()
    # 写
    def writeData(self, dataList):
        print('open fileout file')
        column_list = [
            'rid',
            'zoro_id',
            'amazon_id',
            'zoro_price',
            'in_stock',
            'package',
            'zoro_new_price',
            'amazon_price',
            'best_price',
            'quant',

            'time',
            'amazon_seller',
            'debug'
        ]
        # format_string = "{}\t" * len(column_list)
        # format_string = format_string.strip()

        format_string = ''
        for i in range(len(column_list)):
            format_string += "{0["+str(i)+"]}\t"
        format_string = format_string.strip()
        # print(format_string)
        fileout = open('./fileout.txt', 'a')
        for item in dataList:
            # print(item)
            # print(item.values())
            # print(list(item.values()))
            fileout.write(format_string.format(
                list(item.values())
                # item['rid'],
                # item['zoro_id'],
                # item['amazon_id'],
                # item['zoro_price'],
                # item['in_stock'],
                # item['package'],
                # item['zoro_new_price'],
                # item['amazon_price'],
                # item['best_price'],
                # item['quant'],

                # item['time'],
                # item['amazon_seller'],
                # item['debug']
            ) + "\n")
        fileout.close()
    # zoro爬虫
    def zoro(self, sku):
        i = 0
        while True:
            i += 1
            try:
                ret = self.zoroSession.get('https://www.zoro.com/product/?products={}'.format(sku))
                break
            except:
                print('zoro() error',sku)
            if i == 3:
                return 0, 0
            time.sleep(3)
        ret = ret.json()
        return float(ret['products'][0]['price']), int(ret['products'][0]['validation']['minOrderQuantity'])
    
    # amazon 爬虫
    def amazon(self, sku):
        priceList = []
        sellerList = []
        i = 0
        while True:
            i += 1
            try:
                response = self.amazonGet(
                    'https://www.amazon.com/gp/offer-listing/{}/ref=olp_f_new?f_new=true'.format(sku))
                break
            except:
                print('amazon() error,',sku)
            if i == 3:
                return 0, 'error'
            time.sleep(3)

        if response.status_code != 200:
            print('amazon status_code:', response.status_code)
            self.debug += 'a_get_err:' + str(response.status_code) + ';'
            time.sleep(20)
            return False, False
        else:
            if 'Try a different refinement' in response.text:
                print('amazon get:Try a different refinement')

        tree = etree.HTML(response.text)
        tableList = tree.xpath('//div[contains(@class,"olpOffer")]')
        self.debug += 'a_con:' + str(len(tableList) - 1) + ';'
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
                # sellerList.append('')
                # //div[contains(@class,"olpOffer")]/div[2]/div[1]/div[1]/span/text()
                # //div[contains(@class,"olpOffer")]/div[2]/div[1]/div[contains(@class,"olpSellerName")]/span/text()
                # 手机
                sellerInfo = rowTree.xpath('div[2]/div[1]/div[contains(@class,"olpSellerName")]/span/text()')
            if sellerInfo == []:
                sellerList.append('')
            else:
                sellerInfo = sellerInfo[0].strip()
                sellerList.append(sellerInfo)
        
        if len(priceList) != len(sellerList) or '' in sellerList:
            # log debug
            print(sku, "len(priceList) != len(sellerList) or '' in sellerList")
            self.writePageLog(sku+'.htm', response.content)

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
            time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
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
                self.debug += 'a_price=None;'
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

                'time': time_now,
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
