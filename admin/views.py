#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
from functools import wraps

import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import get_session
from datetime import datetime
from main.views import login_required
from models.db import select, delete_cache
from utils import WhooshSchema, rtData, setWhooshSearch, setFeed, addDictProp
from config.settings import FEED_DIR


def admin_required(func):
    """This function applies only to class views."""
    @wraps(func)
    async def wrapper(cls, *args, **kw):
        location = cls.request.app.router["Index"].url_for()
        session = await get_session(cls.request)
        uid = session.get("uid")
        user = cls.request.app.l_data
        if uid and user:
            if user.get("admin") == 1:
                return await func(cls, *args, **kw)
            else:
                return web.HTTPFound(location=location)
        else:
            return web.HTTPFound(location=location)
    return wrapper


class ResetBlogIndex(web.View):

    @login_required(True)
    @admin_required
    async def post(self):
        rtd = None
        try:
            #dctTuple's fields name must same as WhooshSchema's fields name
            dctTuple = tuple(await select("select `name_en` as 'id', `name` as 'title', `content`, `created_at` as 'createtime' from `blogs` order by `created_at`"))
            setWhooshSearch("blog", WhooshSchema.Blogs, dctTuple)
            rtd = rtData(error_code=-1, error_msg="重置blog索引成功", data=None)
        except Exception as ex:
            rtd = rtData(error_code=11001,
                         error_msg=f"重置blog索引时发生错误{ex}", data=None)
        return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)


class ResetBlogCache(web.View):

    @login_required(True)
    @admin_required
    async def post(self):
        try:
            blogs = await select("select `name_en` from blogs")
            [await delete_cache(blog["name_en"]) for blog in blogs]
            rtd = rtData(error_code=-1, error_msg="重置blog缓存成功", data=None)
        except Exception as ex:
            rtd = rtData(error_code=12001,
                         error_msg=f"重置blog缓存时发生错误{ex}", data=None)
        return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)


class ResetRss(web.View):

    @login_required(True)
    @admin_required
    async def post(self):
        try:
            rqst = self.request
            router = rqst.app.router
            urlIndex = f'{ rqst.scheme }://{ rqst.host }/'

            #get blogs
            blogs = await select("""
                select a.`name_en`, a.`created_at`, a.`updated_at`, a.`summary`, a.`name` as 'title', 
                a.`content`, b.`catelog_name` as 'cateTerm', a.`catelog` as 'cateId'
                from `blogs` a inner join `catelog` b on a.`catelog` = b.`id`
                order by `updated_at`""")
            [addDictProp(blog, "link", router["BlogDetail"].url_for(id=blog["name_en"])) for blog in blogs]
            [addDictProp(blog, "cateScheme", router["catelog"].url_for(cateId=blog["cateId"])) for blog in blogs]

            [addDictProp(blog, "created_at", 
                datetime.fromtimestamp(float(blog["created_at"])).strftime("%Y-%m-%d %H:%M:%S")) for blog in blogs]

            [addDictProp(blog, "updated_at", 
                datetime.fromtimestamp(float(blog["updated_at"])).strftime("%Y-%m-%d %H:%M:%S")) for blog in blogs]

            
            #create feed
            setFeed(
                f'tag:{ rqst.host },{ datetime.now().strftime("%Y-%m-%d %H:%M:%S") }',
                urlIndex, 
                str(router["static"].url_for(filename=r"images/favicon.png")), 
                urlIndex, "l", "l-blog", "larsson", "l@scetia.com", blogs)
            rtd = rtData(error_code=-1, error_msg="重置rss成功", data=None)
        except Exception as ex:
            rtd = rtData(error_code=13001,
                         error_msg=f"重置rss时发生错误{ex}", data=None)
        return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)