import unittest

from breeze.breeze import BreezeApi
from breeze.breeze import BreezeError

class BreezeApiTestCase(unittest.TestCase):
  def setUp(self):
    self.FAKE_API_KEY = 'fak3ap1k3y'
    self.FAKE_SUBDOMAIN = 'https://rohichurh.breezechms.com'
    self.breeze = BreezeApi(self.FAKE_SUBDOMAIN, self.FAKE_API_KEY)
    
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

  def test_make_request(self):
    self.assertRaises(NotImplementedError, 
        lambda: self.breeze._make_request('/request', 'POST'))

  def test_get_people(self):
    self.assertRaises(NotImplementedError, 
        lambda: self.breeze.get_people())

  def test_get_profile_fields(self):
    self.assertRaises(NotImplementedError, 
        lambda: self.breeze.get_profile_fields())

  def test_get_person_details(self):
    self.assertRaises(NotImplementedError, 
        lambda: self.breeze.get_person_details('person_id'))

  def test_get_person_details(self):
    self.assertRaises(NotImplementedError, 
        lambda: self.breeze.get_events('1-5-2004', '1-6-2004'))
    
  def test_event_check_in(self):
    self.assertRaises(NotImplementedError, 
        lambda: self.breeze.event_check_in('person_id', 'event_id'))

  def test_event_check_out(self):
    self.assertRaises(NotImplementedError, 
        lambda: self.breeze.event_check_out('person_id', 'event_id'))
    
if __name__ == '__main__':
  unittest.main()
