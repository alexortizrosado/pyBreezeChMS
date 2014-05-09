import json
import unittest

from breeze.breeze import BreezeApi
from breeze.breeze import BreezeError


class MockConnection(object):
  def __init__(self, response):
    self.response = response
    self.headers = {}
  
  def post(self, url, params, headers, *args, **kwargs):
    return self.response

class MockResponse(object):
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
  
  def test_invalid_subdomain(self):
    self.assertRaises(BreezeError,
        lambda: BreezeApi(self.FAKE_API_KEY, 'invalid-subdomain'))
    self.assertRaises(BreezeError,
        lambda: BreezeApi(self.FAKE_API_KEY, 'http://blah.breezechms.com'))
    self.assertRaises(BreezeError,
        lambda: BreezeApi(self.FAKE_API_KEY, ''))
  
  def test_missing_api_key(self):
    self.assertRaises(BreezeError,
        lambda: BreezeApi(None, self.FAKE_SUBDOMAIN))
    self.assertRaises(BreezeError,
        lambda: BreezeApi('', self.FAKE_SUBDOMAIN))
  
  def test_get_people(self):
    response = MockResponse(200, json.dumps({'name': 'Some Data.'}))
    connection = MockConnection(response)
    breeze = BreezeApi(self.FAKE_SUBDOMAIN, self.FAKE_API_KEY, connection)
    self.assertEqual(breeze.get_people(), json.loads(response.content))
  
  def test_get_profile_fields(self):
    response = MockResponse(200, json.dumps({'name': 'Some Data.'}))
    connection = MockConnection(response)
    breeze = BreezeApi(self.FAKE_SUBDOMAIN, self.FAKE_API_KEY, connection)
    self.assertEqual(breeze.get_profile_fields(), json.loads(response.content))
  
  def test_get_person_details(self):
    response = MockResponse(200, json.dumps({'person_id': 'Some Data.'}))
    connection = MockConnection(response)
    breeze = BreezeApi(self.FAKE_SUBDOMAIN, self.FAKE_API_KEY, connection)
    self.assertEqual(breeze.get_person_details('person_id'),
                     json.loads(response.content))
  
  def test_get_events(self):
    response = MockResponse(200, json.dumps({'event_id': 'Some Data.'}))
    connection = MockConnection(response)
    breeze = BreezeApi(self.FAKE_SUBDOMAIN, self.FAKE_API_KEY, connection)
    self.assertEqual(breeze.get_events(),json.loads(response.content))
  
  def test_event_check_in(self):
    response = MockResponse(200, json.dumps({'event_id': 'Some Data.'}))
    connection = MockConnection(response)
    breeze = BreezeApi(self.FAKE_SUBDOMAIN, self.FAKE_API_KEY, connection)
    self.assertEqual(breeze.event_check_in('person_id', 'event_id'),
                     json.loads(response.content))
  
  def test_event_check_out(self):
    response = MockResponse(200, json.dumps({'event_id': 'Some Data.'}))
    connection = MockConnection(response)
    breeze = BreezeApi(self.FAKE_SUBDOMAIN, self.FAKE_API_KEY, connection)
    self.assertEqual(breeze.event_check_out('person_id', 'event_id'),
                     json.loads(response.content))


if __name__ == '__main__':
  unittest.main()
