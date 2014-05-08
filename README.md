Python BreezeCHMS
=================

Python interface to BreezeCHMS REST API http://www.breezechms.com

[![Build Status](https://travis-ci.org/aortiz32/pyBreezeChMS.svg?branch=master)](https://travis-ci.org/aortiz32/pyBreezeChMS)

## Installation

Before using pyBreezeChMS, you'll need to install the [requests](http://docs.python-requests.org/en/latest/) library:

    $ sudo pip install requests
    $ sudo pip install python-firebase

## Getting Started

```python
from breeze import breeze

breeze = breeze.BreezeApi('https://your_subdomain.breezechms.com', 'YourApiKey')
```

To JSON of all people:

```python

people = breeze.get_people()
```
