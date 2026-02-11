from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


# ---------------- USERS TABLE ----------------
class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(200), nullable=False)

    role = db.Column(db.String(50), nullable=False)


# ---------------- ORDERS TABLE ----------------
class Order(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    order_number = db.Column(db.String(50), unique=True)

    customer_name = db.Column(db.String(200))
    place_of_supply = db.Column(db.String(200))

    order_date = db.Column(db.Date)
    dispatch_date = db.Column(db.Date)

    delivery_time = db.Column(db.String(50))

    sales_person = db.Column(db.String(100))

    status = db.Column(db.String(50), default="Pending")

    # ⭐ FIXED PROPERLY INSIDE CLASS
    completed_by = db.Column(db.String(100))
    completed_time = db.Column(db.DateTime)


# ---------------- ORDER ITEMS TABLE ----------------
class OrderItem(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))

    product_name = db.Column(db.String(200))
    product_code = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
