#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
from functools import wraps

import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import get_session

from main.views import login_required
from models.db import select
from utils import WhooshSchema, rtData, setWhooshSearch


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
    # dctTuple = (dict(
    #     id="aiohttp-publish-with-nginx-supervisor",
    #     title=u"aiohttp 部署 Nginx + supervisord",
    #     content=u"将aiohttp服务器组运行在nginx之后有好多好处。首先，nginx是个很好的前端服务器。它可以预防很多攻击如格式错误的http协议的攻击。第二，部署nginx后可以同时运行多个aiohttp实例，这样可以有效利用CPU。最后，nginx提供的静态文件服务器要比aiohttp内置的静态文件支持快"

    # ),
    #     dict(
    #     id="python-slice",
    #     title=u"Python 切片",
    #     content=u"取一个list或tuple的部分元素是非常常见的操作。这里介绍一下python的高级特性之aiohttp一切"
    # ))

    @login_required(True)
    @admin_required
    async def post(self):
        rtd = None
        try:
            dctTuple = tuple(await select("select `name_en` as 'id', `name` as 'title', `content` from `blogs` order by `created_at`"))
            setWhooshSearch("blog", WhooshSchema.Blogs, dctTuple)
            rtd = rtData(error_code=-1, error_msg="重置blog索引成功", data=None)
        except Exception as ex:
            rtd = rtData(error_code=11001,
                         error_msg=f"重置blog索引时发生错误{ex}", data=None)
        return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)
