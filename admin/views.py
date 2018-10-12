#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import uuid
from datetime import datetime
from functools import wraps
import re
import aiohttp_jinja2
from aiohttp import web, http_exceptions
from aiohttp_session import get_session

from main.views import basePageInfo, login_required
from models.db import (delete_cache, exeNonQuery, exeScalar, get_cache, select,
                       set_cache)
from utils import (WhooshSchema, addDictProp, rtData, setFeed, setRobots, blogName_enRc,
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


async def deleteBlogCache():
    await delete_cache("blogdraft")


async def getBlogLastCache():
    return await get_cache("blogdraft")


async def setCacheForBlogPost(blogPostData, catelogLst, tagsLst):
    await set_cache("blogdraft", dict(
        blogid=blogPostData["blogid"],
        source_from=blogPostData["source_from"],
        name=blogPostData["name"],
        name_en=blogPostData["name_en"],
        title_image_filename="" if not blogPostData["title_image_filename"] or len(
            blogPostData["title_image_filename"]) == 0 else blogPostData["title_image_filename"],
        title_image_bgcolor="" if not blogPostData["title_image_filename"] or len(
            blogPostData["title_image_filename"]) == 0 else blogPostData["title_image_bgcolor"],
        summary=blogPostData["summary"],
        content=blogPostData["content"],
        catelog=catelogLst,
        tags=tagsLst))


async def getCateAndTags(vm):
    # tags
    vm["tags"] = await select("select `id`, `tag_name`, `blog_count` from `tags`")
    # catelogs
    vm["catelogs"] = await select("select `id`, `catelog_name`, `blog_count` from `catelog`")


class AddNewBlog(web.View):
    @basePageInfo
    @login_required(True)
    @admin_required
    async def get(self):
        vm = dict(blogdraft=None)
        await getCateAndTags(vm)
        data = await getBlogLastCache()
        if data:
            data["blogid"]=None
            await setCacheForBlogPost(data, data["catelog"], data["tags"])
        return aiohttp_jinja2.render_template("setblogdetail.html", self.request, vm)

    @login_required(True)
    @admin_required
    async def post(self):
        rtd = None
        try:
            data = await getBlogLastCache()
            rtd = rtData(error_code=-1, error_msg="读取草稿成功" if data else "无草稿可供使用", data=data)
        except Exception as ex:
            rtd = rtData(error_code=16001,
                         error_msg=f"读取草稿时发生错误{ex}", data=None)
        return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)


class SetBlogDetail(web.View):

    @basePageInfo
    @login_required(True)
    @admin_required
    async def get(self):

        vm = {}
        await getCateAndTags(vm)

        # blogdraft
        if "id" in self.request.match_info:
            blog = await select("select `id`, `source_from`, `name`, `name_en`, `title_image`, `summary`, \
                `content`, `catelog`, `tags` from `blogs` where `name_en` = %s limit 1 offset 0", self.request.match_info["id"])
            blog = blog[0]
            blog["blogid"] = blog["name_en"]
            catelog = str(blog.get("catelog")).split(",")
            tags = str(blog.get("tags")).split(",")
            m = titleImageRc.match(blog.get("title_image"))
            blog["title_image_filename"] = m.group(1) if m else ""
            blog["title_image_bgcolor"] = m.group(2) if m else "",
            await setCacheForBlogPost(blog, catelog, tags)
        else:
            raise http_exceptions.HttpBadRequest(message="未能找到编辑需要的文章id")

        vm["blogdraft"] = await getBlogLastCache()

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
                await setCacheForBlogPost(data, catelog, tags)
                rtd = rtData(error_code=-1, error_msg="文章草稿保存成功", data=None)
            else:
                rtd = rtData(error_code=12003,
                             error_msg="未能成功需要的文章信息或登录信息", data=None)
        except Exception as ex:
            rtd = rtData(error_code=12001,
                         error_msg=f"文章草稿保存时发生错误{ex}", data=None)
        return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)


class PublicBlogDetail(web.View):

    def validateBlog(self, blogdraft):
        rtd = None
        if not blogdraft:
            rtd = None
        elif len(blogdraft["catelog"]) != 1 or len(blogdraft["catelog"][0])==0:
            rtd = rtData(error_code=13006, error_msg="请选择文章分类", data=None)
        elif len(blogdraft["tags"]) <= 0 or len(blogdraft["tags"][0])==0:
            rtd = rtData(error_code=13007, error_msg="请选择文章标签", data=None)
        elif len(blogdraft["source_from"]) <= 0:
            rtd = rtData(error_code=13008, error_msg="请选择文章来源", data=None)
        elif not re.match(blogName_enRc, blogdraft["name_en"]):
            rtd = rtData(error_code=13009, error_msg="文章索引标题错误(数字字母或-,不含空格)", data=None)
        return rtd

    @login_required(True)
    @admin_required
    async def post(self):
        rtd = None
        l_data = self.request.app.l_data
        try:
            if l_data:
                user_id = l_data.get("id")
                user_name = l_data.get("name")

                blogdraft = await getBlogLastCache()
                errRtd = self.validateBlog(blogdraft)

                if not blogdraft:
                    rtd = rtData(error_code=13004,
                                 error_msg="未能找到保存的草稿", data=None)
                elif errRtd:
                    rtd = errRtd
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

                    # add new blog
                    if not blogid or len(blogid) == 0:
                        bloguuid = str(uuid.uuid1())
                        created_at = datetime.now().timestamp()
                        idx = await exeScalar("select `index` + 1 from `blogs` order by `index` desc limit 1 offset 0")
                        sqls.append(["insert into `blogs` values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                                     bloguuid, user_id, user_name, title_image, name_en, name, summary, content, created_at,
                                     created_at, idx, 0, source_from, tags, catelog])

                    # update blog
                    else:
                        # clear old catelog and tags
                        tc = await select("select `tags`, `catelog`, `name_en` from `blogs` where `name_en` = %s limit 1 offset 0", blogid)
                        tc = tc[0]

                        orgcatelist = tc["catelog"].split(",")
                        orgtaglist = tc["tags"].split(",")

                        # update blog
                        updated_at = datetime.now().timestamp()
                        sqls = [["UPDATE `blogs` SET `title_image` = %s, `name_en` = %s, `name` = %s, `summary` = %s, \
                            `content` = %s, `updated_at` = %s, `source_from` = %s, `tags` = %s, `catelog` = %s \
                            WHERE `name_en` = %s;", title_image, name_en, name, summary, content, updated_at, source_from,
                            tags, catelog, blogid]]

                    # catelog
                    catelist = blogdraft["catelog"]
                    st = ",".join(["%s" for cate in catelist])
                    if len(st) > 0:
                        sqls.append(
                            [f"update `catelog` set `blog_count` = `blog_count` + 1 where `id` in ({st})", *catelist])

                    # tags
                    taglist = blogdraft["tags"]
                    st = ",".join(["%s" for tag in taglist])
                    if len(st) > 0:
                        sqls.append(
                            [f"update `tags` set `blog_count` = `blog_count` + 1 where `id` in ({st})", *taglist])

                    # orgcatelist
                    if orgcatelist:
                        st = ",".join(["%s" for orgcate in orgcatelist])
                        if len(st) > 0:
                            sqls.append(
                                [f"update `catelog` set `blog_count` = `blog_count` - 1 where `id` in ({st})", *orgcatelist])

                    # orgtaglist
                    if orgtaglist:
                        st = ",".join(["%s" for orgtag in orgtaglist])
                        if len(st) > 0:
                            sqls.append(
                                [f"update `tags` set `blog_count` = `blog_count` - 1 where `id` in ({st})", *orgtaglist])

                    ic = await exeNonQuery(sqls)
                    if(ic > 0):

                        # delete cache
                        if blogid and len(blogid) > 0:
                            await delete_cache(blogid)
                        await deleteBlogCache()
                        rtd = rtData(
                            error_code=-1, error_msg="文章发布成功", data=None)
                    else:
                        rtd = rtData(error_code=13002,
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
Disallow: /admin/
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
