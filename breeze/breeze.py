from utils import make_enum

ENDPOINTS = make_enum('BreezeApiURL',
    PEOPLE = '/api/people',
    EVENTS = '/api/events',
    PROFILE_FIELDS = '/api/profile')

class BreezeError(Exception):
  pass
	

class BreezeApi(object):
	"""
	The Breeze API allows you to build custom applications integrated with the Breeze database.
	"""

  def __init__(self, subdomain, api_key):
    if (subdomain and 
        subdomain.startswith('https://') and 
        subdomain.endswith('.breezechms.com')):
      self.subdomain = subdomain
    else:
      raise BreezeError('You must provide your subdomain as https://[subdomain].breezechms.com: %s' % subdomain)

    if api_key:
      self.api_key = api_key
    else:
      raise BreezeError('You must provide an API key.')

  def make_request(self, url, method='POST', data=None, params=None, headers=None, timeout=60):
    raise NotImplementedError
    
  def get_people(self):
    # List People
    # https://[SUBDOMAIN].breezechms.com/api/people
    raise NotImplementedError
	
  def get_profile_fields(self):
    # View Profile Fields
    # https://[SUBDOMAIN].breezechms.com/api/profile
    raise NotImplementedError
    
  def get_person_details(self, person_id):
    # View Person Details (updated to include fields and family data)
    # https://[SUBDOMAIN].breezechms.com/api/people/[PERSONID]
    raise NotImplementedError
    
  def get_events(self, start_date, end_date):
    # Retrieve Events in Given Date (example dates left in for formatting example; defaults to current month if no parameters supplied)
    # https://[SUBDOMAIN].breezechms.com/api/events?start=1-5-2013&end=4-24-2014
    raise NotImplementedError
    
  def event_check_in(self, person_id, event_id):
    # Check In Person
    # https://[SUBDOMAIN].breezechms.com/api/events/attendance/add?person_id=[PERSONID]&instance_id=[INSTANCEID]
    raise NotImplementedError
    
  def event_check_out(self, person_id, event_id):
    # Remove Checked In Person
    # https://[SUBDOMAIN].breezechms.com/api/events/attendance/delete?person_id=[PERSONID]&instance_id=[INSTANCEID]
    raise NotImplementedError

