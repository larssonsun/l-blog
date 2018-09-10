#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio, aiohttp, re
from datetime import datetime

async def open(addr):
    result = None
    headers= {"User-Agent": "Mozilla/5.0 (Windows NT 6.1)"}
    async with aiohttp.ClientSession() as session:
        async with session.get(addr, headers=headers) as r:
            try:
                decodedTxt = await r.text()
                result = await getTbHotList(decodedTxt)
            except Exception as e:
                print(e)
    return result

async def request(url):
    result = await open(url)
    return result

async def getTbHotList(decodedTxt):
    result = None
    hotTopicRe = re.compile(r'<span class="topic_flag_hot">\d+</span>([\s\S.]*)<span class="topic_num">\d+</span>')
    lst = re.findall(hotTopicRe, decodedTxt)
    lis = re.findall(r'<a.*?>(.*?)</a>', lst[0])
    return lis
'''
<ul class="topic_list_hot topic_list j_topic_toplist">
        
            <li class="topic_item">
                <span class="topic_flag_hot">1</span>
                <a rel="noreferrer" target="_blank" href="http://tieba.baidu.com/hottopic/browse/hottopic?topic_id=252068&amp;topic_name=OMG%E5%A4%BA%E5%86%A0" class="topic_name">OMG夺冠</a>
                <span class="topic_num">1572341</span>
            </li>
'''

def do():
    loop = asyncio.get_event_loop()
    tasks = [asyncio.ensure_future(request(r"https://tieba.baidu.com/f?kw=%E9%98%BF%E6%A3%AE%E7%BA%B3"))]
    result = loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
    if result:
        n = (x for x in range(1, 11))
        print(f'贴吧热议榜 top 10 - {datetime.now()}')
        [print(f'{next(n)} - {x}') for x in tasks[0].result()]
        

if __name__ == "__main__":
    do()
    while True:
        r = input(f'刷新（r）/退出(e) :')
        if r=="r":
            asyncio.set_event_loop(asyncio.new_event_loop())
            do()
        elif r == "e":
            break
        else:
            continue
