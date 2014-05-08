import requests

from utils import make_enum

ENDPOINTS = make_enum('BreezeApiURL',
    PEOPLE = '/api/people',
    EVENTS = '/api/events',
    PROFILE_FIELDS = '/api/profile')

class BreezeError(Exception):
  pass


class BreezeApi(object):
  def __init__(self, subdomain, api_key, connection=requests.Session()):
    if (subdomain and
        subdomain.startswith('https://') and
        subdomain.endswith('.breezechms.com')):
      self.subdomain = subdomain
    else:
      raise BreezeError('You must provide your subdomain as ',
          'https://[subdomain].breezechms.com: [%s]' % subdomain)
    
    if api_key:
      self.api_key = api_key
    else:
      raise BreezeError('You must provide an API key.')
    
    self.connection = connection

  
  def make_request(self, endpoint, params=None, headers=None, timeout=60):
    headers = {'Content-Type': 'application/json',
               'Api-Key': self.api_key}
    
    if params is None:
      params = {}
    kw = dict(params=params, headers=headers, timeout=timeout)
    url = '%s%s' % (self.subdomain, endpoint)
    
    response = self.connection.post(url, **kw)
    try:
        response = response.json()
    except requests.ConnectionError as error:
        raise BreezeError(error.message)
    else:
        if not self.request_succeeded(response):
            raise BreezeError(response)
        return response
  
  def request_succeeded(self, response):
    return not (('error' in response) or ('errorCode' in response))

  
  def get_people(self):
    return self.make_request(ENDPOINTS.PEOPLE)

  
  def get_profile_fields(self):
    return self.make_request(ENDPOINTS.PROFILE_FIELDS)
  
  def get_person_details(self, person_id):
    return self.make_request('%s/%s' % (ENDPOINTS.PEOPLE, str(person_id)))
  
  def get_events(self, start_date=None, end_date=None):
    """
    Retrieve events in given date.
    defaults to current month if no parameters supplied.
    """
    params = []
    if start_date:
      params.append('start=%s' % start_date)
    if end_date:
      params.append('end=%s' % end_date)
    return self.make_request('%s/?%s' % (ENDPOINTS.EVENTS, '&'.join(params)))
  
  def event_check_in(self, person_id, event_instance_id):
    """
    Check In Person
     /api/events/attendance/add?person_id=[PERSONID]&instance_id=[INSTANCEID]
    """
    return self.make_request('%s/attendance/add?person_id=%s&instance_id=%s' % (
        ENDPOINTS.EVENTS, str(person_id), str(event_instance_id)))
    
  
  def event_check_out(self, person_id, event_instance_id):
    """
    Remove Checked In Person
     /api/events/attendance/delete?person_id=[PERSONID]&instance_id=[INSTANCEID]
    """
    return self.make_request(
        '%s/attendance/delete?person_id=%s&instance_id=%s' % (
            ENDPOINTS.EVENTS, str(person_id), str(event_instance_id)))


