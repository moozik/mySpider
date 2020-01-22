import asyncio
import random
import time
import requests
import aiohttp

class spider:
    output = []
    def __init__(self):
        self.gen = self.pageUrl()
        loop = asyncio.get_event_loop()
        tasks = [self.main(i) for i in range(4)]
        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()
    
    def pageUrl(self):
        for i in range(10):
            yield 'https://moozik.cn/ip.php?a={}'.format(i)

    def saveData(self, data, flag = False):
        if flag and len(self.output) > 0:
            print('saveData:', self.output)
            self.output = []
            return
        self.output.append(data)
        if len(self.output) == 3:
            print('saveData:', self.output)
            self.output = []

    async def getdata(self, session, url):
        async with session.get(url) as resp:
            print('status:',resp.status)
            return await resp.text()

    async def main(self, number):
        #获取session
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    url = self.gen.send(None)
                except StopIteration:
                    break
                # 异步请求
                ret = await self.getdata(session, url)
                print('number:',number,'do something:',url)
                self.saveData((url, number, ret))

if __name__ == '__main__':
    spider()