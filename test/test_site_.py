#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

import pytest_aiohttp
from aiohttp import web

from project.app.site_ import Feeds_Atom, Feeds_Rss, Robots, Sitemap


@pytest_aiohttp.pytest.fixture
def resultPattern():
    return dict(atomxml=r"[\s\S.\w]*</published></entry></feed>",
                rssxml=r"[\s\S.\w]*</pubDate></item></channel></rss>",
                sitemapxml=r"[\s\S.\w]*</priority></url></urlset>",
                robotstxt=r"[\s\S.\w]*sitemap.xml")


@pytest_aiohttp.pytest.mark.parametrize("viewPath, clientPath, resultPatternKey", [
    (("/atom.xml", Feeds_Atom), "/atom.xml", "atomxml"),
    (("/rss.xml", Feeds_Rss), "/rss.xml", "rssxml"),
    (("/sitemap.xml", Sitemap), "/sitemap.xml", "sitemapxml"),
    (("/robots.txt", Robots), "/robots.txt", "robotstxt")
])
async def test_Feeds_Atom(aiohttp_client, loop, viewPath, clientPath, resultPatternKey, resultPattern):
    app = web.Application()
    app.router.add_view(*viewPath, name="test")
    client = await aiohttp_client(app)
    resp = await client.get(clientPath)
    assert resp.status == 200
    text = await resp.text()
    assert re.match(resultPattern[resultPatternKey], text)
