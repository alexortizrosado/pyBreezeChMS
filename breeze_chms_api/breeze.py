"""Python wrapper for Breeze ChMS API: http://www.breezechms.com/api

This API wrapper allows churches to build custom functionality integrated with
Breeze Church Management System.

Usage:
  from breeze import breeze

  breeze_api = breeze.breeze_api()
  # But see the documentation, there's more to the above.
  people = breeze_api.get_people();

  for person in people:
    print f"{person['first_name']} {person['last_name']}"

  Adapted from the original by alexortizrosado@gmail.com (Alex Ortiz-Rosado)
"""

__author__ = 'daw30410@yahoo.com (David A. Willcox)'

import logging
import requests
import json
import combine_settings
from enum import Enum
from typing import Union, List, Mapping, Sequence, Set, Dict


class ENDPOINTS(Enum):
    PEOPLE = 'people'
    EVENTS = 'events'
    PROFILE_FIELDS = 'profile'
    CONTRIBUTIONS = 'giving'
    FUNDS = 'funds'
    PLEDGES = 'pledges'
    TAGS = 'tags'
    ACCOUNT = 'account'
    FORMS = 'forms'
    VOLUNTEERS = 'volunteers'


BREEZE_URL_KEY = 'breeze_url'
BREEZE_API_KEY_KEY = 'api_key'
HELPER_CONFIG_FILE = 'breeze_maker.yml'

# Valid parameters for various calls
_GET_PEOPLE_PARAMS = {'limit', 'offset', 'details', 'filter_json'}
_ADD_PERSON_PARAMS = {'first', 'last', 'fields_json'}
_UPDATE_PERSON_PARAMS = {'person_id', 'fields_json'}
_LIST_EVENTS_PARAMS = {'start', 'end'}
_ADD_EVENT_PARAMS = {'name', 'starts_on', 'ends_on', 'all_day',
                     'description', 'category_id', 'event_id',
                     }
_ADD_CONTRIBUTION_PARAMS = {'amount',
                            'batch_name',
                            'batch_number',
                            'date',
                            'email',
                            'funds_json',
                            'group',
                            'method',
                            'name',
                            'note',
                            'payment_id',
                            'person_id',
                            'processor',
                            'street_address',
                            'uid',
                            }
_EDIT_CONTRIBUTION_PARAMS = set(_ADD_CONTRIBUTION_PARAMS)
_EDIT_CONTRIBUTION_PARAMS.add('person_json')
_LIST_CONTRIBUTION_PARAMS = {'start', 'end', 'person_id', 'include_family',
                             'amount_min', 'amount_max', 'method_ids',
                             'fund_ids', 'envelope_number', 'batches',
                             'forms',
                             }


class BreezeError(Exception):
    """Exception for BreezeApi."""

    def __init__(self, *args):
        Exception.__init__(self, args)


class BreezeBadParameter(BreezeError):
    def __init__(self, *args):
        BreezeError.__init__(self, args)

def _transform_setting(key: str, val: Union[int, Mapping, Sequence, None]) -> \
        Union[str, None]:
    """
    Transform a setting value into something usable in the REST API
    :param val: Value from api
    :return: val converted as follows:
        None (or empty): None
        val if val is already a string
        json_dumps(val) if key ends with _json
        Sequence: '-'.join(str(v) for v in val if v]
        bool: '1' if val is True else None
        Otherwise: str(val)
    """
    if not val:
        return None
    elif isinstance(val, str):
        return val
    elif key.endswith('_json'):
        return json.dumps(val)
    elif isinstance(val, Sequence):
        return '-'.join([str(v) for v in val if v])
    elif isinstance(val, bool):
        return '1' if val else '0'
    else:
        return str(val)


def _transform_settings(args: Mapping) -> dict:
    """
    Given a mapping of parameter:value, return a dict with all of the parameters
    that actually had a value, but with values converted to API-compatible strings
    using _transform_setting().
    :param args: Mapping of parameter:value
    :return: New dict with values suitably transformed
    """
    return {k: _transform_setting(k, v) for k, v in args.items() if v}


def _check_illegal_param(args: Mapping, valid_keys: Set) -> None:
    """
    Check to be sure all parameters are valid.
    :param args:    Map of function arguments
    :param valid_keys: Set of valid keys for this function
    :return: None (implies success)
    :raises: BreezeBadParameter if unexpected setting found
    """
    bad_keys = set(args.keys()).difference(valid_keys)
    if bad_keys:
        raise BreezeBadParameter(f'Unexpected parameter(s): {",".join(list(bad_keys))}')


class BreezeApi(object):
    """A wrapper for the Breeze REST API."""

    def __init__(self, breeze_url, api_key,
                 dry_run=False,
                 connection=requests.Session()):
        """
        Instantiates the BreezeApi with your Breeze account information.
        :param breeze_url: Fully qualified domain for your organization's Breeze service
        :param api_key: Unique Breeze API key. For instructions on finding your
                        key, see http://breezechms.com/docs#extensions_api
        :param dry_run: Enable n-op mode for testing, which disables requests from being
                        made. When combined with debug,, this allows debugging requests
                        without affecting data in your Breeze account
        :param connection: Internet connection session. By default BreezeAPI creates
                        one, but this allows a mock connection for testing.
        """

        self.breeze_url = breeze_url
        self.api_key = api_key
        self.dry_run = dry_run
        self.connection = connection

        # TODO(alex): use urlparse to check url format.
        if not (self.breeze_url and self.breeze_url.startswith('https://') and
                (self.breeze_url.find('.breezechms.') > 0)):
            raise BreezeError('You must provide your breeze_url as ',
                              'subdomain.breezechms.com')

        if not self.api_key:
            raise BreezeError('You must provide an API key.')

        # Profile field id to field spec
        self.profile_spec_by_id: Dict[str, dict] = {}
        # Profile field name to field spec
        self.profile_spec_by_name: Dict[str, dict] = {}
        # All profile field specifications (unwound from original spec)
        self.profile_specs: List[dict] = []
        # Raw profile fields description as returned by Breeze
        self.profile_fields: List[Mapping] = []

    def _request(self,
                 endpoint: ENDPOINTS,
                 command: str = '',
                 params: Mapping[str, Union[str, int, float, Mapping, Sequence]] \
                         = dict(),
                 headers: dict = dict(),
                 timeout: int = 60,
                 ):
        """
        Make an HTTP request to a given url.
        :param endpoint: URL endpoint for the service. (contributions, people, etc.)
        :param command: Command for the endpoint. (add, list, etc.)
        :param params: Parameters for the command {name: value, ...}
        :param headers: Extra HTTP headers if needed
        :return: HTTP response
        :raises": BreezeError if connection or request fails
        """

        http_headers = {
            'Content-Type': 'application/json',
            'Api-Key': self.api_key
        }
        if headers:
            http_headers.update(headers)

        keywords = dict(headers=http_headers,
                        params=_transform_settings(params),
                        timeout=timeout)
        url = f"{self.breeze_url}/api/{endpoint.value}/{command}?"

        logging.debug('Making request to %s', url)
        if self.dry_run:
            return  # NOT TESTED

        try:
            response = self.connection.get(url, verify=True, **keywords)
            if not response.ok:
                raise BreezeError(response)
            response_json = response.json()
        except (requests.ConnectionError,
                requests.exceptions.ConnectionError) as error:
            raise BreezeError(error)

        if isinstance(response_json, dict):
            if response_json.get('errors') or response_json.get('errorCode'):
                raise BreezeError(response)
        logging.debug('JSON Response: %s', response_json)
        return response_json

    # ------------------ ACCOUNT

    def get_account_summary(self) -> dict:
        """Retrieve the details for a specific account using the API key 
          and URL. It can also work to see if the key and URL are valid.

        :return:
          JSON response. For example:
          {
            "id":"1234",
            "name":"Grace Church",
            "subdomain":"gracechurchdemo",
            "status":"1",
            "created_on":"2018-09-10 09:19:35",
            "details":{
                "timezone":"America/New_York",
                "country":{
                    "id":"2",
                    "name":"United States of America",
                    "abbreviation":"USA",
                    "abbreviation_2":"US",
                    "currency":"USD",
                    "currency_symbol":"$",
                    "date_format":"MDY",
                    "sms_prefix":"1"
                }
            }
          }
          """
        return self._request(ENDPOINTS.ACCOUNT, 'summary')  # NOT TESTED

    # ------------------ People

    def list_people(self, **kwargs) -> List[dict]:
        """
        List people from your database
        :param kwargs: Keyed parameters, all optional:
            limit: If set, number of people to return, If none, will return all people
            offset: Number of people to skip before beginning to return results.
            details: Boolean, if True, return all information, Otherwise just names.
            filter_json: Filter results based on criteria (tags, status, etc.)
                Refer to the list_profile_field response to show values you're
                searching for. Or see the API document for a slightly better
                explanation.
        :return:
          JSON response. For example:
          {
            "id":"157857",
            "first_name":"Thomas",
            "last_name":"Anderson",
            "path":"img/profiles/generic/blue.jpg"
          },
          {
            "id":"157859",
            "first_name":"Kate",
            "last_name":"Austen",
            "path":"img/profiles/upload/2498d7f78s.jpg"
          },
          {
            ...
          }
          """
        _check_illegal_param(kwargs, _GET_PEOPLE_PARAMS)
        # TODO Add test for filter_json.
        return self._request(ENDPOINTS.PEOPLE, params=kwargs)

    def _build_profile_fields(self) -> List[dict]:
        """
        Build the list of profile fields.
        :return: Profile field list as returned by Breeze
        But the individual fields have an added 'qualified_name' entry that
        includes section '{section name}:{field name}'
        """
        # Profile fields by id
        # self.profile_spec_by_id: Mapping[str, dict] = {}
        # Profile field name to id
        # self.profile_spec_by_name: Mapping[str, str] = {}
        # All profile fields specs
        # self.profile_specs: List[dict] = []
        if not self.profile_fields:
            # First time. Get profile fields from Breeze
            self.profile_fields = self._request(ENDPOINTS.PROFILE_FIELDS)
            for section in self.profile_fields:
                for field in section.get('fields'):
                    field_name = field.get('name')
                    field_id = field.get('field_id')
                    field['section_spec'] = section
                    self.profile_spec_by_id[field_id] = field
                    self.profile_spec_by_name[field_name] = field
                    self.profile_specs.append(field)
        return self.profile_fields

    def get_profile_fields(self) -> List[dict]:
        """List profile fields from your database.
        To be clear, this is a list of profile sections, each section
        having a list of field specifications in that section.
        Each field specification has a new 'section_spec' item
        that refers back to the containing section, which
        can give the setion name among other things.

        :return: List of descriptors of profile fields
        """
        return self.profile_fields if self.profile_fields \
            else self._build_profile_fields()

    def get_field_spec_by_id(self, field_id: str) -> dict:
        """
        Return profile spec for given field id
        :param field_id: Field id
        :return: Field specification
        """
        if not self.profile_fields:
            self._build_profile_fields()
        return self.profile_spec_by_id.get(field_id)

    def get_field_spec_by_name(self, name: str) -> dict:
        """
        Return profile spec for named field
        :param name: Name of field
        :return: Field specification
        """
        if not self.profile_fields:
            self._build_profile_fields()
        return self.profile_spec_by_name.get(name)

    def get_person_details(self, person_id: str) -> dict:
        """
        Retrieve the details for a specific person by their ID.
        :param person_id: Unique id for a person in Breeze database.
        :return: JSON response.
        """
        return self._request(ENDPOINTS.PEOPLE, command=str(person_id))

    def field_value_from_name(self, field_name: str, person_details: dict) -> dict:
        """
        Get a profile field value from a person's profile data
        :param field_name: Name of the field
        :param person_details: Person's detail info
        :return: The field's value information
        """
        field_spec = self.get_field_spec_by_name(field_name)
        if not field_spec:
            return {}
        field_id = field_spec.get('field_id')
        return person_details.get('details').get(field_id)

    def add_person(self, **kwargs) -> str:
        """
        Add a new person to the database
        :param kwargs: Keyed parameters:
            first: The first name of the person.
            last: The last name of the person.
            fields_json: JSON string representing an array of fields to update.
                       Each array element must contain field id, field type, response,
                       and in some cases, more information.
                       eg. [ {
                               "field_id":"929778337",
                               "field_type":"email",
                               "response":"true",
                               "details":{
                                    "address": "tony@starkindustries.com",
                                    "is_private":1}
                             }
                           ].
                       Obtain such field information from get_profile_fields() or
                       use get_person_details() to see fields that already exist
                       for a specific person.
        :return: JSON response equivalent to get_person_details().
        """
        _check_illegal_param(kwargs, _ADD_PERSON_PARAMS)
        return self._request(ENDPOINTS.PEOPLE, command='add',
                             params=_transform_settings(kwargs))

    def update_person(self, **kwargs) -> dict:
        """
        Updates the details for a specific person in the database.

        :param kwargs:
          person_id: Unique id for a person in Breeze database.
          fields_json: JSON string representing an array of fields to update.
                       Each array element must contain field id, field type, response,
                       and in some cases, more information.
                       eg.eg. [ {
                               "field_id":"929778337",
                               "field_type":"email",
                               "response":"true",
                               "details":{
                                    "address": "tony@starkindustries.com",
                                    "is_private":1}
                             }
                           ].
                       Obtain such field information from get_profile_fields() or
                       use get_person_details() to see fields that already
                       exist for a specific person.
        :returns: JSON response equivalent to get_person_details(person_id).
        """
        _check_illegal_param(kwargs, _UPDATE_PERSON_PARAMS)
        return self._request(ENDPOINTS.PEOPLE, command='update', params=kwargs)

    # -------------------- Calendars and Events

    def list_calendars(self) -> List[dict]:
        """
        Return a list of calendars
        :return: List of descriptions of available calenders
        """
        return self._request(ENDPOINTS.EVENTS, command='calendars/list')

    def list_events(self, **kwargs) -> List[dict]:
        """
        Retrieve all events for a given date range.

        :param kwargs: Keyed parameters
          start: Start date; defaults to first day of the current month.
          end: End date; defaults to last day of the current month
        :return: JSON response
        """
        _check_illegal_param(kwargs, _LIST_EVENTS_PARAMS)
        return self._request(ENDPOINTS.EVENTS, params=kwargs)

    def list_event(self, instance_id: Union[str, int]) -> dict:
        """
        Return information about a specific event
        :param instance_id: ID of the event
        :return: json object with event data
        """
        return self._request(ENDPOINTS.EVENTS,
                             command='list_event',
                             params={'instance_id': instance_id})

    def add_event(self, **kwargs) -> str:
        """
        Add event for given date rage

        :param kwargs: Keyed parameters
          name: Name of event
          starts_on: Start datetimestamp (epoch time)
          ends_on: End datetimestamp (epoch time)
          all_day: boolean
          description: description of event (default none)
          category id: which calendar your event is on (defaults to primary)
          event id: series id
        :return: JSON response
        """

        _check_illegal_param(kwargs, _ADD_EVENT_PARAMS)
        return self._request(ENDPOINTS.EVENTS,
                             command='add',
                             params=_transform_settings(kwargs))

    def event_check_in(self, person_id, instance_id):
        """
        Checks a person in to an event.
        :param person_id: ID for person in Breeze database
        :param instance_id: ID for event to check in to
        :return: Request response
        """
        return self._request(ENDPOINTS.EVENTS, command='attendance/add',
                             params={'person_id': person_id,
                                     'instance_id': instance_id,
                                     'direction': 'in'})

    def event_check_out(self, person_id, instance_id):
        """
        Remove the attendance for a person checked into an event.
        :param person_id: Breeze ID for a person in Breeze database.
        :param instance_id: Breeze ID for a person in Breeze database.
        :return: True if check-out succeeds; False if check-out fails.

        Note: event_check_out() differs from delete_attendance() in that
        it adds a check-out record. (It also adds a check-in if the person
        isn't already checked in.) delete_attendance() removes all attendance
        records for the person.
        """
        return self._request(ENDPOINTS.EVENTS,
                             command='attendance/add',
                             params={'person_id': person_id,
                                     'instance_id': instance_id,
                                     'direction': 'out'})

    def delete_attendance(self, person_id, instance_id):
        """
        Delete all attendance records for a person from an event
        :param person_id: Id of person to remove
        :param instance_id: Event instance ID
        :return: True if delete succeeds
        """
        return self._request(ENDPOINTS.EVENTS,
                             command='attendance/delete',
                             params={'person_id': person_id,
                                     'instance_id': instance_id})

    def list_attendance(self, instance_id: Union[str, int], details: bool = False):
        """
        List attendance for an event
        :param instance_id: ID of the event
        :param details: If true, give details
        :return: List of people who attended this event
        """
        params = {'instance_id': instance_id}
        if details:
            params['details'] = 'true'
        return self._request(ENDPOINTS.EVENTS,
                             command='attendance/list',
                             params=params)

    def list_eligible_people(self, instance_id: Union[int, str]):
        """
        List people eligible for an event
        :param instance_id: ID of the event
        :return: List of eligible people
        """
        return self._request(ENDPOINTS.EVENTS, command='attendance/eligible',
                             params={'instance_id': instance_id})

    # ------------ Contributions

    def add_contribution(self, **kwargs) -> str:
        """
        Add a contribution to Breeze.Y
        :param kwargs: Keyed arguments as follows:
          date: Date of transaction in YYYY-MM-DD format (eg. 2016-05-24)
          person_id: The Breeze ID of the donor. If unknown, use UID instead of
                     person id (eg. 1234567)
          method: The payment method. (eg. Check, Cash, Credit/Debit Online,
                  Credit/Debit Offline, Donated Goods (FMV), Stocks (FMV),
                  Direct Deposit)
          funds_json: JSON object containing fund names and amounts. This
                      allows splitting fund giving. The ID is optional. If
                      present, it must match an existing fund ID and it will
                      override the fund name. In other words,
                      eg.. [ {
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
          group: This will create a new batch and enter all contributions with
                 the same group into the new batch. Previous groups will be
                 remembered and so they should be unique for every new batch.
                 Use this if wanting to import into the next batch number in a
                 series.
          batch_number: The batch number to import contributions into. Use
                        group instead if you want to import into the next batch
                        number.
          batch_name: The name of the batch. Can be used with batch number or
                      group.
          note: An optional note for the transaction
          uid: The unique id of the person sent from the giving platform. This
               should be used when the Breeze ID is unknown. Within Breeze a
               user will be able to associate this ID with a given Breeze ID.
          processor: The name of the processor used to send the payment. Used
                     in conjunction with uid. Not needed if using Breeze ID.
                     (eg. SimpleGive, BluePay, Stripe, Vanco Services)
          ---- If person_id is provided, or Breeze has already determined which
               person corresponds to the given uid and processor combination, the
               payment will be recorded for that person. If only uid and
               processor are provided, Breeze will attempt to determine the correct
               person using any or all of the following:
          name: Donor's name.
          email: Email address of the donor.
          street_address: Donor's street address.
        :return: Payment id
        :raises: BreezeError on failure to add contribution
        """
        _check_illegal_param(kwargs, _ADD_CONTRIBUTION_PARAMS)
        response = self._request(ENDPOINTS.CONTRIBUTIONS, command='add', params=kwargs)
        return response['payment_id']

    def edit_contribution(self, **kwargs) -> str:
        """
        Edit an existing contribution
        :param kwargs: Keyed parameters
          payment_id: The ID of the payment that should be modified.
          date: Date of transaction in YYYY-MM-DD format (eg. 2015-05-24)
          name: Name of person that made the transaction. Used to help match up
                contribution to correct profile within Breeze.  (eg. John Doe)
          person_id: The Breeze ID of the donor. If unknown, use UID instead of
                     person id  (eg. 1234567) (Curious. Why if payment_id is given?)
          uid: The unique id of the person sent from the giving platform. This
               should be used when the Breeze ID is unknown. Within Breeze a
               user will be able to associate this ID with a given Breeze ID.
               (eg. 9876543)
          email: Email address of donor. If no person_id is provided, used to
                 help automatically match the person to the correct profile.
                 (eg. sample@breezechms.com)
          street_address: Donor's street address. If person_id is not provided,
                          street_address will be used to help automatically
                          match the person to the correct profile.
                          (eg. 123 Sample St)
          processor: The name of the processor used to send the payment. Used
                     in conjunction with uid. Not needed if using Breeze ID.
                     (eg. SimpleGive, BluePay, Stripe)
          method: The payment method. (eg. Check, Cash, Credit/Debit Online,
                  Credit/Debit Offline, Donated Goods (FMV), Stocks (FMV),
                  Direct Deposit)
          funds_json: JSON string containing fund names and amounts. This
                      allows splitting fund giving. The ID is optional. If
                      present, it must match an existing fund ID and it will
                      override the fund name.
                      eg. [ {
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
          group: This will create a new batch and enter all contributions with
                 the same group into the new batch. Previous groups will be
                 remembered and so they should be unique for every new batch.
                 Use this if wanting to import into the next batch number in a
                 series.
          batch_number: The batch number to import contributions into. Use
                        group instead if you want to import into the next batch
                        number.
          batch_name: The name of the batch. Can be used with batch number or
                      group.
        :returns: New payment ID for the the payment
        :raises: BreezeError on failure to edit contribution.
        :note: The old payment is removed and a new one is added with
               the provided fields updated.
        :note: Handling of fields related to uid and processor is as described
               for add_contribution().
        """
        _check_illegal_param(kwargs, _EDIT_CONTRIBUTION_PARAMS)
        response = self._request(ENDPOINTS.CONTRIBUTIONS,
                                 command='edit',
                                 params=kwargs)
        return response.get('payment_id') if isinstance(response, dict) else response

    def delete_contribution(self, payment_id):
        """
        Delete an existing contribution.
        :param payment_id: The ID of the payment to be deleted
        :return: True if successful
        :raises: BreezeError on failure to delete a contribution.
        """
        response = self._request(ENDPOINTS.CONTRIBUTIONS,
                                 command="delete",
                                 params={'payment_id': payment_id})
        return response.get('success', False)

    def list_contributions(self, **kwargs) -> List[Mapping]:
        """
        Retrieve a list of contributions.
        :param kwargs: Set of keyed arguments
          start: Find contributions given on or after a specific date (YYYY-MM-DD)
          end: Find contributions given on or before a specific date
          person_id: ID of person's contributions to fetch. (eg. 9023482)
          include_family: Include family members of person_id (must provide
                          person_id); default: False.
          amount_min: Contribution amounts equal or greater than.
          amount_max: Contribution amounts equal or less than.
          method_ids: List of method IDs.
          fund_ids: List of fund IDs.
          envelope_number: Envelope number.
          batches: List of Batch numbers.
          forms: List of form IDs.
        :return: List of matching contributions as dicts
        :raises: BreezeError on malformed request
        :raises: BreezeBadParameter on missing start or end
        """
        if kwargs.get('include_family') and not kwargs.get('person_id'):
            raise BreezeError('include_family requires a person_id.')

        _check_illegal_param(kwargs, _LIST_CONTRIBUTION_PARAMS)
        return self._request(ENDPOINTS.CONTRIBUTIONS, command='list', params=kwargs)

    def list_funds(self, include_totals: bool = False) -> List[dict]:
        """
        List all funds
        :param include_totals: If True include total given for each fund
        :return: List of fund descriptions
        """

        return self._request(ENDPOINTS.FUNDS,
                             command='list',
                             params={'include_totals': '1'} if include_totals else None)

    def list_campaigns(self) -> List[dict]:
        """
        List pledge campaigns
        :return:  List of campaigns
        """
        return self._request(ENDPOINTS.PLEDGES, command='list_campaigns')


    def list_pledges(self, campaign_id) -> List[dict]:
        """
        List of pledges within a campaign
        :param campaign_id: ID number of a campaign
        :return: List of pledges
        """

        return self._request(ENDPOINTS.PLEDGES,
                             command="list_pledges",
                             params={'campaign_id': campaign_id})

    # -------------------------- Forms

    def list_form_entries(self, form_id, details=False):
        """
        Return entries for a given form
        :param form_id: The ID of the form
        :param details: If True, return all information (slower) else just names
        :return: List of form entries, for example:
          [
           {
            "id":"11",
            "form_id":"15326",
            "created_on":"2021-03-09 13:04:02",
            "person_id":null,
            "response":{
                "45":{
                "id":"13",
                "oid":"1512",
                "first_name":"Zoe",
                "last_name":"Washburne",
                "created_on":"2021-03-09 13:04:03"
                },
                "46":"zwashburne@test.com",
                "47":"Red"
            }
           },
          ]
          """
        return self._request(ENDPOINTS.FORMS, command='list_form_entries',
                             params={'form_id': form_id,
                                     'details': '1' if details else None})

    def remove_form_entry(self, entry_id):
        """
        Remove the designated form entry.
        :param entry_id: The ID of the entry to remove from Breeze.
        :return: True if successful
        """
        return self._request(ENDPOINTS.FORMS, command='remove_form_entry',
                             params={'entry_id': entry_id})


    def list_form_fields(self, form_id):
        """
            List the fields for a given form.
            :param form_id: The ID of the form
            :return: The fields that correspond to the numeric form id provided,
                for example:
        [
        {
            "id":"185",
            "oid":"1512",
            "field_id":"45",
            "profile_section_id":"0",
            "field_type":"name",
            "name":"Name",
            "position":"3",
            "profile_id":"5877b98301fc2",
            "created_on":"2022-01-12 09:14:43",
            "options":[
            ]
        },
        {
            "id":"186",
            "oid":"1512",
            "field_id":"46",
            "profile_section_id":"0",
            "field_type":"single_line",
            "name":"Email",
            "position":"4",
            "profile_id":"5877b98301fc2",
            "created_on":"2022-01-12 09:14:43",
            "options":[
            ]
        },
        {
            "id":"187",
            "oid":"1512",
            "field_id":"47",
            "profile_section_id":"0",
            "field_type":"single_line",
            "name":"Favorite Color",
            "position":"5",
            "profile_id":"5877b98301fc2",
            "created_on":"2022-01-12 09:14:43",
            "options":[
            ]
        }
        ]
        """
        return self._request(ENDPOINTS.FORMS, command='list_form_fields',
                             params={'form_id': form_id,
                                     })

    # ------------- Tags

    def get_tags(self, folder_id=None):
        """
        Get list of tags
        :param folder_id: If set, only include tags in this folder id
        :return: List of tags, for example:
            [
              {
                "id":"523928",
                "name":"4th & 5th",
                "created_on":"2018-09-10 09:19:40",
                "folder_id":"1539"
              },
              {
                "id":"51994",
                "name":"6th Grade",
                "created_on":"2018-02-06 06:40:40",
                "folder_id":"1539"
              },
            ]
        """

        return self._request(ENDPOINTS.TAGS,
                             command='list_tags',
                             params={'folder_id': folder_id} if folder_id else None)

    def get_tag_folders(self) -> List[dict]:
        """
        Get list of tag folders
        :return: List of tag folders, for example:
           [
             {
                 "id":"1234567",
                 "parent_id":"0",
                 "name":"All Tags",
                 "created_on":"2018-06-05 18:12:34"
             },
             {
                 "id":"8234253",
                 "parent_id":"120425",
                 "name":"Kids",
                 "created_on":"2018-06-05 18:12:10"
             },
             {
                 "id":"1537253",
                 "parent_id":"5923042",
                 "name":"Small Groups",
                 "created_on":"2018-09-10 09:19:40"
             },
             {
                 "id":"20033",
                 "parent_id":"20031",
                 "name":"Student Ministries",
                 "created_on":"2018-12-15 18:11:31"
             }
          ]
        """
        return self._request(ENDPOINTS.TAGS, command='list_folders')

    def assign_tag(self,
                   person_id: str,
                   tag_id: str) -> bool:
        """
        Assign a tag to a person
        :param person_id: The person to get the tag
        :param tag_id: ID of tag to assign
        :return: True if success
        """
        response = self._request(ENDPOINTS.TAGS, command='assign',
                                 params={'person_id': person_id, 'tag_id': tag_id})
        return response

    def unassign_tag(self, person_id: str,
                     tag_id: str) -> bool:
        """
        Unassign a tag from a person
        :param person_id: Person to lose the tag
        :param tag_id: ID of tag to lose
        :return: True if success
        """

        response = self._request(ENDPOINTS.TAGS, command='unassign',
                                 params={'person_id': person_id, 'tag_id': tag_id})

        return response


# ------------ Volunteers

# APIs for for volunteer management are described by the generic Breeze API
# specification, but there was no implementation in the Python module.
# Since my church doesn't use Breeze volunteer management I don't have a
# good eay to test. If there's a strong desire for them, I'll consider adding
# them after other projects are done.
# list_volunteers
# Add Volunteer
# Remove Volunteer
# Update Volunteer
# List Volunteer Roles
# Add Volunteer Role
# Remove Volunteer Role


def breeze_api(breeze_url: str = None,
               api_key: str = None,
               dry_run: bool = False,
               connection: requests.Session = requests.Session(),
               config_name: str = HELPER_CONFIG_FILE,
               **kwargs,
               ) -> BreezeApi:
    """
    Create an instance of a Breeze api object. Parameters needed to configure the api
    can be passed explicitly or loaded from a file using load_config().
    :param breeze_url: Explicitly given url for the Breeze API.
                (load_config() key 'breeze_url')
    :param api_key: Explicitly given API key for the Breeze API.
                (load_config() key 'api_key')
    :param dry_run: Just for testing, causes breeze_api to skip all net interactions.
    :param connection: Session if other than default (mostly for testing)
    :param config_name: Alternate load_config() file name.
    :param kwargs: Other parameters used by load_config()
    :return: A BreezeAPI instance
    """

    # First check if we have an explicit url and API key
    if not breeze_url or not api_key:
        # url and api key not explicitly given, so load from configuration files
        config = combine_settings.load_config(config_name, **kwargs)
        breeze_url = breeze_url if breeze_url else config.get('breeze_url')
        api_key = api_key if api_key else config.get('api_key')
        if not breeze_url or not api_key:
            raise BreezeError("Both breeze_url and api_key are required")

    return BreezeApi(breeze_url, api_key, dry_run=dry_run, connection=connection)

def config_file_list(config_name: str = HELPER_CONFIG_FILE,
                     **kwargs) -> List[str]:
    """
    Returns list of potential files that will be searched for Breeze configuration.
    :param config_name: Name of configuration file if not default
    :param kwargs: Other configuration arguments relevant to load_config()
    :return: List of files
    """
    return combine_settings.config_file_list(config_name=config_name, **kwargs)
