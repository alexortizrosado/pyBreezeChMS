from utils import make_enum

ENDPOINTS = make_enum('BreezeApiURL',
    PEOPLE = '/api/people',
    EVENTS = '/api/events',
    PROFILE_FIELDS = '/api/profile')

class BreezeError(Exception):
  pass
	

class BreezeApi(object):
  """
  The Breeze API allows you to build custom applications integrated with the
  Breeze database.
  """

  def __init__(self, subdomain, api_key):
    if (subdomain and 
        subdomain.startswith('https://') and 
        subdomain.endswith('.breezechms.com')):
      self.subdomain = subdomain
    else:
      raise BreezeError('You must provide your subdomain as ',
          'https://[subdomain].breezechms.com: %s' % subdomain)

    if api_key:
      self.api_key = api_key
    else:
      raise BreezeError('You must provide an API key.')

  def _make_request(self, url, method='POST', data=None, params=None,
                    headers=None, timeout=60):
    raise NotImplementedError
    
  def get_people(self):
    """
    List People
      /api/people
    """
    raise NotImplementedError
	
  def get_profile_fields(self):
    """
    View Profile Fields
      /api/profile
    """
    raise NotImplementedError
    
  def get_person_details(self, person_id):
    """
    View Person Details (updated to include fields and family data)
     /api/people/[PERSONID]
    """
    raise NotImplementedError
    
  def get_events(self, start_date=None, end_date=None):
    """
    Retrieve events in given date.
    defaults to current month if no parameters supplied.
     /api/events?start=1-5-2013&end=4-24-2014
    """
    raise NotImplementedError
    
  def event_check_in(self, person_id, event_id):
    """
    Check In Person
     /api/events/attendance/add?person_id=[PERSONID]&instance_id=[INSTANCEID]
    """
    raise NotImplementedError
    
  def event_check_out(self, person_id, event_id):
    """
    Remove Checked In Person
     /api/events/attendance/delete?person_id=[PERSONID]&instance_id=[INSTANCEID]
    """
    raise NotImplementedError

