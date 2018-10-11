#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import uuid
from datetime import datetime
from functools import wraps

import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import get_session

from main.views import basePageInfo, login_required
from models.db import (delete_cache, exeNonQuery, exeScalar, get_cache, select,
                       set_cache)
from utils import (WhooshSchema, addDictProp, rtData, setFeed, setRobots,
                   setSitemap, setWhooshSearch, smtp_send_thread_self, titleImageRc)


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


class SetBlogDetail(web.View):

    @basePageInfo
    @login_required(True)
    @admin_required
    async def get(self):

        vm = {}

        # tags
        vm["tags"] = await select("select `id`, `tag_name`, `blog_count` from `tags`")
        # catelogs
        vm["catelogs"] = await select("select `id`, `catelog_name`, `blog_count` from `catelog`")

        # blogdraft
        if "id" in self.request.match_info:
            blog = await select("select `id`, `source_from`, `name`, `name_en`, `title_image`, `summary`, `content`, `catelog`, `tags` from `blogs` \
                where `name_en` = %s limit 1 offset 0", self.request.match_info["id"])
            blog = blog[0]

            catelog = str(blog.get("catelog")).split(",")
            tags = str(blog.get("tags")).split(",")
            m = titleImageRc.match(blog.get("title_image"))
            await set_cache("blogdraft", dict(
                blogid=blog.get("id"),
                source_from=blog.get("source_from"),
                name=blog.get("name"),
                name_en=blog.get("name_en"),
                title_image_filename=m.group(1) if m else "",
                title_image_bgcolor=m.group(2) if m else "",
                summary=blog.get("summary"),
                content=blog.get("content"),
                catelog=catelog,
                tags=tags))

        vm["blogdraft"] = await get_cache("blogdraft")
        if "id" not in self.request.match_info and vm["blogdraft"]:
            vm["blogdraft"]["blogid"] = None

        return aiohttp_jinja2.render_template("setblogdetail.html", self.request, vm)

    @login_required(True)
    @admin_required
    async def post(self):
        rtd = None
        data = await self.request.post()
        l_data = self.request.app.l_data
        try:
            if data and l_data:

                catelog = data.get("catelog").split(",")
                tags = data.get("tags").split(",")

                await set_cache("blogdraft", dict(
                    blogid=data.get("blogid"),
                    source_from=data.get("source_from"),
                    name=data.get("name"),
                    name_en=data.get("name_en"),
                    title_image_filename="" if len(
                        data.get("title_image_filename")) == 0 else data.get("title_image_filename"),
                    title_image_bgcolor="" if len(
                        data.get("title_image_filename")) == 0 else data.get("title_image_bgcolor"),
                    summary=data.get("summary"),
                    content=data.get("content"),
                    catelog=catelog,
                    tags=tags))

                rtd = rtData(error_code=-1, error_msg="文章草稿保存成功", data=None)
            else:
                rtd = rtData(error_code=12003,
                             error_msg="未能成功需要的文章信息或登录信息", data=None)
        except Exception as ex:
            rtd = rtData(error_code=12001,
                         error_msg=f"文章草稿保存时发生错误{ex}", data=None)
        return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)


class PublicBlogDetail(web.View):

    @login_required(True)
    @admin_required
    async def post(self):
        rtd = None
        l_data = self.request.app.l_data
        try:
            if l_data:
                user_id = l_data.get("id")
                user_name = l_data.get("name")

                blogdraft = await get_cache("blogdraft")
                if not blogdraft:
                    rtd = rtData(error_code=13004,
                                 error_msg="未能找到保存的草稿", data=None)
                else:
                    blogid = blogdraft["blogid"]
                    source_from = blogdraft["source_from"]
                    name = blogdraft["name"]
                    name_en = blogdraft["name_en"]
                    title_image = "" if blogdraft[
                        'title_image_filename'] == None else f"/static/images/article/{ blogdraft['title_image_filename'] }.png|bgc|#{ blogdraft['title_image_bgcolor'] }|bgcend|"
                    summary = blogdraft["summary"]
                    content = blogdraft["content"]
                    catelog = ",".join(blogdraft["catelog"])
                    tags = ",".join(blogdraft["tags"])

                    sqls = []
                    orgcatelist = None
                    orgtaglist = None
                    orgname_en = None

                    # add new blog
                    if not blogid or len(blogid) == 0:
                        blogid = str(uuid.uuid1())
                        created_at = datetime.now().timestamp()
                        idx = await exeScalar("select `index` + 1 from `blogs` order by `index` desc limit 1 offset 0")
                        sqls.append(["insert into `blogs` values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                                     blogid, user_id, user_name, title_image, name_en, name, summary, content, created_at,
                                     created_at, idx, 0, source_from, tags, catelog])

                    # update blog
                    else:
                        # clear old catelog and tags
                        tc = await select("select `tags`, `catelog`, `name_en` from `blogs` where `id` = %s limit 1 offset 0", blogid)
                        tc = tc[0]

                        orgcatelist = tc["catelog"].split(",")
                        orgtaglist = tc["tags"].split(",")
                        orgname_en = tc["name_en"]
                        # update blog
                        updated_at = datetime.now().timestamp()
                        sqls = [["UPDATE `blogs` SET `title_image` = %s, `name_en` = %s, `name` = %s, `summary` = %s, `content` = %s, `updated_at` = %s, `source_from` = %s, \
                            `tags` = %s, `catelog` = %s WHERE `id` = %s;", title_image, name_en, name, summary, content, updated_at, source_from, tags, catelog, blogid]]

                    # catelog
                    catelist = blogdraft["catelog"]
                    if orgcatelist:
                        [(catelist.remove(orgcate) if orgcate in catelist else None)
                         for orgcate in orgcatelist]
                    st = ",".join(["%s" for cate in catelist])
                    if len(st) > 0:
                        sqls.append(
                            [f"update `catelog` set `blog_count` = `blog_count` + 1 where `id` in ({st})", *catelist])

                    # tags
                    taglist = blogdraft["tags"]
                    if orgtaglist:
                        [(taglist.remove(orgtag) if orgtag in taglist else None)
                         for orgtag in orgtaglist]
                    st = ",".join(["%s" for tag in taglist])
                    if len(st) > 0:
                        sqls.append(
                            [f"update `tags` set `blog_count` = `blog_count` + 1 where `id` in ({st})", *taglist])

                    ic = await exeNonQuery(sqls)
                    if(ic > 0):

                        # delete cache
                        if orgname_en:
                            await delete_cache(orgname_en)

                        rtd = rtData(
                            error_code=-1, error_msg="文章发布成功", data=None)
                    else:
                        rtd = rtData(error_code=12002,
                                     error_msg="未能成功发布文章", data=None)
            else:
                rtd = rtData(error_code=13003,
                             error_msg="未能成功需要的文章信息或登录信息", data=None)
        except Exception as ex:
            rtd = rtData(error_code=13001,
                         error_msg=f"文章发布时发生错误{ex}", data=None)
        return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)


class DeleteBlog(web.View):
    @login_required(True)
    @admin_required
    async def post(self):
        rtd = None
        data = await self.request.post()
        try:
            if data and "id" in data:
                # get blog
                blog = await select("select * from `blogs` where `name_en` = %s limit 1 offset 0", data.get("id"))
                blog = blog[0]

                # delete blog
                sqls = [
                    ["delete from `blogs` where `name_en`=%s", data.get("id")]]

                # update catelog
                catelist = blog["catelog"].split(",")
                st = ",".join(["%s" for cate in catelist])
                if len(st) > 0:
                    sqls.append(
                        [f"update `catelog` set `blog_count` = `blog_count` - 1 where `id` in ({st})", *catelist])

                # update tags
                taglist = blog["tags"].split(",")
                st = ",".join(["%s" for tag in taglist])
                if len(st) > 0:
                    sqls.append(
                        [f"update `tags` set `blog_count` = `blog_count` - 1 where `id` in ({st})", *taglist])

                ic = await exeNonQuery(sqls)
                if ic > 0:
                    # delete blog cache
                    await delete_cache(data.get("id"))
                    # send to mail
                    smtp_send_thread_self(
                        f"已删除博客备份:{blog.get('name')}", str(blog))
                    rtd = rtData(error_code=-1,
                                 error_msg="删除文章成功, 被删除的内容已发送到邮箱", data=None)
                else:
                    rtd = rtData(error_code=15003,
                                 error_msg="未能成功删除文章", data=None)
            else:
                rtd = rtData(error_code=15002,
                             error_msg="未能找到目标文章", data=None)
        except Exception as ex:
            rtd = rtData(error_code=15001,
                         error_msg=f"删除文章时发生错误{ex}", data=None)
        return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)


class ResetBlogIndex(web.View):

    @login_required(True)
    @admin_required
    async def post(self):
        rtd = None
        try:
            # dctTuple's fields name must same as WhooshSchema's fields name
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


class ResetFeeds(web.View):

    @login_required(True)
    @admin_required
    async def post(self):
        try:
            rqst = self.request
            router = rqst.app.router
            urlIndex = f'{ rqst.scheme }://{ rqst.host }'

            # get blogs
            blogs = await select("""
                select `name_en`, `created_at`, `updated_at`, `summary`, `name` as 'title',
                `content`,  `catelog`
                from `blogs` a
                order by `updated_at`""")
            [addDictProp(
                blog, "link", f'{urlIndex}{router["BlogDetail"].url_for(id=blog["name_en"])}') for blog in blogs]
            [addDictProp(
                blog, "cateScheme", f'{urlIndex}{router["catelog"].url_for(cateId=blog["catelog"])}') for blog in blogs]

            [addDictProp(blog, "created_at",
                         datetime.fromtimestamp(float(blog["created_at"])).strftime("%Y-%m-%d %H:%M:%S")) for blog in blogs]

            [addDictProp(blog, "updated_at",
                         datetime.fromtimestamp(float(blog["updated_at"])).strftime("%Y-%m-%d %H:%M:%S")) for blog in blogs]

            # create feed
            setFeed(
                f'tag:{ rqst.host },{ datetime.now().strftime("%Y-%m-%d %H:%M:%S") }',
                f'{urlIndex}/',
                f'{urlIndex}{router["static"].url_for(filename=r"images/favicon.png")}',
                f'{urlIndex}/', "l", "l-blog", "larsson", "77540975@qq.com", blogs)
            rtd = rtData(error_code=-1, error_msg="重置rss成功", data=None)
        except Exception as ex:
            rtd = rtData(error_code=13001,
                         error_msg=f"重置rss时发生错误{ex}", data=None)
        return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)


class ResetSitemap(web.View):

    @login_required(True)
    @admin_required
    async def post(self):
        try:
            rqst = self.request
            router = rqst.app.router
            urlIndex = f'{ rqst.scheme }://{ rqst.host }'

            # get blogs
            blogs = await select("""
                select `name_en`, `updated_at`
                from `blogs` a
                order by `updated_at`""")

            [addDictProp(blog, "lastmod",
                         datetime.fromtimestamp(float(blog["updated_at"])).strftime("%Y-%m-%d")) for blog in blogs]

            [addDictProp(
                blog, "loc", f'{urlIndex}{router["BlogDetail"].url_for(id=blog["name_en"])}') for blog in blogs]

            [blog.pop("name_en") for blog in blogs]
            [blog.pop("updated_at") for blog in blogs]

            # write to sitemap.xml
            setSitemap("sitemap.xml", blogs)

            rtd = rtData(error_code=-1, error_msg="重置sitemap成功", data=None)
        except Exception as ex:
            rtd = rtData(error_code=14001,
                         error_msg=f"重置sitemap时发生错误{ex}", data=None)
        return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)


class ResetRobots(web.View):

    @login_required(True)
    @admin_required
    async def post(self):
        try:
            rqst = self.request
            urlIndex = f'{ rqst.scheme }://{ rqst.host }'

            # robotsStr
            robotsStr = f"""User-agent: *
Disallow: /fullsitesearch/
Disallow: /login/
Disallow: /logout/
Disallow: /registe/
Disallow: /approve/
Disallow: /css/
Disallow: /js/

Sitemap: { urlIndex }/sitemap.xml"""

            # write to robots.txt
            setRobots("robots.txt", robotsStr)

            rtd = rtData(error_code=-1, error_msg="重置robots.txt成功", data=None)
        except Exception as ex:
            rtd = rtData(error_code=15001,
                         error_msg=f"重置robots.txt时发生错误{ex}", data=None)
        return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)
