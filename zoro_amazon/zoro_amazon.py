import requests
import time
from lxml import etree
import helper
import sys
import asyncio

class zoro_amazon:

    def __init__(self):
        # print(sys.argv)
        # exit()
        self.config()
        # self.filein = open('./filein_10000.txt', 'r')  # filein_10000.txt
        self.fileout = False

        self.time_str = time.strftime('%y%m%d_%H%M%S',time.localtime())
        self.amazon_main(
            self.inputData('./filein.txt')
        )

    def __del__(self):
        pass
    
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
            'referer': 'https://www.amazon.com/'
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
        
        proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
            "host" : 'http-proxy-t3.dobel.cn',
            "port" : 9180,
            "user" : 'MOOZIKHJ5ALMR20',
            "pass" : 'uQ2BJSE9',
        }
        self.aSession.proxies = {
            'http':proxyMeta,
            'https':proxyMeta
        }
        # tb:K26VQTG66CA8BAPPF0HX+s-6TST51X5TYE05BXPCCE1|1579336490948&t:1579336490948&adb:adblk_yes
        # tb:s-R3KDF4Q21GW4P18K12G8|1579336506593&t:1579336507469&adb:adblk_yes

    def writePageLog(self, name, data):
        f = open(name,'wb')
        f.write(data)
        f.close()

    # 读
    def inputData(self, file = './filein.txt'):
        filein = open(file, 'r')
        row = filein.readline()
        flag = False
        while row.strip() != '':
            tmp = row.strip().split("\t")
            # if tmp[0] == 'G9178849':
            #     flag = True
            # if flag == False:
            #     row = filein.readline()
            #     continue

            # 列数为2是异常状态
            if len(tmp) == 2:
                print(','.join(tmp),'error')
                row = filein.readline()
                continue
            yield tmp
            row = filein.readline()
        filein.close()
    
    # 写
    def writeData(self, dataList, filepath = ''):
        if filepath == '':
            filepath = './fileout_'+self.time_str+'.txt'
        fileout = open(filepath, 'a', encoding = 'utf-8')
        if type(dataList) == list and len(dataList) > 0:
            # 为列表
            if type(dataList[0]) == dict:
                # 列表中为字典
                for item in dataList:
                    fileout.write("\t".join(map(str, list(item.values()))) + "\n")
            else:
                # 单行列表数据
                fileout.write("\t".join(map(str, dataList)) + "\n")
        else:
            print('dataList empty.')
            # dataList为空列表
            return
        if type(dataList) == str:
            # 文本数据直接写
            fileout.write(dataList)
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
                response = self.aSession.get(
                    'https://www.amazon.com/gp/offer-listing/{}/ref=olp_f_new?f_new=true'.format(sku),
                    headers = {'user-agent': helper.get_user_agent()})
                break
            except:
                print('amazon() error,',sku)
            if i == 2:
                return 0, False
            time.sleep(5)

        if response.status_code != 200:
            print('amazon status_code:', response.status_code,sku)
            # self.debug += 'a_get_err:' + str(response.status_code) + ';'
            self.writePageLog(sku + '.htm', response.content)
            time.sleep(5)
            return False, False
        else:
            if 'Try a different refinement' in response.text:
                print('amazon get:Try a different refinement',sku)
                self.writePageLog(sku + '.htm', response.content)
                return False, False

        tree = etree.HTML(response.text)
        tableList = tree.xpath('//div[contains(@class,"olpOffer")]')
        self.debug += 'a_con:' + str(len(tableList) - 1) + ';'
        for rowTree in tableList:
            # price
            # //div[contains(@class,"olpOffer")]/div[1]/span/text()
            price = rowTree.xpath('div[1]/span/text()')
            if price == []:
                continue
            price = price[0].strip('$ ').replace(',','')
            # shippingPrice
            # //div[contains(@class,"olpOffer")]/div[1]/p/span/span[@class="olpShippingPrice"]/text()
            shippingPrice = rowTree.xpath('div[1]/p/span/span[@class="olpShippingPrice"]/text()')
            if shippingPrice == []:
                shippingPrice = 0
            else:
                shippingPrice = shippingPrice[0].strip('$ ').replace(',','')
            try:
                priceList.append(float(price) + float(shippingPrice))
            except ValueError as err:
                print('ValueError', sku)
                continue
            # pc 经销商
            sellerInfo = rowTree.xpath('div[4]/h3/span/a/text()')
            if sellerInfo == []:
                # mobile 经销商 amazon 经销商
                sellerInfo = rowTree.xpath('div[2]/div[1]/div[contains(@class,"olpSellerName")]/span/text()')
                if sellerInfo == []:
                    # pc amazon为经销商
                    sellerInfo = rowTree.xpath('div[4]/h3/img/@alt')

            if sellerInfo == []:
                sellerList.append('')
            else:
                sellerInfo = sellerInfo[0].strip()
                sellerList.append(sellerInfo)
        
        if len(priceList) != len(sellerList):
            # log debug
            print("len(priceList) != len(sellerList)", sku)
            self.writePageLog(sku + '.htm', response.content)

        if priceList == []:
            print("priceList==[]", sku)
            return False, False
        else:
            amazon_price = min(priceList)
            amazon_seller = sellerList[priceList.index(amazon_price)]
            # if amazon_seller in self.specal_seller:
                # self.debug += 'found specal seller;'
            # 返回最低价格和seller
            return amazon_price, amazon_seller

    # 获取zoro库存
    def zoroInstock(self,dataList):
        postData = str([x['zoro_id'] for x in dataList]).replace("'",'"')
        try:
            r = self.zoroSession.post('https://www.zoro.com/avl/', data = postData)
            if r.status_code != 200 or r.text.strip() == '':
                time.sleep(5)
                r = self.zoroSession.post('https://www.zoro.com/avl/', data=postData)
            jsonList = r.json()
        except:
            return False
        for item in dataList:
            item['in_stock'] = float(jsonList[item['zoro_id']][2])
            # 当in_stock >= 2 时 quant = 1
            if item['in_stock'] >= 2:
                item['quant'] = 1
        return True

    # self.write_list
    # 写爬虫结果唯一入口，除了错误log
    def add_data(self, data, filepath):
        self.write_list.append(data)
        if len(self.write_list) == self.write_limit:
            self.writeData(self.write_list, filepath)
            self.write_list = []

    # 主进程
    def amazon_main(self, generate):
        self.specal_seller = ['VPSupply']
        # 阈值
        self.write_limit = 3
        # 延时
        self.sleep_time = 3
        self.count = 0
        self.write_list = []

        loop = asyncio.get_event_loop()
        tasks = [self.amazon_loop(generate, i) for i in range(2)]
        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()
    
    async def amazon_loop(self, generate, number):
        for item in generate:
            time.sleep(self.sleep_time)
            self.debug = ''
            self.count += 1
            print(self.count, number, item)
            zoro_id = item[0]
            rid = item[1]
            amazon_id = item[2]
            # zoro_price, package = self.zoro(zoro_id)
            # zoro_new_price = zoro_price * package * 1.35 + 5
            amazon_price, amazon_seller = await self.amazon(amazon_id)
            if amazon_seller == False:
                print('amazon_id:',amazon_id,' amazon_seller=False')
                self.writeData(item, './amazon_error_'+self.time_str+'.txt')
                continue
            # amazon价格为空 使用zoro价格
            '''
            if amazon_price == False:
                amazon_price = zoro_price
                self.debug += 'a_price=None;'
            # 命中特殊seller
            if amazon_seller in self.specal_seller:
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
            '''
            self.add_data({
                'zoro_id' : zoro_id,
                'rid' : rid,
                'amazon_id' : amazon_id,
                'amazon_price': round(amazon_price, 2),
                'amazon_seller' : amazon_seller
            },'./amazon_out_'+self.time_str+'.txt')
            # ret.append({
            #     'rid': rid,

            #     'zoro_id': zoro_id,
            #     'amazon_id': amazon_id,
            #     'zoro_price': round(zoro_price, 2),
            #     'in_stock': 'n',
            #     'package': package,
            #     # zoro new price
            #     'zoro_new_price': round(zoro_new_price, 2),
            #     # ASIN Price
            #     'amazon_price': round(amazon_price, 2),
            #     #比较后价格
            #     'best_price': round(best_price, 2),
            #     # 计算new price = zoro_price * 1.35 + 5
            #     'quant': 'n',

            #     'time': time_now,
            #     'amazon_seller':amazon_seller,
            #     'debug':self.debug
            # })
            # if len(ret) == self.write_limit:
            #     print('len(ret) == ' + str(self.write_limit))
            #     ret = self.zoroInstock(ret)
                # self.writeData(ret)
                # ret = []
        # self.zoroInstock(ret)
        # self.writeData(ret)
        # ret = []

if __name__ == '__main__':
    zoro_amazon()
