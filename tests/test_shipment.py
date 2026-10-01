import unittest

from app import create_app, db
from app.models.shipment import (
    ORDER_STATUSES,
    ShipmentOrder,
    generate_tracking_number,
)


class ShipmentModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_tracking_number_prefix_and_length(self):
        number = generate_tracking_number()
        self.assertTrue(number.startswith('FS'))
        self.assertEqual(len(number), 14)

    def test_order_defaults_to_created(self):
        order = ShipmentOrder(origin='Austin, TX', destination='Denver, CO')
        db.session.add(order)
        db.session.commit()
        self.assertEqual(order.status, 'created')
        self.assertTrue(order.tracking_number.startswith('FS'))

    def test_record_event_updates_status_and_history(self):
        order = ShipmentOrder(origin='Austin, TX', destination='Denver, CO')
        db.session.add(order)
        order.record_event('labeled', location='Austin hub')
        order.record_event('in_transit', note='Departed origin')
        db.session.commit()

        self.assertEqual(order.status, 'in_transit')
        events = order.events.all()
        self.assertEqual([e.status for e in events], ['labeled', 'in_transit'])
        self.assertEqual(events[0].location, 'Austin hub')

    def test_unknown_status_rejected(self):
        order = ShipmentOrder(origin='Austin, TX', destination='Denver, CO')
        with self.assertRaises(ValueError):
            order.record_event('teleported')
        self.assertEqual(order.status, 'created')

    def test_status_catalog_is_stable(self):
        self.assertIn('delivered', ORDER_STATUSES)
        self.assertIn('exception', ORDER_STATUSES)
