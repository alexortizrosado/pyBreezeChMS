"""Unittests for breeze.py"""

import json
import unittest

from breeze.breeze import BreezeApi
from breeze.breeze import BreezeError


class MockConnection(object):
  """Mock requests connection."""
  def __init__(self, response):
    self.response = response
    self.headers = {}
  
  def post(self, url, params, headers, *args, **kwargs):
    return self.response

class MockResponse(object):
  """ Mock requests HTTP response."""
  def __init__(self, status_code, content):
    self.status_code = status_code
    self.content = content
  
  @property
  def ok(self):
    return str(self.status_code).startswith('2')
  
  def json(self):
    if self.content:
        return json.loads(self.content)
    return None
  
  def raise_for_status(self):
    raise Exception('Fake HTTP Error')


class BreezeApiTestCase(unittest.TestCase):
  def setUp(self):
    self.FAKE_API_KEY = 'fak3ap1k3y'
    self.FAKE_SUBDOMAIN = 'https://demo.breezechms.com'
  
  def testInvalidSubdomain(self):
    self.assertRaises(BreezeError,
        lambda: BreezeApi(api_key=self.FAKE_API_KEY,
                          breeze_url='invalid-subdomain'))
    self.assertRaises(BreezeError,
        lambda: BreezeApi(api_key=self.FAKE_API_KEY,
                          breeze_url='http://blah.breezechms.com'))
    self.assertRaises(BreezeError,
        lambda: BreezeApi(api_key=self.FAKE_API_KEY, breeze_url=''))
  
  def testMissingApiKey(self):
    self.assertRaises(BreezeError,
        lambda: BreezeApi(api_key=None, breeze_url=self.FAKE_SUBDOMAIN))
    self.assertRaises(BreezeError,
        lambda: BreezeApi(api_key='', breeze_url=self.FAKE_SUBDOMAIN))
  
  def testGetPeople(self):
    response = MockResponse(200, json.dumps({'name': 'Some Data.'}))
    connection = MockConnection(response)
    breeze = BreezeApi(
        breeze_url=self.FAKE_SUBDOMAIN,
        api_key=self.FAKE_API_KEY,
        connection=connection)
    self.assertEqual(breeze.GetPeople(), json.loads(response.content))
  
  def testGetProfileFields(self):
    response = MockResponse(200, json.dumps({'name': 'Some Data.'}))
    connection = MockConnection(response)
    breeze = BreezeApi(
        breeze_url=self.FAKE_SUBDOMAIN,
        api_key=self.FAKE_API_KEY,
        connection=connection)
    self.assertEqual(breeze.GetProfileFields(), json.loads(response.content))
  
  def testGetPersonDetails(self):
    response = MockResponse(200, json.dumps({'person_id': 'Some Data.'}))
    connection = MockConnection(response)
    breeze = BreezeApi(
        breeze_url=self.FAKE_SUBDOMAIN,
        api_key=self.FAKE_API_KEY,
        connection=connection)
    self.assertEqual(breeze.GetPersonDetails('person_id'),
                     json.loads(response.content))
  
  def testGetEvents(self):
    response = MockResponse(200, json.dumps({'event_id': 'Some Data.'}))
    connection = MockConnection(response)
    breeze = BreezeApi(
        breeze_url=self.FAKE_SUBDOMAIN,
        api_key=self.FAKE_API_KEY,
        connection=connection)
    self.assertEqual(breeze.GetEvents(),json.loads(response.content))
  
  def testEventCheckIn(self):
    response = MockResponse(200, json.dumps({'event_id': 'Some Data.'}))
    connection = MockConnection(response)
    breeze = BreezeApi(
        breeze_url=self.FAKE_SUBDOMAIN,
        api_key=self.FAKE_API_KEY,
        connection=connection)
    self.assertEqual(breeze.EventCheckIn('person_id', 'event_id'),
                     json.loads(response.content))
  
  def testEventCheckOut(self):
    response = MockResponse(200, json.dumps({'event_id': 'Some Data.'}))
    connection = MockConnection(response)
    breeze = BreezeApi(
        breeze_url=self.FAKE_SUBDOMAIN,
        api_key=self.FAKE_API_KEY,
        connection=connection)
    self.assertEqual(breeze.EventCheckOut('person_id', 'event_id'),
                     json.loads(response.content))


if __name__ == '__main__':
  unittest.main()
