from castlehps import parser


def test_parser():
    result = parser.get_text_query('foobar')
    assert(len(result['bool']['should']) == 3)


def test_query():
    query = parser.query({
        'SearchableText': 'foobar',
        'searchSite': 'foobar.com',
        'portal_type': 'image'
    }, 'foobar')
    assert(query['query']['filtered']['query'] is not None)
