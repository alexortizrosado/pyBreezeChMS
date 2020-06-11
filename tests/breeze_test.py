"""Unittests for breeze.py

Usage:
  python -m unittest tests.breeze_test
"""

import json
import unittest

from breeze import breeze


class MockConnection(object):
    """Mock requests connection."""

    def __init__(self, response, url=None, params=None, headers=None):
        self._url = url
        self._params = params
        self._headers = headers
        self._response = response

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


FAKE_API_KEY = 'fak3ap1k3y'
FAKE_SUBDOMAIN = 'https://demo.breezechms.com'


class BreezeApiTestCase(unittest.TestCase):

    def test_request_header_override(self):
        response = MockResponse(200, json.dumps({'name': 'Some Data.'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)

        headers = {'Additional-Header': 'Data'}
        breeze_api._request('endpoint', headers=headers)
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

        breeze_api.get_people(limit=1, offset=1, details=True)
        self.assertEqual(
            connection.url,
            '%s%s/?%s' % (FAKE_SUBDOMAIN, breeze.ENDPOINTS.PEOPLE,
                          '&'.join(['limit=1', 'offset=1', 'details=1'])))
        self.assertEqual(
            breeze_api.get_people(), json.loads(response.content))

    def test_get_profile_fields(self):
        response = MockResponse(200, json.dumps({'name': 'Some Data.'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        self.assertEqual(breeze_api.get_profile_fields(),
                         json.loads(response.content))

    def test_get_person_details(self):
        response = MockResponse(200, json.dumps({'person_id': 'Some Data.'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)

        person_id = '123456'
        breeze_api.get_person_details(person_id)
        self.assertEqual(
            connection.url, '%s%s/%s' % (FAKE_SUBDOMAIN,
                                         breeze.ENDPOINTS.PEOPLE, person_id))
        self.assertEqual(breeze_api.get_person_details(person_id),
                         json.loads(response.content))

    def test_add_person(self):
        response = MockResponse(200, json.dumps([{'person_id': 'Some Data.'}]))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)

        first_name = 'Jiminy'
        last_name = 'Cricket'
        breeze_api.add_person(
            first_name=first_name,
            last_name=last_name)
        self.assertEqual(
            connection.url, '%s%s/add?%s' %
                            (FAKE_SUBDOMAIN, breeze.ENDPOINTS.PEOPLE, '&'.join(
                                ['first=%s' % first_name,
                                 'last=%s' % last_name])
                             )
        )
        self.assertEqual(breeze_api.add_person(first_name, last_name),
                         json.loads(response.content))

    def test_update_person(self):
        response = MockResponse(200, json.dumps([{'person_id': 'Some Data.'}]))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)

        person_id = '123456'
        breeze_api.update_person(person_id, '[]')
        self.assertEqual(
            connection.url, '%s%s/update?%s' %
                            (FAKE_SUBDOMAIN, breeze.ENDPOINTS.PEOPLE, '&'.join(
                                ['person_id=%s' % person_id,
                                 'fields_json=%s' % '[]'])
                             )
        )
        self.assertEqual(breeze_api.update_person(person_id, '[]'),
                         json.loads(response.content))
    
    def test_update_person_with_fields_json(self):
        response = MockResponse(200, json.dumps([{'person_id': 'Some Data.'}]))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)

        person_id = '123456'
        fields_json = json.dumps([{
            "field_id": "929778337",
            "field_type": "email",
            "response": "true",
            "details": {
                 "address": "tony@starkindustries.com",
                 "is_private": 1
            }
        }], separators=(',', ':'))
        breeze_api.update_person(person_id, fields_json)
        self.assertEqual(
            connection.url, '%s%s/update?%s' %
                            (FAKE_SUBDOMAIN, breeze.ENDPOINTS.PEOPLE, '&' . join(
                                ['person_id=%s' % person_id,
                                 'fields_json=%s' % fields_json])
                             )
        )
        self.assertEqual(breeze_api.update_person(person_id, fields_json),
                         json.loads(response.content))

    def test_get_events(self):
        response = MockResponse(200, json.dumps({'event_id': 'Some Data.'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)

        start_date = '3-1-2014'
        end_date = '3-7-2014'
        breeze_api.get_events(start_date=start_date, end_date=end_date)
        self.assertEqual(
            connection.url, '%s%s/?%s' % (FAKE_SUBDOMAIN,
                                          breeze.ENDPOINTS.EVENTS,
                                          '&'.join(['start=%s' % start_date,
                                                    'end=%s' % end_date])))
        self.assertEqual(breeze_api.get_events(), json.loads(response.content))

    def test_event_check_in(self):
        response = MockResponse(200, json.dumps({'event_id': 'Some Data.'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        self.assertEqual(breeze_api.event_check_in('person_id', 'event_id'),
                         json.loads(response.content))

    def test_event_check_out(self):
        response = MockResponse(200, json.dumps({'event_id': 'Some Data.'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        self.assertEqual(breeze_api.event_check_out('person_id', 'event_id'),
                         json.loads(response.content))

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
        date = '3-1-2014'
        name = 'John Doe'
        person_id = '123456'
        uid = 'UID'
        processor = 'Processor'
        method = 'Method'
        funds_json = "[{'id': '12345', 'name': 'Fund', 'amount', '150.00' }]"
        amount = '150.00'
        group = 'Group'
        batch_number = '100'
        batch_name = 'Batch Name'

        breeze_api.add_contribution(
            date=date,
            name=name,
            person_id=person_id,
            uid=uid,
            processor=processor,
            method=method,
            funds_json=funds_json,
            amount=amount,
            group=group,
            batch_number=batch_number,
            batch_name=batch_name)
        self.assertEqual(
            connection.url, '%s%s/add?%s' %
            (FAKE_SUBDOMAIN, breeze.ENDPOINTS.CONTRIBUTIONS, '&'.join(
                ['date=%s' % date,
                 'name=%s' % name,
                 'person_id=%s' % person_id,
                 'uid=%s' % uid,
                 'processor=%s' % processor,
                 'method=%s' % method,
                 'funds_json=%s' % funds_json,
                 'amount=%s' % amount,
                 'group=%s' % group,
                 'batch_number=%s' % batch_number,
                 'batch_name=%s' % batch_name
                 ])))
        self.assertEqual(breeze_api.add_contribution(), payment_id)

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
        payment_id = '12345'
        date = '3-1-2014'
        name = 'John Doe'
        person_id = '123456'
        uid = 'UID'
        processor = 'Processor'
        method = 'Method'
        funds_json = "[{'id': '12345', 'name': 'Fund', 'amount', '150.00' }]"
        amount = '150.00'
        group = 'Group'
        batch_number = '100'
        batch_name = 'Batch Name'

        breeze_api.edit_contribution(
            payment_id=payment_id,
            date=date,
            name=name,
            person_id=person_id,
            uid=uid,
            processor=processor,
            method=method,
            funds_json=funds_json,
            amount=amount,
            group=group,
            batch_number=batch_number,
            batch_name=batch_name)
        self.assertEqual(
            connection.url, '%s%s/edit?%s' %
            (FAKE_SUBDOMAIN, breeze.ENDPOINTS.CONTRIBUTIONS,
             '&'.join(
                ['payment_id=%s' % payment_id,
                 'date=%s' % date,
                 'name=%s' % name,
                 'person_id=%s' % person_id,
                 'uid=%s' % uid,
                 'processor=%s' % processor,
                 'method=%s' % method,
                 'funds_json=%s' % funds_json,
                 'amount=%s' % amount,
                 'group=%s' % group,
                 'batch_number=%s' % batch_number,
                 'batch_name=%s' % batch_name
                 ])))
        self.assertEqual(breeze_api.edit_contribution(), new_payment_id)

    def test_list_contributions(self):
        response = MockResponse(
            200, json.dumps({'success': True,
                             'payment_id': '555'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        start_date = '3-1-2014'
        end_date = '3-2-2014'
        person_id = '12345'
        include_family = True
        amount_min = '123456'
        amount_max = 'UID'
        method_ids = ['100', '101', '102']
        fund_ids = ['200', '201', '202']
        envelope_number = '1234'
        batches = ['300', '301', '302']
        forms = ['400', '401', '402']

        breeze_api.list_contributions(
            start_date=start_date,
            end_date=end_date,
            person_id=person_id,
            include_family=include_family,
            amount_min=amount_min,
            amount_max=amount_max,
            method_ids=method_ids,
            fund_ids=fund_ids,
            envelope_number=envelope_number,
            batches=batches,
            forms=forms)
        self.assertEqual(
            connection.url, '%s%s/list?%s' %
            (FAKE_SUBDOMAIN, breeze.ENDPOINTS.CONTRIBUTIONS, '&'.join(
                ['start=%s' % start_date, 'end=%s' % end_date, 'person_id=%s' %
                 person_id, 'include_family=1', 'amount_min=%s' % amount_min,
                 'amount_max=%s' % amount_max, 'method_ids=%s' %
                 '-'.join(method_ids), 'fund_ids=%s' % '-'.join(fund_ids),
                 'envelope_number=%s' % envelope_number, 'batches=%s' %
                 '-'.join(batches), 'forms=%s' % '-'.join(forms)])))
        self.assertEqual(breeze_api.list_contributions(start_date, end_date),
                         json.loads(response.content))

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
        self.assertEqual(
            breeze_api.delete_contribution(payment_id=payment_id), payment_id)
        self.assertEqual(
            connection.url, '%s%s/delete?payment_id=%s' % (
                FAKE_SUBDOMAIN, breeze.ENDPOINTS.CONTRIBUTIONS, payment_id
            ))

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
        self.assertEqual(breeze_api.list_funds(include_totals=True),
                         json.loads(response.content))
        self.assertEqual(
            connection.url,
            '%s%s/list?include_totals=1' % (FAKE_SUBDOMAIN,
                                            breeze.ENDPOINTS.FUNDS))

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
        self.assertEqual(breeze_api.list_campaigns(),
                         json.loads(response.content))
        self.assertEqual(
            connection.url,
            '%s%s/list_campaigns' % (FAKE_SUBDOMAIN,
                                     breeze.ENDPOINTS.PLEDGES))

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
        self.assertEqual(breeze_api.list_pledges(campaign_id=329),
                         json.loads(response.content))
        self.assertEqual(
            connection.url,
            '%s%s/list_pledges?campaign_id=329' % (FAKE_SUBDOMAIN,
                                                   breeze.ENDPOINTS.PLEDGES))

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
        self.assertEqual(breeze_api.get_tags(folder=1539),
                         json.loads(response.content))
        self.assertEqual(
            connection.url,
            "%s%s/list_tags/?folder_id=1539" % (FAKE_SUBDOMAIN, breeze.ENDPOINTS.TAGS)
        )

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
        self.assertEqual(breeze_api.get_tag_folders(),
                         json.loads(response.content))
        self.assertEqual(
            connection.url,
            "%s%s/list_folders" % (FAKE_SUBDOMAIN, breeze.ENDPOINTS.TAGS)
        )

    def test_assign_tag(self):
        person_id = '12345'
        tag_id = '1234567'
        response = MockResponse(200, json.dumps({
            'success': True,
             }))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        self.assertEqual(breeze_api.assign_tag(person_id, tag_id),
                         json.loads(response.content))
        self.assertEqual(
            connection.url,
            "%s%s/assign?person_id=%s&tag_id=%s" % (FAKE_SUBDOMAIN, breeze.ENDPOINTS.TAGS, person_id, tag_id))   

    def test_unassign_tag(self):
        person_id = '12345'
        tag_id = '1234567'
        response = MockResponse(
            200, json.dumps({'success': True
                             }))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        self.assertEqual(breeze_api.unassign_tag(person_id, tag_id),
                         json.loads(response.content))
        self.assertEqual(
            connection.url,
            "%s%s/unassign?person_id=%s&tag_id=%s" % (FAKE_SUBDOMAIN, breeze.ENDPOINTS.TAGS, person_id, tag_id))    

if __name__ == '__main__':
    unittest.main()
