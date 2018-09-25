#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import uuid

import aiohttp_jinja2
import jinja2
from aiohttp import web
from aiohttp_session import setup
from aiohttp_session.redis_storage import RedisStorage

from admin.views import ResetBlogCache, ResetBlogIndex
from config.settings import STATIC_DIR, TEMPLATE_DIR
from main import filters
from main.views import (About, AddComment, Approve, Archive, BlogDetail,
                        DelComment, FullSiteSearch, Index, Login, Logout,
                        Registe, hello)
from utils import hash_sha256


def setupRoutes(app):
    
    #main
    app.router.add_view("/hello", hello, name="Hello")
    app.router.add_view("/", Index, name="Index")
    app.router.add_view("/" + "{type:[hot|time]+}/", Index, name="index_sort")
    app.router.add_view("/archive/", Archive, name="archive")
    app.router.add_view("/about/", About, name="about")
    app.router.add_view("/tag/" + r"{tagId:[0-9a-zA-Z\_]+}/", Index, name="tag")
    app.router.add_view("/tag/" + r"{tagId:[0-9a-zA-Z\_]+}/" + r"{type:[hot|time]+}/", Index, name="index_tag_sort")
    app.router.add_view("/catelog/" + r"{cateId:[0-9a-zA-Z\_]+}/", Index, name="catelog")
    app.router.add_view("/catelog/" + r"{cateId:[0-9a-zA-Z\_]+}/" + r"{type:[hot|time]+}/", Index, name="index_catelog_sort")
    app.router.add_view("/blogdetail/" + r"{id:[0-9a-zA-Z\-]+}/", BlogDetail, name="BlogDetail")
    app.router.add_view("/blogdetail/addComment", AddComment, name="add-comment")
    app.router.add_view("/blogdetail/delComment", DelComment, name="delete-comment")
    app.router.add_view("/login/", Login, name="Login")
    app.router.add_view("/logout/", Logout, name="logout")
    app.router.add_view("/registe/", Registe, name="registe")
    app.router.add_view("/registe/" + r"{approvedKey:\w{32}}/", Registe, name="registe_confirm")
    app.router.add_view("/approve/", Approve, name="approve")
    app.router.add_view("/fullsitesearch/", FullSiteSearch, name="full-size-search")

    #admin
    app.router.add_view("/admin/resetindex/", ResetBlogIndex, name="admin-resetindex")
    app.router.add_view("/admin/resetblogcache/", ResetBlogCache, name="admin-resetblogcache")
    

def setupStaticRoutes(app):
    app.router.add_static('/static/', path=STATIC_DIR, append_version=True, name='static')

def setupTemplateRoutes(app):
    aiohttp_jinja2.setup(app, 
    filters={
        "fmtLabel" : filters.fmtLabel,
        "fmtCatelog" : filters.fmtCatelog,
        "fmtDatetimeFromFloat" : filters.fmtDatetimeFromFloat,
        "fmtMonthDateFromFloat" : filters.fmtMonthDateFromFloat,
        "fmtYearMonthDateFromFloat" : filters.fmtYearMonthDateFromFloat,
        "getCommentForComments" : filters.getCommentForComments,
        "getArticalLead" : filters.getArticalLead,
        "getArticalMain" : filters.getArticalMain,
        "getArticalFull" : filters.getArticalFull,
        "fmtgetTitleImg" : filters.fmtgetTitleImg,
        "fmtGetHideInfo" : filters.fmtGetHideInfo,
        "fmtGetHideClass": filters.fmtGetHideClass,
        "limitCmmLength": filters.limitCmmLength,
        "converWith3dot" :filters.converWith3dot},
    loader=jinja2.FileSystemLoader(TEMPLATE_DIR))

def setupSession(app, redis_pool):
    storage = RedisStorage(redis_pool=redis_pool, cookie_name='sessionid', key_factory=lambda: hash_sha256(uuid.uuid4().hex))
    setup(app, storage)