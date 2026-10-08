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

    def _create(self, origin='Austin, TX', destination='Denver, CO'):
        return self.client.post(
            '/api/shipments',
            data=json.dumps({
                'origin': origin,
                'destination': destination,
            }),
            content_type='application/json',
        )

    def test_create_and_track(self):
        response = self._create()
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

    def test_list_and_status_filter(self):
        first = json.loads(self._create().data)
        second = json.loads(
            self._create(destination='Seattle, WA').data)
        self.client.post(
            '/api/shipments/' + second['tracking_number'] + '/events',
            data=json.dumps({'status': 'labeled'}),
            content_type='application/json',
        )

        listed = self.client.get('/api/shipments')
        self.assertEqual(listed.status_code, 200)
        numbers = [
            item['tracking_number']
            for item in json.loads(listed.data)['shipments']
        ]
        self.assertEqual(numbers[0], second['tracking_number'])
        self.assertIn(first['tracking_number'], numbers)

        labeled = self.client.get('/api/shipments?status=labeled')
        self.assertEqual(labeled.status_code, 200)
        labeled_body = json.loads(labeled.data)['shipments']
        self.assertEqual(len(labeled_body), 1)
        self.assertEqual(
            labeled_body[0]['tracking_number'], second['tracking_number'])

        bad = self.client.get('/api/shipments?status=teleported')
        self.assertEqual(bad.status_code, 400)

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
        created = self._create()
        number = json.loads(created.data)['tracking_number']
        response = self.client.post(
            '/api/shipments/' + number + '/events',
            data=json.dumps({'status': 'teleported'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
