"""Shipping-domain models: orders and tracking events.

Statuses are an ordered lifecycle. Unknown statuses are rejected so the
admin UI and API cannot invent ad-hoc states.
"""
import secrets
import string
from datetime import datetime

from .. import db

ORDER_STATUSES = (
    'created',
    'labeled',
    'in_transit',
    'out_for_delivery',
    'delivered',
    'exception',
)


def generate_tracking_number():
    """Public tracking id, e.g. FS7K2Q9M4N1P8R."""
    alphabet = string.ascii_uppercase + string.digits
    suffix = ''.join(secrets.choice(alphabet) for _ in range(12))
    return 'FS' + suffix


class ShipmentOrder(db.Model):
    __tablename__ = 'shipment_orders'

    id = db.Column(db.Integer, primary_key=True)
    tracking_number = db.Column(
        db.String(32), unique=True, index=True, nullable=False)
    origin = db.Column(db.String(128), nullable=False)
    destination = db.Column(db.String(128), nullable=False)
    status = db.Column(
        db.String(32), nullable=False, default='created', index=True)
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False)
    events = db.relationship(
        'TrackingEvent',
        backref='order',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='TrackingEvent.occurred_at',
    )

    def __init__(self, **kwargs):
        if not kwargs.get('tracking_number'):
            kwargs['tracking_number'] = generate_tracking_number()
        # Column default is only applied on flush. Set it here so a rejected
        # event still leaves a new order in the created state.
        if not kwargs.get('status'):
            kwargs['status'] = 'created'
        super(ShipmentOrder, self).__init__(**kwargs)

    def record_event(self, status, note=None, location=None):
        """Append a tracking event and move the order to that status."""
        if status not in ORDER_STATUSES:
            raise ValueError('unknown status: %s' % status)
        event = TrackingEvent(
            order=self,
            status=status,
            note=note,
            location=location,
        )
        self.status = status
        db.session.add(event)
        return event

    def __repr__(self):
        return '<ShipmentOrder %s %s>' % (self.tracking_number, self.status)


class TrackingEvent(db.Model):
    __tablename__ = 'tracking_events'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey('shipment_orders.id'),
        nullable=False,
        index=True,
    )
    status = db.Column(db.String(32), nullable=False)
    location = db.Column(db.String(128))
    note = db.Column(db.String(256))
    occurred_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return '<TrackingEvent %s %s>' % (self.status, self.occurred_at)
