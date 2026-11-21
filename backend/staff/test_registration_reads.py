import json

from django.db import connection
from django.test import Client, TestCase

from core import testing as t


class RegistrationReadTests(TestCase):
    def setUp(self):
        self.zone = t.make_zone()
        self.household, self.member, _ = t.make_household(self.zone)
        self.second = t.make_member(self.household, first='Second')
        self.event = t.make_event(status='Closed')
        self.other_event = t.make_event('Other')
        t.make_staff()
        self.client.post('/api/staff/auth/login', json.dumps({
            'login_email': 'staff@example.com', 'password': t.PASSWORD}), content_type='application/json')
        with connection.cursor() as cur:
            cur.execute("INSERT INTO SHELTER (name,address,capacity,available_spaces) VALUES ('First','Address',10,10)")
            self.shelter = cur.lastrowid
            cur.execute("INSERT INTO SHELTER (name,address,capacity,available_spaces) VALUES ('Second','Address',10,10)")
            self.destination = cur.lastrowid
            cur.execute('INSERT INTO REGISTRATION (household_id,event_id,submitter_id) VALUES (%s,%s,%s)',
                        [self.household.pk, self.event.pk, self.member.pk])
            self.registration = cur.lastrowid
            cur.execute('INSERT INTO REGISTRATION_MEMBER VALUES (%s,%s),(%s,%s)',
                        [self.registration, self.member.pk, self.registration, self.second.pk])
            cur.execute("INSERT INTO PLACEMENT (registration_id,placement_no,shelter_id,status,arrival_time,departure_time) VALUES (%s,1,%s,'Transferred','2026-08-02 10:00:00','2026-08-03 10:00:00')", [self.registration, self.shelter])
            cur.execute('INSERT INTO PLACEMENT (registration_id,placement_no,shelter_id) VALUES (%s,2,%s)',
                        [self.registration, self.destination])
            cur.execute('INSERT INTO REGISTRATION (household_id,event_id) VALUES (%s,%s)',
                        [self.household.pk, self.other_event.pk])
            self.empty = cur.lastrowid
        self.detail = f'/api/staff/registrations/{self.registration}'
        self.placements = f'/api/staff/shelters/{self.destination}/placements'

    def test_registration_contract_and_history(self):
        response = self.client.get(self.detail)
        self.assertEqual(response.status_code, 200)
        row = response.json()
        self.assertEqual(row['household']['household_id'], self.household.pk)
        self.assertEqual(row['event']['status'], 'Closed')
        self.assertEqual(row['contact'], {'member_id': self.member.pk, 'first_name': 'Anh',
                                         'last_name': 'Nguyen', 'phone_number': None, 'email': 'holder@example.com'})
        self.assertEqual(row['participant_count'], 2)
        self.assertEqual([p['member_id'] for p in row['participants']], [self.member.pk, self.second.pk])
        self.assertEqual([p['placement_no'] for p in row['placements']], [1, 2])
        self.assertEqual(row['current_placement'], row['placements'][1])
        self.assertEqual(row['placements'][0]['departure_time'], '2026-08-03T10:00:00')
        self.assertIsNone(row['placements'][1]['arrival_time'])
        self.assertEqual(row['placements'][1]['shelter']['shelter_id'], self.destination)
        rows = self.client.get('/api/staff/registrations').json()['registrations']
        self.assertEqual(len(rows), 2)
        self.assertNotIn('placements', rows[0])
        self.assertNotIn('password', json.dumps(rows))
        empty = self.client.get(f'/api/staff/registrations/{self.empty}').json()
        self.assertIsNone(empty['contact'])
        self.assertIsNone(empty['current_placement'])
        self.assertEqual(empty['participants'], [])
        self.assertEqual(empty['placements'], [])

    def test_filters_and_empty_results(self):
        for filters in ({'event_id': self.event.pk}, {'registration_id': self.registration},
                        {'event_id': self.event.pk, 'registration_id': self.registration}):
            response = self.client.get('/api/staff/registrations', filters)
            self.assertEqual(response.status_code, 200)
            self.assertEqual([r['registration_id'] for r in response.json()['registrations']], [self.registration])
        for filters in ({'event_id': 999999}, {'registration_id': 999999},
                        {'event_id': self.other_event.pk, 'registration_id': self.registration}):
            self.assertEqual(self.client.get('/api/staff/registrations', filters).json(), {'registrations': []})
        self.assertEqual(self.client.get(self.placements, {'event_id': self.other_event.pk}).json()['placements'], [])

    def test_shelter_views_and_terminal_current_placement(self):
        rows = self.client.get(self.placements).json()['placements']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['placement_no'], 2)
        self.assertEqual(rows[0]['participant_count'], 2)
        self.assertEqual(rows[0]['registration_status'], 'Active')
        self.assertEqual(self.client.get(self.placements, {'view': 'occupants'}).json()['placements'], [])
        source = f'/api/staff/shelters/{self.shelter}/placements'
        self.assertEqual(self.client.get(source).json()['placements'], [])
        self.assertEqual(self.client.get(source, {'view': 'history'}).json()['placements'][0]['status'], 'Transferred')
        with connection.cursor() as cur:
            cur.execute("UPDATE PLACEMENT SET status='Arrived',arrival_time='2026-08-04 10:00:00' WHERE registration_id=%s AND placement_no=2", [self.registration])
        self.assertEqual(len(self.client.get(self.placements, {'view': 'occupants'}).json()['placements']), 1)
        self.assertEqual(self.client.get(self.placements).json()['placements'], [])
        for status in ('Departed', 'Cancelled', 'Transferred'):
            with connection.cursor() as cur:
                cur.execute('UPDATE PLACEMENT SET status=%s WHERE registration_id=%s AND placement_no=2', [status, self.registration])
            self.assertIsNone(self.client.get(self.detail).json()['current_placement'])
            self.assertEqual(len(self.client.get(self.placements, {'view': 'history'}).json()['placements']), 1)
        with connection.cursor() as cur:
            cur.execute("UPDATE PLACEMENT SET status='Reserved' WHERE registration_id=%s AND placement_no=2", [self.registration])
            cur.execute("UPDATE REGISTRATION SET status='Cancelled' WHERE registration_id=%s", [self.registration])
        self.assertIsNone(self.client.get(self.detail).json()['current_placement'])
        self.assertEqual(self.client.get(self.placements).json()['placements'], [])
        self.assertEqual(self.client.get(self.placements, {'view': 'history'}).json()['placements'][0]['registration_status'], 'Cancelled')

    def test_invalid_filters_access_and_methods(self):
        for value in ('', '0', '-1', '1.5', 'abc', '2147483648', '9' * 5000):
            for key in ('event_id', 'registration_id'):
                self.assertEqual(self.client.get('/api/staff/registrations', {key: value}).status_code, 400)
            self.assertEqual(self.client.get(self.placements, {'event_id': value}).status_code, 400)
        for view in ('', 'pending', 'Reservations'):
            self.assertEqual(self.client.get(self.placements, {'view': view}).status_code, 400)
        self.assertEqual(self.client.get('/api/staff/registrations/999999').status_code, 404)
        self.assertEqual(self.client.get('/api/staff/shelters/999999/placements').status_code, 404)
        paths = ['/api/staff/registrations', self.detail, self.placements]
        anonymous = Client()
        for path in paths:
            self.assertEqual(anonymous.get(path).status_code, 401)
            self.assertEqual(self.client.post(path, '{}', content_type='application/json').status_code, 405)
        anonymous.post('/api/auth/login', json.dumps({'login_email': 'holder@example.com',
                       'password': t.PASSWORD}), content_type='application/json')
        for path in paths:
            self.assertEqual(anonymous.get(path).status_code, 403)
