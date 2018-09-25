#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import os.path
import re
import smtplib
import urllib
import uuid
from collections import namedtuple
from email.mime.text import MIMEText
from enum import Enum, unique
from threading import Thread

from jieba.analyse import ChineseAnalyzer
from markdown import Markdown
from markdown.extensions.toc import TocExtension
from whoosh.fields import ID, STORED, TEXT, Schema, NUMERIC
from whoosh.index import create_in, exists_in, open_dir, exists_in
from whoosh.qparser import MultifieldParser

from config.settings import HASH_KEY, INDEX_DIR, INDEXPREFIX, MAIL_SMTPCLIENT

analyzer = ChineseAnalyzer()
rtData = namedtuple("rtData", ["error_code", "error_msg", "data"])

emailRc = re.compile(r'^[\w-]+(\.[\w-]+)*@[\w-]+(\.[\w-]+)+$')
pwdRc = re.compile(r'^[0-9a-zA-Z\_]{6,18}$')
userNameRc = re.compile(r'^[0-9a-zA-Z]{6,18}$')
duplicateSqlRc = re.compile(r'[d|D]uplicate entry .+ for key .+')
certivateMailHtml = '''
<div style="background-color:#bbb;padding:30px">
    <div style="padding:20px 5px">L-blog</div>
    <div style="background-color:#fff;border-top:#3F6D98 solid 8px; padding:30px">
        <h2 style="font-size:20px;font-weight:bold">Hi {targetUserName},</h2>
        <div style="padding:15px 0">{describ}</div>
        <div style="background-color:#eee;text-align:center;padding:15px 0">
            <a href="{certificateHref}" style="color: #fff; text-decoration:none; font-size: 14px; background:#3f6d98; line-height: 32px; padding: 1px 20px; display: inline-block;border-radius: 3px;"
                target="_blank">{certificateButtonTxt}</a>
        </div>
        <div style="font-style:italic;color:#bbb;padding-top:20px">—— L-blog</div>
    </div>
</div>
'''


@unique
class WhooshSchema(Enum):
    Blogs = Schema(
        # stored= meanings that result will contains this filed's content
        id=ID(unique=True, stored=True),
        createtime=NUMERIC(stored=True),
        title=TEXT(analyzer=analyzer, stored=True),
        content=TEXT(analyzer=analyzer, stored=True))
        # summary=STORED)


def addDictProp(dct, newProp, prpoVal):
    dct[newProp] = prpoVal


def mdToHtml(mdStr):
    md = Markdown(extensions=[
        'markdown.extensions.fenced_code',
        'markdown.extensions.extra',
        'markdown.extensions.codehilite',
        'markdown.extensions.toc'
    ])
    #TocExtension实例用替代'markdown.extensions.toc'时
    #slugify 参数可以接受一个函数作为参数，这个函数将被用于处理标题的锚点值。Markdown 内置的处理方法不能处理中文标题
    html = md.convert(mdStr)
    toc = md.toc
    return html, toc


def hash_sha256(ctt):
    sha256 = hashlib.sha256(HASH_KEY["session"].encode('utf-8'))
    sha256.update(ctt.encode('utf-8'))
    return sha256.hexdigest()


def hash_md5(password):
    md5 = hashlib.md5(HASH_KEY["password"].encode('utf-8'))
    md5.update(password.encode('utf-8'))
    return md5.hexdigest()


def stmp_send(toAddr, subject, html):
    msg = MIMEText(html, "HTML", "utf-8")
    msg['Subject'] = subject
    # 这里如果不是使用SSL就是smtplib.SMTP
    smtpServ = smtplib.SMTP_SSL(
        MAIL_SMTPCLIENT['host'], port=MAIL_SMTPCLIENT['port'])
    smtpServ.set_debuglevel(-1)
    smtpServ.login(MAIL_SMTPCLIENT['fromAddr'], MAIL_SMTPCLIENT['fromPwd'])
    smtpServ.sendmail(MAIL_SMTPCLIENT['fromAddr'], toAddr, msg.as_string())
    smtpServ.quit()


def stmp_send_thread(toAddr, subject, html):
    t = Thread(target=stmp_send, args=(toAddr, subject, html))
    t.start()
    return t


def setAvatar(emailAddr):
    avatarAdmin = "/static/images/avatardemo.png"
    size = 40
    gravatar_url = "http://www.gravatar.com/avatar/{0}?"
    gravatar_url += urllib.parse.urlencode({'d': "mm", 's': str(size)})
    if emailAddr and len(emailAddr) > 0:
        gravatar_url = gravatar_url.format(hashlib.md5(
            emailAddr.encode("utf-8").lower()).hexdigest())
    return dict(avatarAdmin=avatarAdmin, avatarNormal=gravatar_url)


def getWhooshSearch(partten, indexNameLast, fieldList, hightlightFieldList):
    """hightlightFieldList must be the stored fields and under analyzed"""
    rt = []
    indexPath = INDEX_DIR
    if not exists_in(indexPath, indexname=f'{INDEXPREFIX}{indexNameLast}'):
        pass
    else:
        idx = open_dir(indexPath, indexname=f'{INDEXPREFIX}{indexNameLast}')
        with idx.searcher() as searcher:
            parser = MultifieldParser(fieldList, idx.schema)
            query = parser.parse(str(partten))
            results = searcher.search(query)
            for hit in results:
                rt.append(dict(hit))
                if hightlightFieldList:
                    for hf in hightlightFieldList:
                        hl = hit.highlights(hf)# Assume hf field is stored
                        rt[-1][hf] = hl if hl and len(hl)>0 else rt[-1][hf]

    return rt


def setWhooshSearch(indexNameLast, WhooshSchema, docs):
        schema = WhooshSchema.value
        idx = setWhooshIndex(indexNameLast, schema)
        setWhooshDoc(idx, docs)


def setWhooshIndex(indexName, schema):
    indexPath = INDEX_DIR
    idxName = f'{INDEXPREFIX}{indexName}'
    if not os.path.exists(indexPath):
        os.mkdir(indexPath)
    idx = create_in(indexPath, schema, indexname=idxName)

    return idx


def setWhooshDoc(idx, docs):
    with idx.writer() as writer:  # it calls commit() when the context exits
        with writer.group():
            for dct in docs:
                writer.update_document(**dct)