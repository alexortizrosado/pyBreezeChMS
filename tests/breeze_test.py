"""Unittests for breeze.py

Usage:
  python -m unittest tests.breeze_test
"""

import json
import unittest
import requests
import os

from breeze_chms_api import breeze
from breeze_chms_api.breeze import ENDPOINTS
from typing import List

TEST_FILES_DIR = os.path.join(os.path.split(__file__)[0], 'test_files')


class MockConnection(object):
    """Mock requests connection."""

    def __init__(self, response, url=None, params=None, headers=None):
        self._url = []
        self._params = []
        self._headers = headers
        self._response = response
        self._timeout = None
        self._verify = None

    def post(self, url, params, headers, timeout):
        self._url.append(url)
        self._params.append(params)
        self._headers = headers
        self._timeout = timeout
        return self._response

    def get(self, url, verify, params, headers, timeout):
        self._url.append(url)
        self._verify = verify
        self._params.append(params)
        self._headers = headers
        self._timeout = timeout
        return self._response

    def reset(self):
        self.url = []
        self.params = []

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

    # TODO: Need tests for verify_params

    def make_api(self, result, error=False):
        self.response = MockResponse(200, result, error=error)
        self.connection = MockConnection(self.response)
        self.breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=self.connection)

    def validate_url(self,
                     endpoint: ENDPOINTS,
                     connection: MockConnection = None,
                     command: str = '',
                     expect_params: dict = dict(),
                     arg_alias: dict = dict(),
                     select_query: int = 0):
        connection = connection if connection else self.connection
        url = connection.url[select_query]
        expect_params = breeze._transform_settings(expect_params)
        got_params = connection.params[select_query]
        base, extra = url.split('?')
        expect_url = f'{FAKE_SUBDOMAIN}/api/{endpoint.value}/{command}'
        self.assertEqual(base, expect_url, f'Expected {expect_url}, got {base}')

        eparams = dict(expect_params)

        if eparams:
            gotparams = dict(got_params)
            for ek, ev in expect_params.items():
                gk = arg_alias.get(ek, ek)  # still needed?
                gv = gotparams.get(gk)
                if gv is None:
                    self.fail(f'Missing argument {ek}:{ev}')
                if ev is True:
                    ev = '1'
                elif isinstance(ev, List):
                    ev = '-'.join(str(v) for v in ev)
                else:
                    ev = str(ev)
                # Probably need to handle json strings above

                self.assertEqual(gv, ev, f'Expected {ev} for {ek}, got {gv}')
                del gotparams[gk]
                del eparams[ek]

            if gotparams:
                # unexpected arguments
                self.fail(f'Unexpected arguments in {url}: {gotparams}')

        if eparams:
            # Missing arguments
            self.fail(f'Missing arguments in {url}: {eparams}')

    def test_request_header_override(self):
        self.make_api(json.dumps({'name': 'Some Data.'}))

        headers = {'Additional-Header': 'Data'}
        self.breeze_api._request(ENDPOINTS.FUNDS, headers=headers)
        self.assertTrue(
            set(headers.items()).issubset(
                set(self.connection._headers.items())))

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
        self.make_api({'errorCode': '400'}, error=True)
        self.assertRaises(breeze.BreezeError,
                          lambda: self.breeze_api.get_profile_fields())

    def test_missing_api_key(self):
        self.assertRaises(
            breeze.BreezeError,
            lambda: breeze.BreezeApi(api_key=None,
                                     breeze_url=FAKE_SUBDOMAIN))
        self.assertRaises(
            breeze.BreezeError,
            lambda: breeze.BreezeApi(api_key='',
                                     breeze_url=FAKE_SUBDOMAIN))

    def test_list_people(self):
        self.make_api(json.dumps({'name': 'Some Data.'}))

        args = {'limit': 1, 'offset': 1, 'details': True}
        result = self.breeze_api.list_people(**args)
        self.validate_url(ENDPOINTS.PEOPLE, expect_params=args)
        self.assertEqual(json.loads(self.response.content), result)

    def _make_profile_field_api(self) -> List[dict]:
        with open(os.path.join(TEST_FILES_DIR, 'profiles.json'), 'r') as f:
            json_str = f.read()
        self.make_api(json_str)
        return json_str

    def test_get_profile_fields(self):
        json_str = self._make_profile_field_api()
        result = self.breeze_api.get_profile_fields()
        expect = json.loads(json_str)
        self.validate_url(ENDPOINTS.PROFILE_FIELDS)
        # self.assertEqual(expect[])
        self.assertEqual(expect[3].get('name'), result[3].get('name'))

    def test_get_field_spec_by_name(self):
        self._make_profile_field_api()
        expect_id = '2114298709'
        field = self.breeze_api.get_field_spec_by_name('Church Relationship')
        self.assertEqual(expect_id, field.get('field_id'))
        self.assertEqual('Church Relationships', field.get('section_spec').get('name'))
        profile = {'details': {expect_id: {'content': 'expected'}}}
        val_from_name =self.breeze_api.field_value_from_name(
            'Church Relationship',
            profile)
        self.assertEqual('expected', val_from_name.get('content'))
        bad_field = self.breeze_api.field_value_from_name('badfield', profile)
        self.assertFalse(bad_field)

    def test_get_field_spec_by_id(self):
        self._make_profile_field_api()
        field = self.breeze_api.get_field_spec_by_id('2114298972')
        self.assertEqual('Member Number', field.get('name'))
        self.assertEqual('Membership Status', field.get('section_spec').get('name'))

    def test_field_value_by_name(self):
        self._make_profile_field_api()

    def test_account_summary(self):
        rsp = {
            "id": "1234",
            "name": "Grace Church",
            "subdomain": "gracechurchdemo",
            "status": "1",
            "created_on": "2018-09-10 09:19:35",
            "details": {
                "timezone": "America/New_York",
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
        self.make_api(json.dumps(rsp))
        result = self.breeze_api.get_account_summary()
        self.validate_url(ENDPOINTS.ACCOUNT_SUMMARY)
        self.assertEqual(json.loads(self.response.content), result)

    def test_get_person_details(self):
        self.make_api(json.dumps({"person_id": "Some Data."}))
        person_id = '123456'
        result = self.breeze_api.get_person_details(person_id)
        self.validate_url(ENDPOINTS.PEOPLE, command=str(person_id))
        self.assertEqual(self.response.content, json.dumps(result))

    def test_add_person(self):
        self.make_api(json.dumps([{'person_id': 'Some Data.'}]))

        first_name = 'Jiminy'
        last_name = 'Cricket'
        args = {'first': first_name, 'last': last_name}

        result = self.breeze_api.add_person(**args)
        self.validate_url(ENDPOINTS.PEOPLE, command='add', expect_params=args)
        self.assertEqual(json.loads(self.response.content), result)

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
        self.make_api(json.dumps([{'person_id': 'Some Data.'}]))

        person_id = '123456'
        fields_json = json.dumps([fields], separators=(',', ':')) if fields else '[]'
        args = {'person_id': person_id, 'fields_json': fields_json}
        result = self.breeze_api.update_person(**args)
        self.validate_url(ENDPOINTS.PEOPLE, command='update', expect_params=args)
        self.assertEqual(json.loads(self.response.content), result)

    def test_list_calendars(self):
        ret = [{'id': 0, 'name': 'Main'}, {'id': 987, 'name': 'Private'}]
        self.make_api(json.dumps(ret))
        result = self.breeze_api.list_calendars()
        self.validate_url(ENDPOINTS.EVENTS, command='calendars/list')
        self.assertEqual(json.loads(self.response.content), result)

    def test_list_events(self):
        self.make_api(json.dumps({'event_id': 'Some Data.'}))

        args = {'start': '3-1-2014', 'end': '3-7-2014'}
        result = self.breeze_api.list_events(**args)
        self.validate_url(ENDPOINTS.EVENTS, expect_params=args)
        self.assertEqual(json.loads(self.response.content), result)

    def test_list_event(self):
        inst_id = '235235'
        self.make_api(json.dumps({'id': inst_id, 'name': 'Raffle'}))
        result = self.breeze_api.list_event(inst_id)
        self.validate_url(ENDPOINTS.EVENTS, command="list_event",
                          expect_params={'instance_id': inst_id})
        self.assertEqual('Raffle', result.get('name'))

    def test_event_check_in(self):
        # response = MockResponse(200, json.dumps({'event_id': 'Some Data.'}))
        self.make_api(json.dumps(True))
        args = {'person_id': 'person', 'instance_id': 'event'}
        result = self.breeze_api.event_check_in(**args)
        self.assertTrue(result)
        args['direction'] = 'in'

        self.validate_url(ENDPOINTS.EVENTS,
                          command='attendance/add',
                          expect_params=args)

    def test_event_check_out(self):
        self.make_api(json.dumps({'event_id': 'Some Data.'}))
        args = {'person_id': 'person', 'instance_id': 'event'}
        # args_alias = {'event_instance_id': 'instance_id'}
        result = self.breeze_api.event_check_out(**args)
        self.assertEqual(json.loads(self.response.content), result)
        args['direction'] = 'out'
        self.validate_url(ENDPOINTS.EVENTS,
                          command='attendance/add',
                          expect_params=args)

    def test_delete_attendance(self):
        self.make_api('true')
        result = self.breeze_api.delete_attendance('person', 'instance')
        self.assertEqual(True, result)
        self.validate_url(ENDPOINTS.EVENTS,
                          command='attendance/delete',
                          expect_params={'person_id': 'person',
                                         'instance_id': 'instance'})

    def test_list_attendance(self):
        expect_result = json.dumps([{'stuff': 'value'}])
        self.make_api(expect_result)
        instance_id = 'inst'
        result = self.breeze_api.list_attendance(instance_id=instance_id, details=True)
        self.validate_url(ENDPOINTS.EVENTS, command='attendance/list',
                          expect_params={'details': 'true', 'instance_id': instance_id})
        r1 = result[0]
        self.assertEqual('value', r1.get('stuff'))

    def test_list_eligible_people(self):
        ret = [{'id': '123', 'first_name': 'alex'}]
        self.make_api(json.dumps(ret))
        instance = '123459'
        result = self.breeze_api.list_eligible_people(instance)
        self.validate_url(ENDPOINTS.EVENTS, command='attendance/eligible',
                          expect_params={'instance_id': instance})
        self.assertEqual('alex', (result[0]).get('first_name'))

    def test_add_contribution(self):
        payment_id = '12345'
        self.make_api(json.dumps({'success': True, 'payment_id': payment_id}))

        args = {
            'date': '2014-01-03',
            # 'name': 'John Doe',
            'person_id': '123456',
            'uid': 'UID',
            'processor': 'Processor',
            'method': 'Method',
            'funds_json': [{'id': '12345', 'name': 'Fund', 'amount': '150.00'}],
            'amount': '150.00',
            'group': 'Group',
            'batch_number': '100',
            'batch_name': 'Batch Name',
            }

        result = self.breeze_api.add_contribution(**args)

        self.validate_url(ENDPOINTS.CONTRIBUTIONS, command='add', expect_params=args)
        self.assertEqual(payment_id, result)

        self.assertRaises(breeze.BreezeBadParameter,
                          lambda: self.breeze_api.add_contribution(notaparm=''))

    def test_edit_contribution(self):
        new_payment_id = '99999'
        self.make_api(json.dumps({'success': True, 'payment_id': new_payment_id}))
        args = {
            'date': '2014-01-03',
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

        result = self.breeze_api.edit_contribution(**args)
        self.validate_url(ENDPOINTS.CONTRIBUTIONS, command='edit', expect_params=args)
        # self.assertTrue(result.get('success'))
        self.assertEqual(new_payment_id, result)

    def test_list_contributions(self):
        self.make_api(json.dumps({'success': True,
                             'payment_id': '555'}))
        args = {
            'start': '3-1-2014',
            'end': '3-2-2014',
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

        result = self.breeze_api.list_contributions(**args)
        self.validate_url(ENDPOINTS.CONTRIBUTIONS, command='list', expect_params=args)
        self.assertEqual(json.loads(self.response.content), result)

        # Ensure that an error gets thrown if person_id is not
        # provided with include_family.
        self.assertRaises(
            breeze.BreezeError,
            lambda: self.breeze_api.list_contributions(include_family=True))

    def test_delete_contribution(self):
        payment_id = '12345'
        self.make_api(json.dumps({'success': True,
                             'payment_id': payment_id}))
        args = {'payment_id': payment_id}
        self.assertTrue(self.breeze_api.delete_contribution(**args))
        self.validate_url(ENDPOINTS.CONTRIBUTIONS,
                          command='delete',
                          expect_params=args)

    def test_list_form_entries(self):
        self.make_api(json.dumps([{
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
        args = {'form_id': 329}
        result = self.breeze_api.list_form_entries(**args)
        self.assertEqual(json.loads(self.response.content), result)
        self.validate_url(ENDPOINTS.FORMS,
                          command='list_form_entries',
                          expect_params=args)

    def test_list_funds(self):
        self.make_api(json.dumps([{
            "id": "12345",
            "name": "Adult Ministries",
            "tax_deductible": "1",
            "is_default": "0",
            "created_on": "2014-09-10 02:19:35"
        }]))
        args = {'include_totals': True}
        result = self.breeze_api.list_funds(**args)
        self.assertEqual(json.loads(self.response.content), result)
        args['include_totals'] = '1'
        self.validate_url(ENDPOINTS.FUNDS, command='list', expect_params=args)

    def test_list_campaigns(self):
        self.make_api(json.dumps([{
            "id": "12345",
            "name": "Building Campaign",
            "number_of_pledges": 65,
            "total_pledged": 13030,
            "created_on": "2014-09-10 02:19:35"
        }]))
        result = self.breeze_api.list_campaigns()
        self.assertEqual(json.loads(self.response.content),  result)
        self.validate_url(ENDPOINTS.PLEDGES, command='list_campaigns')

    def test_false_response(self):
        self.make_api(json.dumps(False))
        self.assertRaises(breeze.BreezeError,
                          lambda: self.breeze_api.event_check_in('1', '2'))

    def test_errors_response(self):
        self.make_api(json.dumps({'errors': 'Some Errors'}))
        self.assertRaises(breeze.BreezeError,
                          lambda: self.breeze_api.event_check_in('1', '2'))

    def test_list_pledges(self):
        self.make_api(json.dumps([{
            "id": "12345",
            "name": "Building Campaign",
            "number_of_pledges": 65,
            "total_pledged": 13030,
            "created_on": "2014-09-10 02:19:35"
        }]))
        args = {'campaign_id': 329}
        result = self.breeze_api.list_pledges(**args)
        self.assertEqual(json.loads(self.response.content), result)
        self.validate_url(ENDPOINTS.PLEDGES, command='list_pledges', expect_params=args)

    def test_get_tags(self):
        self.make_api(json.dumps([{
            "id": "523928",
            "name": "4th & 5th",
            "created_on": "2018-09-10 09:19:40",
            "folder_id": "1539"
        }]))
        args = {'folder_id': 1539}
        result = self.breeze_api.get_tags(**args)
        self.assertEqual(json.loads(self.response.content), result)
        self.validate_url(ENDPOINTS.TAGS, command='list_tags', expect_params=args)

    def test_get_tag_folders(self):
        self.make_api(json.dumps([{
            "id": "1234567",
            "parent_id": "0",
            "name": "All Tags",
            "created_on": "2018-06-05 18:12:34"
        }]))

        result = self.breeze_api.get_tag_folders()
        self.assertEqual(json.loads(self.response.content), result)
        self.validate_url(ENDPOINTS.TAGS, command='list_folders')

    def test_assign_tag(self):
        self.make_api(json.dumps({
            'success': True,
             }))
        args = {'person_id': 14134, 'tag_id': 1569323}
        result = self.breeze_api.assign_tag(**args)
        self.assertEqual(json.loads(self.response.content), result)
        self.validate_url(ENDPOINTS.TAGS, command='assign', expect_params=args)

    def test_unassign_tag(self):
        args = {'person_id': 17442, 'tag_id': 123156235}
        self.make_api(json.dumps({'success': True}))
        result = self.breeze_api.unassign_tag(**args)
        self.assertEqual(json.loads(self.response.content), result)
        self.validate_url(ENDPOINTS.TAGS, command='unassign', expect_params=args)

    def test_add_event(self):
        self.make_api(json.dumps([{
            "id": "8324092",
            "oid": "1234",
            "event_id": "4567",
            "name": "Bonfire",
            "category_id": "0",
            "start_datetime": "2016-06-28 19:45:00",
            "end_datetime": "2016-06-23 20:45:00",
            "created_on": "2016-06-23 15:40:06"
        }]))

        args = {
            'name': 'Test Event',
            'starts_on': '2022-09-01',
            'ends_on': '2023-10-01',
            'all_day': True,
            'description': 'This is a test event',
            'category_id': 'secret',
            'event_id': 2809215
        }
        result = self.breeze_api.add_event(**args)
        self.validate_url(ENDPOINTS.EVENTS, command='add', expect_params=args)
        self.assertEqual(json.loads(self.response.content), result)

    def test_failed_request(self):
        self.make_api(json.dumps({'success': False, 'errors': 23}))
        self.assertRaises(breeze.BreezeError, lambda: self.breeze_api.list_people())

    def test_build(self):
        url = 'https://4breezetest.breezechms.com'
        overrides = {'breeze_url': url, 'api_key': 'zyzzy'}
        api = breeze.breeze_api(overrides=overrides)
        self.assertEqual(url, api.breeze_url)

    def test_build_bad_url(self):
        url = 'https://4breeetest.breezy.com'
        self.assertRaises(breeze.BreezeError,
                          lambda: breeze.breeze_api(breeze_url=url,
                                                    api_key='plover'))
        overrides = {'breeze_url': None, 'api_key': None}
        self.assertRaises(breeze.BreezeError,
                          lambda: breeze.breeze_api(overrides=overrides))


if __name__ == '__main__':
    unittest.main()
