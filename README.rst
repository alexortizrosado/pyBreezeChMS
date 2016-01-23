PyBreezeChMS
=================

Python interface to BreezeChMS REST API http://www.breezechms.com

.. image:: https://travis-ci.org/alexortizrosado/pyBreezeChMS.svg?branch=master
   :target: https://travis-ci.org/alexortizrosado/pyBreezeChMS

.. image:: https://coveralls.io/repos/alexortizrosado/pyBreezeChMS/badge.png
   :target: https://coveralls.io/r/alexortizrosado/pyBreezeChMS

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

    people = breeze_api.get_people()

License
-------

Code released under the `Apache 2.0 <https://github.com/aortiz32/pyBreezeChMS/blob/master/LICENSE>`_ license.
