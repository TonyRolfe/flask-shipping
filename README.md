# flask-shipping

An open-source Flask-based shipping web application.

Built on top of the excellent [flask-base](https://github.com/hack4impact/flask-base) template, this project adapts the boilerplate for shipping / logistics workflows (orders, tracking, admin management, etc.).

**Status:** flask-base foundation plus shipment orders, tracking events, and a JSON create/list/track API on `feat/orders-tracking`.

### Portfolio roadmap

| Step | Status |
|------|--------|
| Polish README | ✅ this file |
| Core shipping features (orders, tracking numbers, status events) | ✅ models + `/api/shipments` on `feat/orders-tracking` |
| Tests (order/tracking model and API) | ✅ `tests/test_shipment.py`, `tests/test_shipment_api.py` |
| Deploy demo (Docker Compose, Python 3.11) | ✅ `docker-compose.yml` + `Dockerfile.demo` |

### Shipment API (branch `feat/orders-tracking`)

```bash
curl -s -X POST http://localhost:5000/api/shipments \
  -H 'Content-Type: application/json' \
  -d '{"origin":"Austin, TX","destination":"Denver, CO"}'

curl -s http://localhost:5000/api/shipments
curl -s 'http://localhost:5000/api/shipments?status=in_transit'

curl -s http://localhost:5000/api/shipments/FS7K2Q9M4N1P8R

curl -s -X POST http://localhost:5000/api/shipments/FS7K2Q9M4N1P8R/events \
  -H 'Content-Type: application/json' \
  -d '{"status":"in_transit","location":"Dallas"}'
```

Allowed statuses: `created`, `labeled`, `in_transit`, `out_for_delivery`, `delivered`, `exception`. `GET /api/shipments` returns newest first. An unknown `status` query returns 400.

### Demo (Compose)

The legacy `Dockerfile` still targets Ubuntu 16.04 / Python 3.6. Use the demo image instead:

```bash
docker compose up --build
# http://localhost:5000
curl -s -X POST http://localhost:5000/api/shipments \
  -H 'Content-Type: application/json' \
  -d '{"origin":"Austin, TX","destination":"Denver, CO"}'
```

`Dockerfile.demo` pins Flask 2.2.5, Flask-SQLAlchemy 2.5.1, itsdangerous 2.0.1, and WTForms 2.2.1 so the existing app factory imports on Python 3.11. SQLite is the default database. CI runs the shipment tests on the same pin (`.github/workflows/pytest.yml`).

---

## Original flask-base Badges & Overview

See the previous README sections below for the flask-base setup (venv, Redis, Postgres, `manage.py`). The portfolio demo path is Compose above, not the Ubuntu 16.04 Dockerfile.

[![Circle CI](https://circleci.com/gh/hack4impact/flask-base.svg?style=svg)](https://circleci.com/gh/hack4impact/flask-base)

A Flask application template with the boilerplate code already done for you. Documentation: [hack4impact flask-base](http://hack4impact.github.io/flask-base).

## Setting up

```
$ git clone https://github.com/TonyRolfe/flask-shipping.git
$ cd flask-shipping
$ git checkout feat/orders-tracking
$ python3 -m venv venv && source venv/bin/activate
$ pip install -r requirements.txt
$ python manage.py recreate_db && python manage.py setup_dev
```

Required local env: `SECRET_KEY`, plus Redis if you use the background queue. Do not commit `config.env`.

## Running the app

```
$ honcho start -e config.env -f Local
```

Or the portfolio demo:

```
$ docker compose up --build
```

## Contributing

Contributions are welcome. See [CONDUCT.md](./CONDUCT.md).

## License
[MIT License](LICENSE.md)

---

**Portfolio note:** Part of [Tony Rolfe](https://github.com/TonyRolfe)'s public portfolio. Orders, tracking, list, tests, and the Python 3.11 Compose demo are on `feat/orders-tracking`.
