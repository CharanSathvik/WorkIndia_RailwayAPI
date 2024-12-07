from flask import Blueprint, request, jsonify
from app.models import User, Train, Booking, db
from app import bcrypt
from flask import current_app as app
import jwt
import datetime

main_blueprint = Blueprint("main", __name__)

@main_blueprint.route("/register", methods=["POST"])
def register():
    """Endpoint to register a new user"""
    data = request.json
    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    user = User(username=data["username"], password=hashed_password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User registered successfully!"}), 201

@main_blueprint.route("/login", methods=["POST"])
def login():
    """Endpoint to login a user and return a token"""
    data = request.json
    user = User.query.filter_by(username=data["username"]).first()
    if user and bcrypt.check_password_hash(user.password, data["password"]):
        token = jwt.encode({"user_id": user.id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, app.config["SECRET_KEY"])
        return jsonify({"token": token}), 200
    return jsonify({"message": "Invalid credentials!"}), 401

@main_blueprint.route("/trains", methods=["POST"])
def add_train():
    """Admin endpoint to add a new train"""
    api_key = request.headers.get("x-api-key")
    if api_key != app.config["ADMIN_API_KEY"]:
        return jsonify({"message": "Unauthorized!"}), 403
    data = request.json
    train = Train(name=data["name"], source=data["source"], destination=data["destination"], total_seats=data["total_seats"], available_seats=data["total_seats"])
    db.session.add(train)
    db.session.commit()
    return jsonify({"message": "Train added successfully!"}), 201

@main_blueprint.route("/trains", methods=["GET"])
def get_trains():
    """Endpoint to get available trains between source and destination"""
    source = request.args.get("source")
    destination = request.args.get("destination")
    trains = Train.query.filter_by(source=source, destination=destination).all()
    result = [{"id": t.id, "name": t.name, "available_seats": t.available_seats} for t in trains]
    return jsonify(result), 200

@main_blueprint.route("/book", methods=["POST"])
def book_seat():
    """Endpoint to book a seat on a specific train"""
    token = request.headers.get("Authorization").split()[1]
    data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
    user_id = data["user_id"]
    data = request.json
    train = Train.query.get(data["train_id"])
    if train.available_seats < data["seats"]:
        return jsonify({"message": "Not enough seats available!"}), 400
    train.available_seats -= data["seats"]
    booking = Booking(user_id=user_id, train_id=data["train_id"], seats_booked=data["seats"])
    db.session.add(booking)
    db.session.commit()
    return jsonify({"message": "Booking successful!"}), 200