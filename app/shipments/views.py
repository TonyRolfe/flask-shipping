"""JSON create/track API for shipment orders.

CSRF is exempted because these routes are consumed by clients that send
JSON, not form posts. Status values still come from ORDER_STATUSES.
"""
from flask import Blueprint, jsonify, request

from app import csrf, db
from app.models.shipment import ORDER_STATUSES, ShipmentOrder

shipments = Blueprint('shipments', __name__)
csrf.exempt(shipments)


def _serialize(order):
    return {
        'tracking_number': order.tracking_number,
        'origin': order.origin,
        'destination': order.destination,
        'status': order.status,
        'events': [
            {
                'status': event.status,
                'location': event.location,
                'note': event.note,
                'occurred_at': (
                    event.occurred_at.isoformat() if event.occurred_at else None
                ),
            }
            for event in order.events
        ],
    }


@shipments.route('/shipments', methods=['POST'])
def create_shipment():
    data = request.get_json(silent=True) or {}
    origin = (data.get('origin') or '').strip()
    destination = (data.get('destination') or '').strip()
    if not origin or not destination:
        return jsonify({'error': 'origin and destination are required'}), 400
    order = ShipmentOrder(origin=origin, destination=destination)
    order.record_event('created', note='Order created')
    db.session.add(order)
    db.session.commit()
    return jsonify(_serialize(order)), 201


@shipments.route('/shipments/<tracking_number>', methods=['GET'])
def get_shipment(tracking_number):
    order = ShipmentOrder.query.filter_by(
        tracking_number=tracking_number).first()
    if order is None:
        return jsonify({'error': 'not found'}), 404
    return jsonify(_serialize(order))


@shipments.route('/shipments/<tracking_number>/events', methods=['POST'])
def add_event(tracking_number):
    order = ShipmentOrder.query.filter_by(
        tracking_number=tracking_number).first()
    if order is None:
        return jsonify({'error': 'not found'}), 404
    data = request.get_json(silent=True) or {}
    status = data.get('status')
    if status not in ORDER_STATUSES:
        return jsonify({
            'error': 'unknown status',
            'allowed': list(ORDER_STATUSES),
        }), 400
    order.record_event(
        status, note=data.get('note'), location=data.get('location'))
    db.session.commit()
    return jsonify(_serialize(order))
