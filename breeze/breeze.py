"""Python wrapper for Breeze ChMS API: http://breezechms.com/docs#extensions_api

The Breeze API allows churches to build custom functionality integrated with
Breeze.

Usage:
  from breeze import breeze

  breeze_api = breeze.BreezeApi(
      breeze_url='https://demo.breezechms.com',
      api_key='5c2d2cbacg3...')
  people = breeze_api.GetPeople();

  for person in people:
    print '%s %s' % (person['first_name'], person['last_name'])
"""

__author__ = 'alex@rohichurch.org (Alex Ortiz-Rosado)'

import requests

from utils import make_enum

ENDPOINTS = make_enum(
    'BreezeApiURL',
    PEOPLE = '/api/people',
    EVENTS = '/api/events',
    PROFILE_FIELDS = '/api/profile',
    CONTRIBUTIONS = '/api/giving',
    FUNDS = '/api/funds')

class BreezeError(Exception):
  pass


class BreezeApi(object):
  """A wrapper for the Breeze REST API."""

  def __init__(self, breeze_url, api_key, debug=False, dry_run=False,
               connection=requests.Session()):
    """Instantiates the BreezeApi with your Breeze account information.

    Args:
      breeze_url: Fully qualified domain for your organizations Breeze service.
      api_key: Unique Breeze API key. For instructions on finding your
               organizations API key, see:
               http://breezechms.com/docs#extensions_api
      debug: Enable debug output.
      dry_run: Enable no-op mode, which disables requests from being made. When
               combined with debug, this allows debugging requests without
               affecting data in your Breeze account."""

    self.breeze_url = breeze_url
    self.api_key = api_key
    self.debug = debug
    self.dry_run = dry_run
    self.connection = connection

    if not (self.breeze_url and
        # TODO(alex): use urlparse to check url format.
        self.breeze_url.startswith('https://') and
        self.breeze_url.endswith('.breezechms.com')):
      raise BreezeError('You must provide your breeze_url as ',
          'subdomain.breezechms.com')

    if not self.api_key:
      raise BreezeError('You must provide an API key.')

  def _Request(self, endpoint, params=None, headers=None, timeout=60):
    """Makes an HTTP request to a given url.

    Args:
      endpoint: URL where the service can be accessed.
      params: Query parameters to append to endpoint url.
      headers: HTTP headers; used for authenication parameters.
      timeout: Timeout in seconds for HTTP request.

    Returns:
      HTTP response

    Throws:
      BreezeError if connection or request fails.
    """
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
      if not self._RequestSucceeded(response):
        raise BreezeError(response)
      return response

  def _RequestSucceeded(self, response):
    """Predicate to ensure that the HTTP request succeeded."""
    return not (('error' in response) or ('errorCode' in response))


  def GetPeople(self, limit=None, offset=None, details=False):
    """List people from your database.

    Args:
      limit: Number of people to return. If None, will return all people.
      offset: Number of people to skip before beginning to return results.
              Can be used in conjunction with limit for pagination.
      details: Option to return all information (slower) or just names.

    returns:
      JSON response. For example:
      {
        "id":"157857",
        "first_name":"Thomas",
        "last_name":"Anderson",
        "path":"img\/profiles\/generic\/blue.jpg"
      },
      {
        "id":"157859",
        "first_name":"Kate",
        "last_name":"Austen",
        "path":"img\/profiles\/upload\/2498d7f78s.jpg"
      },
      {
        ...
      }
    """

    params = []
    if limit:
      params.append('limit=%s' % limit)
    if offset:
      params.append('offset=%s' % offset)
    if details:
      params.append('details=1')
    return self._Request('%s/?%s' % (ENDPOINTS.PEOPLE, '&'.join(params)))


  def GetProfileFields(self):
    """List profile fields from your database.

    Returns:
      JSON response.
    """
    return self._Request(ENDPOINTS.PROFILE_FIELDS)

  def GetPersonDetails(self, person_id):
    """Retrieve the details for a specific person by their ID.

    Args:
      person_id: Unique id for a person in Breeze database.

    Returns:
      JSON response.
    """
    return self._Request('%s/%s' % (ENDPOINTS.PEOPLE, str(person_id)))

  def GetEvents(self, start_date=None, end_date=None):
    """Retrieve all events for a given date range.
    Args:
      start_date: Start date; defaults to first day of the current month.
      end_date: End date; defaults to last day of the current month

    Returns:
      JSON response.
    """
    params = []
    if start_date:
      params.append('start=%s' % start_date)
    if end_date:
      params.append('end=%s' % end_date)
    return self._Request('%s/?%s' % (ENDPOINTS.EVENTS, '&'.join(params)))

  def EventCheckIn(self, person_id, event_instance_id):
    """Checks in a person into an event.

    Args:
      person_id: id for a person in Breeze database.
      event_instance_id: id for event instance to check into.

    Returns:
      True if check-in succeeds; False if check-in fails.
    """
    return self._Request('%s/attendance/add?person_id=%s&instance_id=%s' % (
        ENDPOINTS.EVENTS, str(person_id), str(event_instance_id)))


  def EventCheckOut(self, person_id, event_instance_id):
    """Remove the attendance for a person checked into an event.

    Args:
      person_id: Breeze ID for a person in Breeze database.
      event_instance_id: id for event instance to check out (delete).

    Returns:
      True if check-in succeeds; False if check-in fails.
    """
    return self._Request(
        '%s/attendance/delete?person_id=%s&instance_id=%s' % (
            ENDPOINTS.EVENTS, str(person_id), str(event_instance_id)))

  def AddContribution(self, date=None, name=None, person_id=None, uid=None,
                      processor=None, method=None, funds_json=None,
                      amount=None, group=None, batch_number=None,
                      batch_name=None):
    """Add a contribution to Breeze.

    Args:
      date: Date of transaction in DD-MM-YYYY format (ie. 24-5-2015)
      name: Name of person that made the transaction. Used to help match up
            contribution to correct profile within Breeze.  (ie. John Doe)
      person_id: The Breeze ID of the donor. If unknown, use UID instead of
                 person id  (ie. 1234567)
      uid: The unique id of the person sent from the giving platform. This
           should be used when the Breeze ID is unknown. Within Breeze a user
           will be able to associate this ID with a given Breeze ID.
           (ie. 9876543)
      email: Email address of donor. If no person_id is provided, used to help
             automatically match the person to the correct profile.
             (ie. sample@breezechms.com)
      street_address: Donor's street address. If person_id is not provided,
                      street_address will be used to help automatically match
                      the person to the correct profile.  (ie. 123 Sample St)
      processor: The name of the processor used to send the payment. Used in
                 conjunction with uid. Not needed if using Breeze ID.
                 (ie. SimpleGive, BluePay, Stripe)
      method: The payment method. (ie. Check, Cash, Credit/Debit Online,
              Credit/Debit Offline, Donated Goods (FMV), Stocks (FMV),
              Direct Deposit)
      funds_json: JSON string containing fund names and amounts. This allows
                  splitting fund giving. The ID is optional. If present, it must
                  match an existing fund ID and it will override the fund name.
                  ie. [ {
                          'id':'12345',
                          'name':'General Fund',
                          'amount':'100.00'
                        },
                        {
                          'name':'Missions Fund',
                          'amount':'150.00'
                        }
                      ]
      amount: Total amount given. Must match sum of amount in funds_json.
      group: This will create a new batch and enter all contributions with the
             same group into the new batch. Previous groups will be remembered
             and so they should be unique for every new batch. Use this if
             wanting to import into the next batch number in a series.
      batch_number: The batch number to import contributions into. Use group
                    instead if you want to import into the next batch number.
      batch_name: The name of the batch. Can be used with batch number or group.

    Returns:
      Payment Id.

    Throws:
      BreezeError on failure to add contribution.
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
      params.append('batch_name=%s' % batch_name)
    response = self._Request('%s/add?%s' % (ENDPOINTS.CONTRIBUTIONS,
                                            '&'.join(params)))
    if response['success']:
      return response['payment_id']
    else:
      raise BreezeError('Failed to delete contribution: ', response['errors'])

  def EditContribution(self, payment_id=None, date=None, name=None,
                       person_id=None, uid=None, processor=None, method=None,
                       funds_json=None, amount=None, group=None,
                       batch_number=None, batch_name=None):
    """Edit an existing contribution.

    Args:
      payment_id: The ID of the payment that should be modified.
      date: Date of transaction in DD-MM-YYYY format (ie. 24-5-2015)
      name: Name of person that made the transaction. Used to help match up
            contribution to correct profile within Breeze.  (ie. John Doe)
      person_id: The Breeze ID of the donor. If unknown, use UID instead of
                 person id  (ie. 1234567)
      uid: The unique id of the person sent from the giving platform. This
           should be used when the Breeze ID is unknown. Within Breeze a user
           will be able to associate this ID with a given Breeze ID.
           (ie. 9876543)
      email: Email address of donor. If no person_id is provided, used to help
             automatically match the person to the correct profile.
             (ie. sample@breezechms.com)
      street_address: Donor's street address. If person_id is not provided,
                      street_address will be used to help automatically match
                      the person to the correct profile.  (ie. 123 Sample St)
      processor: The name of the processor used to send the payment. Used in
                 conjunction with uid. Not needed if using Breeze ID.
                 (ie. SimpleGive, BluePay, Stripe)
      method: The payment method. (ie. Check, Cash, Credit/Debit Online,
              Credit/Debit Offline, Donated Goods (FMV), Stocks (FMV),
              Direct Deposit)
      funds_json: JSON string containing fund names and amounts. This allows
                  splitting fund giving. The ID is optional. If present, it must
                  match an existing fund ID and it will override the fund name.
                  ie. [ {
                          'id':'12345',
                          'name':'General Fund',
                          'amount':'100.00'
                        },
                        {
                          'name':'Missions Fund',
                          'amount':'150.00'
                        }
                      ]
      amount: Total amount given. Must match sum of amount in funds_json.
      group: This will create a new batch and enter all contributions with the
             same group into the new batch. Previous groups will be remembered
             and so they should be unique for every new batch. Use this if
             wanting to import into the next batch number in a series.
      batch_number: The batch number to import contributions into. Use group
                    instead if you want to import into the next batch number.
      batch_name: The name of the batch. Can be used with batch number or group.

    Returns:
      Payment id.

    Throws:
      BreezeError on failure to edit contribution.
    """
    params = []
    if payment_id:
      params.append('payment_id=%s' % payment_id)
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
      params.append('batch_name=%s' % batch_name)
    response = self._Request('%s/edit?%s' % (ENDPOINTS.CONTRIBUTIONS,
                                            '&'.join(params)))
    if not response['success']:
      raise BreezeError('Failed to edit contribution: ', response['errors'])
    return response['payment_id']

  def DeleteContribution(self, payment_id):
    """Delete an existing contribution.

    Args:
      payment_id: The ID of the payment that should be deleted.

    Returns:
      Payment id.

    Throws:
      BreezeError on failure to delete contribution.
    """
    response = self._Request('%s/delete?payment_id=%s' % (
        ENDPOINTS.CONTRIBUTIONS, payment_id))
    if not response['success']:
      raise BreezeError('Failed to delete contribution: ', response['errors'])
    return response['payment_id']

  def ListContributions(self, start_date, end_date, person_id=None,
                        include_family=False, amount_min=None, amount_max=None,
                        method_ids=None, fund_ids=None, envelope_number=None,
                        batches=None, forms=None):
    """Retrieve a list of contributions.

    Args:
      start_date: Find contributions given on or after a specific date
                  (ie. 2015-1-1); required.
      end_date: Find contributions given on or before a specific date
                (ie. 2018-1-31); required.
      person_id: ID of person's contributions to fetch. (ie. 9023482)
      include_family: Include family members of person_id (must provide
                      person_id); default: False.
      amount_min: Contribution amounts equal or greater than.
      amount_max: Contribution amounts equal or less than.
      method_ids: List of method IDs.
      fund_ids: List of fund IDs.
      envelope_number: Envelope number.
      batches: List of Batch numbers.
      forms: List of form IDs.

    Returns:
      List of matching contributions.

    Throws:
      BreezeError on malformed request.
    """
    params = []
    params.append('start_date=%s' % start_date)
    params.append('end_date=%s' % end_date)
    if person_id:
      params.append('person_id=%s' % person_id)
    if include_family:
      if not person_id:
        raise BreezeError('include_family requires a person_id.')
      params.append('include_family=1')
    if amount_min:
      params.append('amount_min=%s' % amount_min)
    if amount_max:
      params.append('amount_max=%s' % amount_max)
    if method_ids:
      params.append('method_ids=%s' % '-'.join(method_ids))
    if fund_ids:
      params.append('fund_ids=%s' % '-'.join(fund_ids))
    if envelope_number:
      params.append('envelope_number=%s' % envelope_number)
    if batches:
      params.append('batches=%s' % '-'.join(batches))
    if forms:
      params.append('forms=%s' % '-'.join(forms))
    response = self._Request('%s/list?%s' % (ENDPOINTS.CONTRIBUTIONS,
                                            '&'.join(params)))
    if not response['success']:
      raise BreezeError('Failed to edit contribution: ', response['errors'])
    return response

  def ListFunds(self, include_totals=False):
    """List all funds.

    Args:
      include_totals: Amount given to the fund should be returned.

    Returns:
      JSON Reponse.
    """
    params = []
    if include_totals:
      params.append('include_totals=1')
    return self._Request('%s/list?%s' % (
        ENDPOINTS.FUNDS, '&'.join(params)))
    if response['success']:
      return response['payment_id']
    else:
      raise BreezeError('Failed to delete contribution: ', response['errors'])
