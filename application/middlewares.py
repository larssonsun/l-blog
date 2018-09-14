#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import aiohttp_jinja2
from aiohttp import web
from application.filters import fmtLabel
import logging

# logging.basicConfig(level=logging.ERROR)

async def handle_403(request, *, msg):
    errorVm = dict(code="403", discrib=msg)
    return aiohttp_jinja2.render_template('errorpage.html', request, locals())

async def handle_404(request):
    errorVm = dict(code="404", discrib=fmtLabel(None, "e404_discrib"))
    return aiohttp_jinja2.render_template('errorpage.html', request, locals())


async def handle_500(request, *, error):
    errorVm = dict(code="500", discrib=fmtLabel(None, "e500_discrib"))
    logging.error(error)
    return aiohttp_jinja2.render_template('errorpage.html', request, locals())

def create_error_middleware(overrides):

    @web.middleware
    async def error_middleware(request, handler):

        try:
            response = await handler(request)

            override = overrides.get(response.status)
            if override:
                return await override(request)

            return response

        except web.HTTPException as ex:
            override = overrides.get(ex.status)
            if override:
                if ex.status == 403:
                    return await override(request, msg=ex.text)
                else:
                    return await override(request)

            raise

        except Exception as ex:
            return await handle_500(request, error=ex)

    return error_middleware


def setup_middlewares(app):
    error_middleware = create_error_middleware({
        403: handle_403,
        404: handle_404,
        500: handle_500
    })
    app.middlewares.append(error_middleware)
