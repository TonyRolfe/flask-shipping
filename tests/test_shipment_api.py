import json
import unittest

from app import create_app, db


class ShipmentApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_and_track(self):
        response = self.client.post(
            '/api/shipments',
            data=json.dumps({
                'origin': 'Austin, TX',
                'destination': 'Denver, CO',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        body = json.loads(response.data)
        self.assertTrue(body['tracking_number'].startswith('FS'))
        self.assertEqual(body['status'], 'created')
        self.assertEqual(body['events'][0]['status'], 'created')

        track = self.client.get('/api/shipments/' + body['tracking_number'])
        self.assertEqual(track.status_code, 200)
        self.assertEqual(
            json.loads(track.data)['destination'], 'Denver, CO')

        event = self.client.post(
            '/api/shipments/' + body['tracking_number'] + '/events',
            data=json.dumps({
                'status': 'in_transit',
                'location': 'Dallas',
            }),
            content_type='application/json',
        )
        self.assertEqual(event.status_code, 200)
        tracked = json.loads(event.data)
        self.assertEqual(tracked['status'], 'in_transit')
        self.assertEqual(tracked['events'][-1]['location'], 'Dallas')

    def test_missing_fields(self):
        response = self.client.post(
            '/api/shipments',
            data=json.dumps({'origin': 'Austin'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_unknown_tracking_number(self):
        response = self.client.get('/api/shipments/FSDOESNOTEXIST')
        self.assertEqual(response.status_code, 404)

    def test_unknown_status(self):
        created = self.client.post(
            '/api/shipments',
            data=json.dumps({
                'origin': 'Austin, TX',
                'destination': 'Denver, CO',
            }),
            content_type='application/json',
        )
        number = json.loads(created.data)['tracking_number']
        response = self.client.post(
            '/api/shipments/' + number + '/events',
            data=json.dumps({'status': 'teleported'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
