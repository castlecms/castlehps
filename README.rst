Prerequisites
-------------

1. Python 3.5+
2. Elastic Search 2.x installed somewhere
3. https://github.com/castlecms/elasticsearch-castle-scoring installed on ES

Install
-------

Just create a virtualenv and run the setup.py::

    $ virtualenv-3.5 ./env
    $ ./env/bin/python setup.py develop


Development and Basic Configuration
-----------------------------------

simple (localhost) dev::

    $ ./env/bin/castlehps

more complex, with options (such as different elasticsearch host)::

    $ ./env/bin/castlehps --config=default_config.ini

A test might look like this::

    curl -i http://127.0.0.1:8000?SearchableText=blah

Check out the ``example-query.json`` for an example of a query being submitted
to the ElasticSearch instance.


Configuration Options
---------------------

A full list of options can be found by looking at the ``default_config.ini``
file.
