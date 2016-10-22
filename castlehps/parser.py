from copy import deepcopy


search_attributes = [
    'Title',
    'Description',
    'Subject',
    'contentType',
    'created',
    'modified',
    'effective',
    'hasImage',
    'is_folderish',
    'portal_type',
    'url'
]

suggest_base = {
    "SearchableText": {
        "text": None,
        "term": {
            "field": "SearchableText"
        }
    }
}

_allowed_origins = (
    '127.0.0.1',
    'localhost',
    '10.3.3.30',
    'api.fbi.gov',
    'www.fbi.gov',
    'bankrobbers.fbi.gov',
)


base_query = {
    "query": {
        "function_score": {
            "query": {
                "filtered": {
                    "filter": {
                        "and": [{
                            "term": {
                                "allowedRolesAndUsers": "Anonymous"
                            }
                        }, {
                            "term": {
                                "trashed": False
                            }
                        }]
                    },
                    "query": {}
                }
            },
            "script_score": {
                "lang": "native",
                "script": "castlepopularity",
                "params": {
                    "search": None
                }
            }
        }
    },
    "suggest": suggest_base
}

site_search_base_query = {
    "query": {
        'filtered': {
            'filter': {
                "term": {
                    "domain": None
                }
            },
            'query': {}
        }
    },
    "suggest": suggest_base
}


def get_text_query(value):
    clean_value = value.strip('*')  # el doesn't care about * like zope catalog does
    queries = [{
        "match_phrase": {
            'SearchableText': {
                'query': clean_value,
                'slop': 2
            }
        }
    }, {
        "match_phrase_prefix": {
            'Title': {
                'query': clean_value,
                'boost': 2
            }
        }
    }, {
        "match": {
            'SearchableText': {
                'query': clean_value
            }
        }
    }]
    return {
        "bool": {
            "should": queries
        }
    }


def query(get_params, doc_type):
    qs = get_params.get('SearchableText', '')

    if 'searchSite' in get_params:
        search_domain = get_params['searchSite']
        query = deepcopy(site_search_base_query)
        query['query']['filtered']['query'] = get_text_query(qs)
        query['query']['filtered']['filter']['term']['domain'] = search_domain
    else:
        query = deepcopy(base_query)
        query['query']['function_score']['query']['filtered']['query'] = get_text_query(qs)
        query['query']['function_score']['script_score']['params']['search'] = qs

        pt = None
        if 'portal_type' in get_params:
            pt = [get_params['portal_type']]
        elif 'portal_type[]' in get_params:
            pt = get_params.getall('portal_type[]')
        if pt:
            pt_terms = []
            for pt_ in pt:
                pt_terms.append({
                    "term": {
                        "portal_type": pt_
                    }
                })
            query['query']['function_score']['query']['filtered']['filter']['and'].append({
                "or": pt_terms
            })
        else:
            # strip out Images from default seach, they just muddy it all up
            query['query']['function_score']['query']['filtered']['filter']['and'].append({
                "not": {
                    "term": {
                        "portal_type": "Image"
                    }
                }
            })

    query['suggest']['SearchableText']['text'] = qs

    return query


def params(get_params, page):
    try:
        page_size = int(get_params.get('pageSize'))
    except:
        page_size = 20
    page_size = min(page_size, 50)
    start = (page - 1) * page_size

    return {
        'fields': ','.join(search_attributes) + ',path.path',
        'size': page_size,
        'from_': start
    }
