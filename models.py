from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    city = db.Column(db.String(64))
    active = db.Column(db.Boolean, default=True)

    items = db.relationship("Item", backref="store", lazy=True)
    orders = db.relationship("Order", backref="store", lazy=True)

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(32), default="staff")
    active = db.Column(db.Boolean, default=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey("store.id"), nullable=False)
    code = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey("store.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    staff_username = db.Column(db.String(64))
    discount = db.Column(db.Float, default=0.0)

    lines = db.relationship("OrderLine", backref="order", lazy=True)

class OrderLine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    item_name = db.Column(db.String(128), nullable=False)
    price = db.Column(db.Float, nullable=False)
    qty = db.Column(db.Integer, nullable=False)
