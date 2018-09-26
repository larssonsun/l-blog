#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from aiohttp import web

class Feeds_Atom(web.View):
    async def get(self):
        location = self.request.app.router["static"].url_for(filename="atom.xml")
        return web.HTTPFound(location=location)

class Feeds_Rss(web.View):
    async def get(self):
        location = self.request.app.router["static"].url_for(filename="rss.xml")
        return web.HTTPFound(location=location)
