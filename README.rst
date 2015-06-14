PyBreezeChMS
=================

Python interface to BreezeChMS REST API http://www.breezechms.com

.. image:: https://travis-ci.org/aortiz32/pyBreezeChMS.svg?branch=master
   :target: https://travis-ci.org/aortiz32/pyBreezeChMS

.. image:: https://coveralls.io/repos/aortiz32/pyBreezeChMS/badge.png
   :target: https://coveralls.io/r/aortiz32/pyBreezeChMS

Installation
-------------
Before using pyBreezeChMS, you'll need to install the `requests <http://docs.python-requests.org/en/latest/>`_ library:

.. code-block:: bash

    $ sudo pip install requests

Getting Started
---------------

.. code-block:: python

    from breeze import breeze
    breeze_api = breeze.BreezeApi(
        breeze_url='https://your_subdomain.breezechms.com',
        apk_key='YourApiKey')


To get a JSON of all people:

.. code-block:: python

    people = breeze_api.GetPeople()
