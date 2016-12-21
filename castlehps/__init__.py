import configparser
from aioes import Elasticsearch
from aiohttp import MultiDict
from aiohttp import web
from urllib.parse import parse_qsl
from urllib.parse import urljoin
from urllib.parse import urlparse

import argparse
import json
import logging
from castlehps.app import CastleHPSApplication
from castlehps import parser


# see build_app for raven/sentry integration to the logger
logger = logging.getLogger(__name__)


def _one(val):
    if val and type(val) == list and len(val) == 1:
        val = val[0]
    return val


def apply_cors(req, response):
    settings = req.app.settings
    req_headers = req.headers
    origin = req_headers.get('origin')
    if origin:
        host, _, _ = urlparse(origin).netloc.partition(':')
        if host in settings['allowed_origins']:
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            # provide valid default origin
            response.headers['Access-Control-Allow-Origin'] = settings['default_allowed_origin']


async def handle_search(req):
    settings = req.app.settings

    get_params = MultiDict(parse_qsl(req.query_string))

    qs = get_params.get('SearchableText', '')
    base_site_url = settings['base_url'] or req.headers.get('origin')

    doc_type = settings['doc_type']
    if 'searchSite' in get_params:
        doc_type = 'website'

    try:
        page = int(get_params.get('page'))
    except:
        page = 1

    params = parser.params(get_params, page)
    if (params['size'] + params['from_']) >= 10000:
        response = web.Response(body=json.dumps({
            'status': 'error',
            'message': 'paging not allowed past 10000'
        }).encode('utf-8'))
        response.headers['Content-Type'] = 'application/json'
        apply_cors(req, response)
        return response

    bypass = False
    conn = Elasticsearch(
        endpoints=settings['elasticsearch_hosts'],
        sniffer_timeout=0.5)
    try:
        if qs:
            results = await conn.search(
                index=settings['index'],
                doc_type=doc_type,
                body=parser.query(get_params),
                **params)
            conn.close()  # can we share a cache of connection objects instead?
            count = results['hits']['total']
            try:
                suggestions = results['suggest']['SearchableText'][0]['options']
            except:
                suggestions = []
            results = results['hits']['hits']
        else:
            bypass = True
    except:
        bypass = True
        logger.error('Error with query', exc_info=True)
    finally:
        conn.close()

    if bypass:
        results = []
        suggestions = []
        count = 0

    items = []
    for res in results:
        fields = res['fields']

        attrs = {}
        for key in parser.search_attributes:
            attrs[key] = _one(fields.get(key))

        if 'url' in fields:
            url = base_url = _one(fields['url'])
            parsed = urlparse(url)
            path = parsed.path
        else:
            path = fields.get('path.path', [''])
            path = path[0]
            path = '/' + '/'.join(path.split('/')[2:])
            url = base_url = urljoin(base_site_url.rstrip('/'), path.lstrip('/'))
            if attrs.get('portal_type') in ('Image', 'File', 'Video', 'Audio'):
                url += '/view'

        attrs.update({
            'review_state': 'published',
            'score': res['_score'],
            'path': path,
            'base_url': base_url,
            'url': url
        })
        items.append(attrs)

    json_resp = json.dumps({
        'count': count,
        'results': items,
        'page': page,
        'suggestions': suggestions
    })
    response = web.Response(body=json_resp.encode('utf-8'))
    response.headers['Content-Type'] = 'application/json'
    apply_cors(req, response)

    return response


def run():
    parser = argparse.ArgumentParser(description='Run CastleHPS server')
    parser.add_argument('--config', dest='config', default='config.ini')
    parser_settings, _ = parser.parse_known_args()
    filename = parser_settings.config

    config = configparser.ConfigParser()
    fi = open(filename)
    config.readfp(fi)
    fi.close()

    settings = {}
    for key, value in config.items('config'):
        if value == 'false':
            value = False
        elif value == 'true':
            value = True
        elif '\n' in value:
            value = [v.strip() for v in value.splitlines() if v.strip()]
        try:
            value = int(value)
        except:
            pass
        settings[key] = value

    if settings['enable_sentry'] and settings['sentry_dsn']:
        from raven.handlers.logging import SentryHandler
        from raven.conf import setup_logging
        level = getattr(logging, settings['sentry_loglevel'].upper(), logging.ERROR)
        handler = SentryHandler(settings['sentry_dsn'], level=level)
        setup_logging(handler)

    app = CastleHPSApplication(settings)
    app.router.add_route('GET', '/', handle_search)
    web.run_app(app, host=settings['host'], port=settings['port'])
