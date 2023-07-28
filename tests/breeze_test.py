"""Unittests for breeze.py

Usage:
  python -m unittest tests.breeze_test
"""

import json
import unittest
import requests

from breeze_chms_api import breeze
from breeze_chms_api.breeze import ENDPOINTS
from typing import List


class MockConnection(object):
    """Mock requests connection."""

    def __init__(self, response, url=None, params=None, headers=None):
        self._url = url
        self._params = params
        self._headers = headers
        self._response = response
        self._timeout = None
        self._verify = None

    def post(self, url, params, headers, timeout):
        self._url = url
        self._params = params
        self._headers = headers
        self._timeout = timeout
        return self._response

    def get(self, url, verify, params, headers, timeout):
        self._url = url
        self._verify = verify
        self._params = params
        self._headers = headers
        self._timeout = timeout
        return self._response

    @property
    def url(self):
        return self._url

    @property
    def params(self):
        return self._params


class MockResponse(object):
    """ Mock requests HTTP response."""

    def __init__(self, status_code, content, error=False):
        self.status_code = status_code
        self.content = content
        self.error = error

    @property
    def ok(self):
        return str(self.status_code).startswith('2')

    def json(self):
        if self.error:
            raise requests.ConnectionError
        if self.content:
            return json.loads(self.content)
        return None

    def raise_for_status(self):
        raise Exception('Fake HTTP Error')


FAKE_API_KEY = 'fak3ap1k3y'
FAKE_SUBDOMAIN = 'https://demo.breezechms.com'


class BreezeApiTestCase(unittest.TestCase):

    def validate_url(self,
                     url: str,
                     endpoint: ENDPOINTS,
                     command: str = '',
                     args: dict = {},
                     arg_alias: dict={}):
        base, extra = url.split('?')
        expect_url = f'{FAKE_SUBDOMAIN}/api/{endpoint.value}/{command}'
        self.assertEqual(base, expect_url, f'Expected {expect_url}, got {base}')

        expectargs = dict(args)

        if extra:
            gotargs = {k: v for k, v in [item.split('=') for item in extra.split('&')]}
            for ek, ev in args.items():
                gk = arg_alias.get(ek, ek)
                gv = gotargs.get(gk)
                if gv is None:
                    self.fail(f'Missing argument {ek}:{ev}')
                if ev is True:
                    ev = '1'
                elif isinstance(ev, List):
                    ev = '-'.join(str(v) for v in ev)
                else:
                    ev = str(ev)

                self.assertEqual(gv, ev, f'Expected {ev} for {ek}, got {gv}')
                del gotargs[gk]
                del expectargs[ek]

            if gotargs:
                # unexpected arguments
                self.fail(f'Unexpected arguments in {url}: {gotargs}')

        if expectargs:
            # Missing arguments
            self.fail(f'Missing arguments in {url}: {expectargs}')

    def test_request_header_override(self):
        response = MockResponse(200, json.dumps({'name': 'Some Data.'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)

        headers = {'Additional-Header': 'Data'}
        breeze_api._request(ENDPOINTS.FUNDS, headers=headers)
        self.assertTrue(
            set(headers.items()).issubset(
                set(connection._headers.items())))

    def test_invalid_subdomain(self):
        self.assertRaises(breeze.BreezeError, lambda: breeze.BreezeApi(
            api_key=FAKE_API_KEY,
            breeze_url='invalid-subdomain'))
        self.assertRaises(breeze.BreezeError, lambda: breeze.BreezeApi(
            api_key=FAKE_API_KEY,
            breeze_url='http://blah.breezechms.com'))
        self.assertRaises(breeze.BreezeError,
                          lambda: breeze.BreezeApi(api_key=FAKE_API_KEY,
                                                   breeze_url=''))

    def test_bad_connection(self):
        response = MockResponse(400, json.dumps({'errorCode': '400'}), error=True)
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
                breeze_url=FAKE_SUBDOMAIN,
                api_key=FAKE_API_KEY,
                connection=connection)

        self.assertRaises(breeze.BreezeError,
                           lambda: breeze_api.get_profile_fields())

    def test_missing_api_key(self):
        self.assertRaises(
            breeze.BreezeError,
            lambda: breeze.BreezeApi(api_key=None,
                                     breeze_url=FAKE_SUBDOMAIN))
        self.assertRaises(
            breeze.BreezeError,
            lambda: breeze.BreezeApi(api_key='',
                                     breeze_url=FAKE_SUBDOMAIN))

    def test_get_people(self):
        response = MockResponse(200, json.dumps({'name': 'Some Data.'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)

        args = {'limit': 1, 'offset': 1, 'details': True}
        result = breeze_api.get_people(**args)
        self.validate_url(connection.url, ENDPOINTS.PEOPLE, args=args)
        self.assertEqual(json.loads(response.content), result)

    def test_get_profile_fields(self):
        response = MockResponse(200, json.dumps({'name': 'Some Data.'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        result = breeze_api.get_profile_fields()
        self.validate_url(connection.url, ENDPOINTS.PROFILE_FIELDS)
        self.assertEqual(json.loads(response.content), result)

    def test_account_summary(self):
        rsp = {
            "id": "1234",
            "name": "Grace Church",
            "subdomain": "gracechurchdemo",
            "status": "1",
            "created_on": "2018-09-10 09:19:35",
            "details": {
                "timezone": "America\/New_York",
                "country": {
                    "id": "2",
                    "name": "United States of America",
                    "abbreviation": "USA",
                    "abbreviation_2": "US",
                    "currency": "USD",
                    "currency_symbol": "$",
                    "date_format": "MDY",
                    "sms_prefix": "1"
                }
            }
        }
        response = MockResponse(200, json.dumps(rsp))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        result = breeze_api.get_account_summary()
        self.validate_url(connection.url, ENDPOINTS.ACCOUNT_SUMMARY)
        self.assertEqual(json.loads(response.content), result)

    def test_get_person_details(self):
        response = MockResponse(200, json.dumps({'person_id': 'Some Data.'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)

        person_id = '123456'
        result = breeze_api.get_person_details(person_id)
        self.validate_url(connection.url, ENDPOINTS.PEOPLE, command=str(person_id))
        self.assertEqual(json.loads(response.content), result)

    def test_add_person(self):
        response = MockResponse(200, json.dumps([{'person_id': 'Some Data.'}]))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)

        first_name = 'Jiminy'
        last_name = 'Cricket'
        args = {'first_name': first_name, 'last_name': last_name}
        arg_alias = {'first_name': 'first', 'last_name': 'last'}

        result = breeze_api.add_person(**args)
        self.validate_url(connection.url, ENDPOINTS.PEOPLE, command='add', args=args, arg_alias=arg_alias)
        self.assertEqual(json.loads(response.content), result)

    def test_update_person(self):
        # With no fields_json
        self.update_person_test()

    def test_update_person_with_fields_json(self):
        fields = {
            "field_id": "929778337",
            "field_type": "email",
            "response": "true",
            "details": {
                 "address": "tony@starkindustries.com",
                 "is_private": 1
            }
        }
        self.update_person_test(fields=fields)

    def update_person_test(self, fields: dict = None):
        response = MockResponse(200, json.dumps([{'person_id': 'Some Data.'}]))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)

        person_id = '123456'
        fields_json = json.dumps([fields], separators=(',', ':')) if fields else '[]'
        args = {'person_id': person_id, 'fields_json': fields_json}
        result = breeze_api.update_person(**args)
        self.validate_url(connection.url, ENDPOINTS.PEOPLE, command='update', args=args)
        self.assertEqual(json.loads(response.content), result)

    def test_get_events(self):
        response = MockResponse(200, json.dumps({'event_id': 'Some Data.'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)

        args = {'start_date': '3-1-2014', 'end_date': '3-7-2014'}
        arg_alias = {'start_date': 'start', 'end_date': 'end'}
        # start_date = '3-1-2014'
        # end_date = '3-7-2014'
        result = breeze_api.get_events(**args)
        self.validate_url(connection.url, ENDPOINTS.EVENTS, args=args, arg_alias=arg_alias)
        self.assertEqual(json.loads(response.content), result)

    def test_event_check_in(self):
        response = MockResponse(200, json.dumps({'event_id': 'Some Data.'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        args = {'person_id': 'person', 'event_instance_id': 'event'}
        arg_alias = {'event_instance_id': 'instance_id'}
        result = breeze_api.event_check_in(**args)
        self.assertEqual(json.loads(response.content), result)

        self.validate_url(connection.url, ENDPOINTS.EVENTS, command='add', args=args, arg_alias=arg_alias)

    def test_event_check_out(self):
        response = MockResponse(200, json.dumps({'event_id': 'Some Data.'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        args = {'person_id': 'person', 'event_instance_id': 'event'}
        args_alias = {'event_instance_id': 'instance_id'}
        result = breeze_api.event_check_out(**args)
        self.assertEqual(json.loads(response.content), result)

        self.validate_url(connection.url, ENDPOINTS.EVENTS, command='delete', args=args, arg_alias=args_alias)

    def test_add_contribution(self):
        payment_id = '12345'
        response = MockResponse(
            200, json.dumps({'success': True,
                             'payment_id': payment_id}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)

        args = {
            'date': '3-1-2014',
            'name': 'John Doe',
            'person_id': '123456',
            'uid': 'UID',
            'processor': 'Processor',
            'method': 'Method',
            'funds_json': "[{'id': '12345', 'name': 'Fund', 'amount', '150.00' }]",
            'amount': '150.00',
            'group': 'Group',
            'batch_number': '100',
            'batch_name': 'Batch Name'
            }

        result = breeze_api.add_contribution(**args)

        self.validate_url(connection.url, ENDPOINTS.CONTRIBUTIONS, command='add', args=args)
        self.assertEqual(payment_id, breeze_api.add_contribution())

    def test_edit_contribution(self):
        new_payment_id = '99999'
        response = MockResponse(
            200, json.dumps({'success': True,
                             'payment_id': new_payment_id}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        args = {
            'date': '3-1-2014',
            'name': 'Jane Doe',
            'person_id': '123456',
            'uid': 'UID2',
            'processor': 'Processor',
            'method': 'Method',
            'funds_json': "[{'id': '12345', 'name': 'Fund', 'amount', '150.00' }]",
            'amount': '150.00',
            'group': 'Group',
            'batch_number': '102',
            'batch_name': 'Batch Name'
            }

        result = breeze_api.edit_contribution(**args)
        self.validate_url(connection.url, ENDPOINTS.CONTRIBUTIONS, command='edit', args=args)
        self.assertEqual(new_payment_id, result)

    def test_list_contributions(self):
        response = MockResponse(
            200, json.dumps({'success': True,
                             'payment_id': '555'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        args = {
            'start_date': '3-1-2014',
            'end_date': '3-2-2014',
            'person_id': '12345',
            'include_family': True,
            'amount_min': '123456',
            'amount_max': 'UID',
            'method_ids': ['100', '101', '102'],
            'fund_ids': ['200', '201', '202'],
            'envelope_number': '1234',
            'batches': ['300', '301', '302'],
            'forms': ['400', '401', '402'],
        }

        result = breeze_api.list_contributions(**args)
        self.validate_url(connection.url, ENDPOINTS.CONTRIBUTIONS, command='list', args=args)
        self.assertEqual(json.loads(response.content), result)

        # Ensure that an error gets thrown if person_id is not
        # provided with include_family.
        self.assertRaises(
            breeze.BreezeError,
            lambda: breeze_api.list_contributions(include_family=True))

    def test_delete_contribution(self):
        payment_id = '12345'
        response = MockResponse(
            200, json.dumps({'success': True,
                             'payment_id': payment_id}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        args = {'payment_id': payment_id}
        self.assertEqual(payment_id, breeze_api.delete_contribution(**args))
        self.validate_url(connection.url, ENDPOINTS.CONTRIBUTIONS, command='delete', args=args)

    def test_list_form_entries(self):
        response = MockResponse(200, json.dumps([{
            "102519456": {
                "id": "102519456",
                "oid": "51124",
                "form_id": "582100",
                "created_on": "2022-07-31 20:33:18",
                "person_id": "10898096",
                "response": {
                  "person_id": ""
                }
              }
        }]))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        args = {'form_id': 329}
        result = breeze_api.list_form_entries(**args)
        self.assertEqual(json.loads(response.content), result)
        self.validate_url(connection.url, ENDPOINTS.FORMS, command='list_form_entries', args=args)

    def test_list_funds(self):
        response = MockResponse(200, json.dumps([{
            "id": "12345",
            "name": "Adult Ministries",
            "tax_deductible": "1",
            "is_default": "0",
            "created_on": "2014-09-10 02:19:35"
        }]))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        args = {'include_totals': True}
        result = breeze_api.list_funds(**args)
        self.assertEqual(json.loads(response.content), result)
        self.validate_url(connection.url, ENDPOINTS.FUNDS, command='list', args=args)

    def test_list_campaigns(self):
        response = MockResponse(200, json.dumps([{
            "id": "12345",
            "name": "Building Campaign",
            "number_of_pledges": 65,
            "total_pledged": 13030,
            "created_on": "2014-09-10 02:19:35"
        }]))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        result = breeze_api.list_campaigns()
        self.assertEqual(json.loads(response.content),  result)
        self.validate_url(connection.url, ENDPOINTS.PLEDGES, command='list_campaigns')

    def test_false_response(self):
        response = MockResponse(200, json.dumps(False))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        self.assertRaises(breeze.BreezeError, lambda: breeze_api.event_check_in('1', '2'))

    def test_errors_response(self):
        response = MockResponse(200, json.dumps({'errors': 'Some Errors'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        self.assertRaises(breeze.BreezeError, lambda: breeze_api.event_check_in('1', '2'))

    def test_list_pledges(self):
        response = MockResponse(200, json.dumps([{
            "id": "12345",
            "name": "Building Campaign",
            "number_of_pledges": 65,
            "total_pledged": 13030,
            "created_on": "2014-09-10 02:19:35"
        }]))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        args = {'campaign_id': 329}
        result = breeze_api.list_pledges(**args)
        self.assertEqual(json.loads(response.content), result)
        self.validate_url(connection.url, ENDPOINTS.PLEDGES, command='list_pledges', args=args)

    def test_get_tags(self):
        response = MockResponse(200, json.dumps([{
            "id": "523928",
            "name": "4th & 5th",
            "created_on": "2018-09-10 09:19:40",
            "folder_id": "1539"
        }]))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        args = {'folder': 1539}
        args_alias = {'folder': 'folder_id'}
        result = breeze_api.get_tags(**args)
        self.assertEqual(json.loads(response.content), result)
        self.validate_url(connection.url, ENDPOINTS.TAGS, command='list_tags', args=args, arg_alias=args_alias)


    def test_get_tag_folders(self):
        response = MockResponse(200, json.dumps([{
            "id": "1234567",
            "parent_id": "0",
            "name": "All Tags",
            "created_on": "2018-06-05 18:12:34"
        }]))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        result = breeze_api.get_tag_folders()
        self.assertEqual(json.loads(response.content), result)
        self.validate_url(connection.url, ENDPOINTS.TAGS, command='list_folders')

    def test_assign_tag(self):
        response = MockResponse(200, json.dumps({
            'success': True,
             }))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        args = {'person_id': 14134, 'tag_id': 1569323}
        result = breeze_api.assign_tag(**args)
        self.assertEqual(json.loads(response.content), result)
        self.validate_url(connection.url, ENDPOINTS.TAGS, command='assign', args=args)


    def test_unassign_tag(self):
        args = {'person_id': 17442, 'tag_id': 123156235}
        response = MockResponse(
            200, json.dumps({'success': True
                             }))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        result = breeze_api.unassign_tag(**args)
        self.assertEqual(json.loads(response.content), result)
        self.validate_url(connection.url, ENDPOINTS.TAGS, command='unassign', args=args)


    def test_add_event(self):
        response = MockResponse(200, json.dumps([{
            "id": "8324092",
            "oid": "1234",
            "event_id": "4567",
            "name": "Bonfire",
            "category_id": "0",
            "start_datetime": "2016-06-28 19:45:00",
            "end_datetime": "2016-06-23 20:45:00",
            "created_on": "2016-06-23 15:40:06"
        }]))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)

        args = {
            'name': 'Test Event',
            'start_date': '2022-09-01',
            'end_date': '2023-10-01',
            'all_day': True,
            'description': 'This is a test event',
            'category_id': 'secret',
            'event_id': 2809215
        }
        arg_alias = {'start_date': 'starts_on',
                     'end_date': 'ends_on'}
        result = breeze_api.add_event(**args)
        self.validate_url(connection.url, ENDPOINTS.EVENTS, command='add', args=args, arg_alias=arg_alias)
        self.assertEqual(json.loads(response.content), result)


if __name__ == '__main__':
    unittest.main()
