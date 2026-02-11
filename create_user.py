from app import app, db, bcrypt
from models import User

with app.app_context():

    password = bcrypt.generate_password_hash("1234").decode("utf-8")

    user1 = User(username="sales1", password=password, role="sales")
    user2 = User(username="production1", password=password, role="production")

    db.session.add(user1)
    db.session.add(user2)

    db.session.commit()

    print("Users Created")
