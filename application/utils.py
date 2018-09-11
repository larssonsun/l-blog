#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import smtplib
from collections import namedtuple
from email.mime.text import MIMEText
from threading import Thread

from markdown import Markdown
from markdown.extensions.toc import TocExtension

from config.settings import MAIL_SMTPCLIENT

rtData = namedtuple("rtData", ["error_code", "error_msg", "data"])

emialRc = re.compile(r'^[\w-]+(\.[\w-]+)*@[\w-]+(\.[\w-]+)+$')
pwdRc = re.compile(r'^[0-9a-zA-Z\_]{6,18}$')
userNameRc = re.compile(r'^[0-9a-zA-Z]{6,12}$')


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

#stmp_send_thread("l@scetia.com", "邮箱确认", f"<div><a href='{request.url}'>{request.url}<div>")
def stmp_send_thread(toAddr, subject, html):
    t = Thread(target=stmp_send, args=(toAddr, subject, html))
    t.start()
    return t
