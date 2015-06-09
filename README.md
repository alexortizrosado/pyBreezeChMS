PyBreezeChMS
=================

Python interface to BreezeCHMS REST API http://www.breezechms.com

[![Build Status](https://travis-ci.org/aortiz32/pyBreezeChMS.svg?branch=master)](https://travis-ci.org/aortiz32/pyBreezeChMS) [![Coverage Status](https://coveralls.io/repos/aortiz32/pyBreezeChMS/badge.png)](https://coveralls.io/r/aortiz32/pyBreezeChMS)

## Installation

Before using pyBreezeChMS, you'll need to install the [requests](http://docs.python-requests.org/en/latest/) library:

    $ sudo pip install requests

## Getting Started

```python
from breeze import breeze

breeze = breeze.BreezeApi(
    breeze_url='https://your_subdomain.breezechms.com',
    api_key='YourApiKey')
```

To get a JSON of all people:

```python

people = breeze.GetPeople()
```
