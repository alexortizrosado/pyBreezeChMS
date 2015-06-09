import requests

from utils import make_enum

ENDPOINTS = make_enum('BreezeApiURL',
    PEOPLE = '/api/people',
    EVENTS = '/api/events',
    PROFILE_FIELDS = '/api/profile',
    CONTRIBUTIONS = '/api/giving')

class BreezeError(Exception):
  pass


class BreezeApi(object):

  def __init__(self, breeze_url, api_key, debug=False, dry_run=False, connection=requests.Session()):
    self.breeze_url = breeze_url
    self.api_key = api_key
    self.debug = debug
    self.dry_run = dry_run
    self.connection = connection

    if not (self.breeze_url and
        self.breeze_url.endswith('.breezechms.com')):
      raise BreezeError('You must provide your breeze_url as ',
          'subdomain.breezechms.com')
    
    if not self.api_key:
      raise BreezeError('You must provide an API key.')

  def _request(self, endpoint, params=None, headers=None, timeout=60):
    headers = {'Content-Type': 'application/json',
               'Api-Key': self.api_key}
    
    if params is None:
      params = {}
    kw = dict(params=params, headers=headers, timeout=timeout)
    url = '%s%s' % (self.breeze_url, endpoint)

    if self.debug:
      print 'Making request to %s' % url
    if self.dry_run:
      return

    response = self.connection.post(url, **kw)
    try:
        response = response.json()
    except requests.ConnectionError as error:
        raise BreezeError(error.message)
    else:
        if not self._request_succeeded(response):
            raise BreezeError(response)
        return response
  
  def _request_succeeded(self, response):
    return not (('error' in response) or ('errorCode' in response))

  
  def get_people(self, limit=None, start=None, details=False):
    params = []
    if limit:
      params.append('limit=%s' % limit)
    if start:
      params.append('start=%s' % start)
    if details:
      params.append('details=1')
    return self._request('%s/?%s' % (ENDPOINTS.PEOPLE, '&'.join(params)))

  
  def get_profile_fields(self):
    return self._request(ENDPOINTS.PROFILE_FIELDS)
  
  def get_person_details(self, person_id):
    return self._request('%s/%s' % (ENDPOINTS.PEOPLE, str(person_id)))
  
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
    return self._request('%s/?%s' % (ENDPOINTS.EVENTS, '&'.join(params)))
  
  def event_check_in(self, person_id, event_instance_id):
    """
    Check In Person
     /api/events/attendance/add?person_id=[PERSONID]&instance_id=[INSTANCEID]
    """
    return self._request('%s/attendance/add?person_id=%s&instance_id=%s' % (
        ENDPOINTS.EVENTS, str(person_id), str(event_instance_id)))
    
  
  def event_check_out(self, person_id, event_instance_id):
    """
    Remove Checked In Person
     /api/events/attendance/delete?person_id=[PERSONID]&instance_id=[INSTANCEID]
    """
    return self._request(
        '%s/attendance/delete?person_id=%s&instance_id=%s' % (
            ENDPOINTS.EVENTS, str(person_id), str(event_instance_id)))

  def add_contribution(self, date=None, name=None, person_id=None, uid=None,
                       processor=None, method=None, funds_json=None,
                       amount=None, group=None, batch_number=None,
                       batch_name=None):
    """
    api/giving/add?
      date=[DATE]&
      name=[NAME]&
      person_id=[PERSON_ID]&
      uid=[UID]&
      processor=[PROCESSOR]&
      method=[METHOD]&
      funds_json=[FUNDS_JSON]&
      amount=[AMOUNT]&
      group=[GROUP]&
      batch_number=[BATCH NUMBER]&
      batch_name=[BATCH_NAME]
    """
    params = []
    if date:
      params.append('date=%s' % date)

    if name:
      params.append('name=%s' % name)

    if person_id:
      params.append('person_id=%s' % person_id)

    if uid:
      params.append('uid=%s' % uid)

    if processor:
      params.append('processor=%s' % processor)

    if method:
      params.append('method=%s' % method)

    if funds_json:
      params.append('funds_json=%s' % funds_json)

    if amount:
      params.append('amount=%s' % amount)

    if group:
      params.append('group=%s' % group)

    if batch_number:
      params.append('batch_number=%s' % batch_number)

    if batch_name:
      params.append('batch_name=%s' % dabatch_namete)
    response = self._request('%s/add?%s' % (ENDPOINTS.CONTRIBUTIONS, '&'.join(params)))
    if not response['success']:
      self.logger.error(response['errors'])




